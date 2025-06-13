import logging

from typing import List, Optional

from fio import FIOClientInterface
from prun.errors import (
    MultipleRecipesError,
    RecipeNotFoundError,
    PlanetResourceRequiredError,
    RecipeSymbolRequiredError,
    PlanetRequiredError,
    PlanetResourceNotFoundError,
)
from prun.interface import RecipeRepositoryInterface
from prun.models import (
    COGCProgram,
    EfficientPlanetExtractionRecipe,
    EfficientRecipe,
    ExchangePrice,
    Experts,
    Planet,
    PlanetExtractionRecipe,
    PlanetResource,
    Recipe,
    RecipeInput,
    RecipeOutput,
)
from prun.services.efficiency_service import EfficiencyService

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        efficiency_service: EfficiencyService,
        recipe_repository: RecipeRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.efficiency_service = efficiency_service
        self.recipe_repository = recipe_repository

    def get_all_recipes(self) -> List[Recipe]:
        """Get all recipes with basic information.

        Returns:
            List of dictionaries containing recipe information
        """
        return self.recipe_repository.get_all_recipes()

    def get_recipes_for_item(self, item_symbol: str) -> List[Recipe]:
        """Get all recipes that can produce an item.

        Args:
            item_symbol: Symbol of the item to find recipes for

        Returns:
            List of recipes that can produce the item
        """
        return self.recipe_repository.get_recipes_for_item(item_symbol)

    def get_recipe(self, recipe_symbol: str) -> Recipe:
        """Get a recipe by its symbol.

        Args:
            symbol: Recipe symbol

        Returns:
            Recipe if found, None otherwise

        Raises:
            RecipeNotFoundError: If the recipe is not found
            PlanetResourceRequiredError: If the recipe is an extraction recipe and a planet resource is required (you should use get_extraction_recipe instead)
        """
        recipe = self.recipe_repository.get_recipe(recipe_symbol)

        if not recipe:
            raise RecipeNotFoundError(recipe_symbol)

        if recipe.is_resource_extraction_recipe:
            raise PlanetResourceRequiredError()

        return recipe

    def get_efficient_recipe(
        self, recipe_symbol: str, experts: Experts, cogc_program: str | None = None
    ) -> EfficientRecipe:
        """Get an efficient recipe by its symbol.

        Args:
            recipe_symbol: Recipe symbol
            planet_resource: Planet resource to use for extraction recipes

        Returns:
            Efficient recipe
        """
        recipe = self.recipe_repository.get_recipe(recipe_symbol)

        if not recipe:
            raise RecipeNotFoundError(recipe_symbol)

        expert_efficiency: float = self.efficiency_service.get_expert_efficiency(
            experts, recipe.building.expertise
        )
        cogc_efficiency = self.efficiency_service.get_cogc_efficiency(
            building=recipe.building, program=cogc_program
        )
        efficiency = expert_efficiency + cogc_efficiency

        return EfficientRecipe.efficient_recipe_from(
            recipe=recipe,
            efficiency=efficiency,
        )

    def get_planet_extraction_recipe(
        self, recipe_symbol: str, planet_resource: PlanetResource
    ) -> PlanetExtractionRecipe:
        """Get an extraction recipe by its symbol.

        Args:
            symbol: Recipe symbol
            planet_resource: Planet resource to use for extraction recipes

        Returns:
            Extraction recipe

        Raises:
            RecipeNotFoundError: If the recipe is not found
        """
        recipe = self.recipe_repository.get_recipe(recipe_symbol)

        if not recipe:
            raise RecipeNotFoundError(recipe_symbol)

        if not recipe.is_resource_extraction_recipe:
            raise ValueError("Recipe is not an extraction recipe")

        return PlanetExtractionRecipe.extraction_recipe_from(recipe, planet_resource)

    def get_efficient_planet_extraction_recipe(
        self,
        recipe_symbol: str,
        planet_resource: PlanetResource,
        experts: Experts,
        cogc_program: COGCProgram | None = None,
    ) -> EfficientPlanetExtractionRecipe:
        """Get an efficient planet extraction recipe by its symbol.

        Args:
            recipe_symbol: Recipe symbol
            planet_resource: Planet resource to use for extraction recipes

        Returns:
            Efficient extraction recipe
        """
        extraction_recipe = self.get_planet_extraction_recipe(
            recipe_symbol, planet_resource
        )

        if not extraction_recipe:
            raise RecipeNotFoundError(recipe_symbol)

        if not extraction_recipe.is_resource_extraction_recipe:
            raise ValueError("Recipe is not an extraction recipe")

        expert_efficiency = self.efficiency_service.get_expert_efficiency(
            experts, extraction_recipe.building.expertise
        )
        cogc_efficiency = self.efficiency_service.get_cogc_efficiency(
            building=extraction_recipe.building, program=cogc_program
        )
        efficiency = expert_efficiency + cogc_efficiency

        efficient_recipe = EfficientPlanetExtractionRecipe.efficient_recipe_from(
            recipe=extraction_recipe, efficiency=efficiency
        )

        return efficient_recipe

    def get_recipe_with_prices(
        self, symbol: str
    ) -> tuple[Recipe, List[tuple[RecipeInput, ExchangePrice]]]:
        """Get a recipe and its inputs with current prices.

        Args:
            symbol: Recipe symbol

        Returns:
            Tuple of (Recipe, list of (RecipeInput, ExchangePrice))
        """
        return self.recipe_repository.get_recipe_with_prices(symbol)

    def sync_recipes(self) -> None:
        """Sync recipes from the FIO API to the database.

        Args:
            fio_client: FIO API client

        Raises:
            Exception: If there's an error syncing recipes
        """
        try:
            recipes = self.fio_client.get_recipes()
            for fio_recipe in recipes:
                # Check if recipe already exists
                if not self.recipe_repository.get_recipe(
                    fio_recipe.standard_recipe_name
                ):
                    recipe = Recipe.model_validate(
                        {
                            "symbol": fio_recipe.standard_recipe_name,
                            "building_symbol": fio_recipe.building_ticker,
                            "time_ms": fio_recipe.time_ms,
                        }
                    )

                    recipe.inputs = [
                        RecipeInput.model_validate(
                            {
                                "recipe_symbol": recipe.symbol,
                                "item_symbol": input.ticker,
                                "quantity": float(input.amount),
                            }
                        )
                        for input in fio_recipe.inputs
                    ]

                    recipe.outputs = [
                        RecipeOutput.model_validate(
                            {
                                "recipe_symbol": recipe.symbol,
                                "item_symbol": output.ticker,
                                "quantity": float(output.amount),
                            }
                        )
                        for output in fio_recipe.outputs
                    ]

                    # Create recipe with its inputs and output
                    self.recipe_repository.create_recipe(recipe)
        except Exception as e:
            logger.error(f"Error syncing recipes: {str(e)}")
            raise

    def recipe_from_resource(
        self, planet_resource: PlanetResource
    ) -> PlanetExtractionRecipe:
        """Get a recipe for a planet resource."""
        if planet_resource.resource_type == "LIQUID":
            recipe = self.recipe_repository.get_recipe("RIG:=>")
            if not recipe:
                raise RecipeNotFoundError("RIG:=>")
            return PlanetExtractionRecipe.extraction_recipe_from(
                recipe, planet_resource
            )
        elif planet_resource.resource_type == "MINERAL":
            recipe = self.recipe_repository.get_recipe("EXT:=>")
            if not recipe:
                raise RecipeNotFoundError("EXT:=>")
            return PlanetExtractionRecipe.extraction_recipe_from(
                recipe, planet_resource
            )
        elif planet_resource.resource_type == "GASEOUS":
            recipe = self.recipe_repository.get_recipe("COL:=>")
            if not recipe:
                raise RecipeNotFoundError("COL:=>")
            return PlanetExtractionRecipe.extraction_recipe_from(
                recipe, planet_resource
            )
        else:
            raise ValueError(f"Unknown resource type: {planet_resource.resource_type}")

    def find_recipe(
        self,
        item_symbol: str | None,
        recipe_symbol: str | None = None,
        planet: Planet | None = None,
    ) -> Recipe | PlanetExtractionRecipe | None:
        """Find a recipe for an item.

        Args:
            item_symbol: Symbol of the item to find a recipe for
            recipe_symbol: Optional specific recipe to use
            planet_resource: Optional specific planet resource to use

        Returns:
            Recipe object

        Raises:
            ValueError: If recipe not found by symbol and no item symbol is provided
            MultipleRecipesError: If multiple recipes are found and no specific recipe was chosen
        """
        try:
            if recipe_symbol:
                return self.get_recipe(recipe_symbol)

            if not item_symbol:
                raise ValueError(
                    "Item symbol is required to find a recipe without a specific recipe symbol"
                )

            recipes = self.recipe_repository.get_recipes_for_item(item_symbol)

            if len(recipes) == 0 and planet:
                planet_resource = next(
                    (
                        resource
                        for resource in planet.resources
                        if resource.item.symbol == item_symbol
                    ),
                    None,
                )

                if not planet_resource:
                    raise PlanetResourceNotFoundError(item_symbol, planet.natural_id)

                return self.get_planet_extraction_recipe(
                    planet_resource.recipe_symbol, planet_resource
                )

            if not recipes:
                return None

            if len(recipes) > 1:
                raise MultipleRecipesError(
                    item_symbol=item_symbol,
                    available_recipes=recipes,
                )

            return recipes[0]

        except PlanetResourceRequiredError:
            if not planet:
                raise PlanetRequiredError()
            planet_resource = next(
                (
                    resource
                    for resource in planet.resources
                    if resource.item.symbol == item_symbol
                ),
                None,
            )
            if not planet_resource:
                raise PlanetResourceNotFoundError(item_symbol, planet.natural_id)

            return self.get_planet_extraction_recipe(
                planet_resource.recipe_symbol, planet_resource
            )
        except Exception as e:
            logger.error(
                f"Error finding recipe for {item_symbol}: {str(e)}", exc_info=True
            )
            raise

    def find_all_recipes(
        self,
        item_symbol: str | None,
        recipe_symbol: str | None = None,
        planet: Planet | None = None,
    ) -> list[Recipe | PlanetExtractionRecipe] | None:
        """Find a recipe for an item.

        Args:
            item_symbol: Symbol of the item to find a recipe for
            recipe_symbol: Optional specific recipe to use
            planet_resource: Optional specific planet resource to use

        Returns:
            List of recipes

        Raises:
            ValueError: If recipe not found by symbol and no item symbol is provided
        """
        try:
            if recipe_symbol:
                return self.get_recipe(recipe_symbol)

            if not item_symbol:
                raise ValueError(
                    "Item symbol is required to find a recipe without a specific recipe symbol"
                )

            recipes = self.recipe_repository.get_recipes_for_item(item_symbol)

            if len(recipes) == 0 and planet:
                planet_resource = next(
                    (
                        resource
                        for resource in planet.resources
                        if resource.item.symbol == item_symbol
                    ),
                    None,
                )

                if not planet_resource:
                    raise PlanetResourceNotFoundError(item_symbol, planet.natural_id)

                return [
                    self.get_planet_extraction_recipe(
                        planet_resource.recipe_symbol, planet_resource
                    )
                ]

            if not recipes:
                return None

            return recipes

        except PlanetResourceRequiredError:
            if not planet:
                raise PlanetRequiredError()
            planet_resource = next(
                (
                    resource
                    for resource in planet.resources
                    if resource.item.symbol == item_symbol
                ),
                None,
            )
            if not planet_resource:
                raise PlanetResourceNotFoundError(item_symbol, planet.natural_id)

            return self.get_planet_extraction_recipe(
                planet_resource.recipe_symbol, planet_resource
            )
        except Exception as e:
            logger.error(
                f"Error finding recipe for {item_symbol}: {str(e)}", exc_info=True
            )
            raise
