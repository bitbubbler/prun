import logging

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from fio import FIOClientInterface
from prun.errors import MultipleRecipesError, RecipeNotFoundError
from prun.interface import RecipeRepositoryInterface
from prun.models import Recipe, RecipeInput, ExchangePrice, RecipeOutput, PlanetResource

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        recipe_repository: RecipeRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
            workforce_service: Workforce service for calculating workforce costs
        """
        self.fio_client = fio_client
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

    def get_recipe(self, symbol: str) -> Optional[Recipe]:
        """Get a recipe by its symbol.

        Args:
            symbol: Recipe symbol

        Returns:
            Recipe if found, None otherwise
        """
        return self.recipe_repository.get_recipe(symbol)

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

    def recipe_from_resource(self, planet_resource: PlanetResource) -> Recipe:
        """Get a recipe for a planet resource."""
        if planet_resource.resource_type == "LIQUID":
            return self.recipe_repository.get_recipe("RIG:=>")
        elif planet_resource.resource_type == "SOLID":
            return self.recipe_repository.get_recipe("EXT:=>")
        elif planet_resource.resource_type == "GASEOUS":
            return self.recipe_repository.get_recipe("COL:=>")
        else:
            raise ValueError(f"Unknown resource type: {planet_resource.resource_type}")

    def find_recipe(
        self, item_symbol: str | None, recipe_symbol: Optional[str] = None
    ) -> Recipe:
        """Find a recipe for an item.

        Args:
            item_symbol: Symbol of the item to find a recipe for
            recipe_symbol: Optional specific recipe to use

        Returns:
            Recipe object

        Raises:
            ValueError: If recipe not found
            MultipleRecipesError: If multiple recipes are found and no specific recipe was chosen
        """
        try:
            if recipe_symbol:
                recipe = self.recipe_repository.get_recipe(recipe_symbol)
                if not recipe:
                    raise RecipeNotFoundError(item_symbol, recipe_symbol)
                return recipe

            recipes = self.recipe_repository.get_recipes_for_item(item_symbol)

            if not recipes:
                raise RecipeNotFoundError(item_symbol, recipe_symbol)

            if len(recipes) > 1:
                raise MultipleRecipesError(
                    item_symbol=item_symbol,
                    available_recipes=recipes,
                )

            return recipes[0]
        except Exception as e:
            logger.error(
                f"Error finding recipe for {item_symbol}: {str(e)}", exc_info=True
            )
            raise
