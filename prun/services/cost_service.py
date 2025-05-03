import logging
import math
from typing import List, Optional, Callable

from pydantic import BaseModel, Field

from prun.config import Empire, EmpireProductionRecipe
from prun.errors import PlanetNotFoundError, RecipeNotFoundError
from prun.models import Planet, PlanetBuilding, PlanetResource, Recipe
from prun.services.building_service import BuildingService
from prun.services.exchange_service import ExchangeService
from prun.services.planet_service import PlanetService
from prun.services.recipe_service import RecipeService
from prun.services.workforce_service import WorkforceService

logger = logging.getLogger(__name__)


class CalculatedInput(BaseModel):
    """Calculated recipe input cost."""

    item_symbol: str = Field(description="The symbol of the item")
    quantity: float = Field(
        description="The quantity of the item needed for the recipe run"
    )
    price: float = Field(description="The price of the item per unit")
    total: float = Field(description="The total cost of the item for the recipe run")


class CalculatedInputCosts(BaseModel):
    inputs: List[CalculatedInput] = Field(
        description="The individual input costs for the recipe run"
    )
    total: float = Field(description="The total cost of all inputs for the recipe run")


class CalculatedWorkforceInput(CalculatedInput):
    """Calculated workforce input cost."""

    workforce_type: str = Field(description="The type of workforce")


class CalculatedWorkforceCosts(BaseModel):
    """Calculated workforce cost."""

    inputs: List[CalculatedWorkforceInput] = Field(
        description="The individual input costs for the workforce"
    )
    total: float = Field(
        description="The total cost of all consumables for the workforce"
    )


class CalculatedRecipeCost(BaseModel):
    """Calculated recipe cost."""

    recipe_symbol: str
    building_symbol: str
    time_ms: int
    input_costs: CalculatedInputCosts
    workforce_cost: CalculatedWorkforceCosts
    repair_cost: float
    total: float


class CalculatedRecipeOutputCOGM(BaseModel):
    """Calculated COGM."""

    recipe_symbol: str
    item_symbol: str
    building_symbol: str
    time_ms: int
    workforce_cost: CalculatedWorkforceCosts
    repair_cost: float
    total_cost: float
    input_costs: CalculatedInputCosts


class CalculatedPlanetCOGM(BaseModel):
    """Calculated planet COGM."""

    planet_name: str
    recipes: List[CalculatedRecipeOutputCOGM]


class CalculatedEmpireCOGM(BaseModel):
    """Calculated empire COGM."""

    empire_name: str
    planets: List[CalculatedPlanetCOGM]


class CostService:
    """Service for cost-related operations."""

    def __init__(
        self,
        building_service: BuildingService,
        exchange_service: ExchangeService,
        planet_service: PlanetService,
        recipe_service: RecipeService,
        workforce_service: WorkforceService,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
            recipe_service: Recipe service for getting recipe information
            workforce_service: Workforce service for calculating workforce costs
        """
        self.building_service = building_service
        self.exchange_service = exchange_service
        self.planet_service = planet_service
        self.recipe_service = recipe_service
        self.workforce_service = workforce_service

    def calculate_cogm(
        self,
        recipe: Recipe,
        planet: Planet,
        item_symbol: str,
        get_buy_price: Callable[[str], float],
    ) -> CalculatedRecipeOutputCOGM:
        # Calculate base recipe cost
        recipe_cost = self.calculate_recipe_cost(
            recipe=recipe, planet=planet, get_buy_price=get_buy_price
        )
        recipe_output = next(
            output for output in recipe.outputs if output.item_symbol == item_symbol
        )
        # Calculate scaled recipe cost
        return CalculatedRecipeOutputCOGM(
            recipe_symbol=recipe.symbol,
            item_symbol=item_symbol,
            building_symbol=recipe.building_symbol,
            time_ms=recipe.time_ms,
            input_costs=CalculatedInputCosts(
                inputs=[
                    CalculatedInput(
                        item_symbol=input.item_symbol,
                        quantity=input.quantity / recipe_output.quantity,
                        price=input.price,
                        total=input.total / recipe_output.quantity,
                    )
                    for input in recipe_cost.input_costs.inputs
                ],
                total=recipe_cost.input_costs.total / recipe_output.quantity,
            ),
            workforce_cost=CalculatedWorkforceCosts(
                inputs=[
                    CalculatedWorkforceInput(
                        workforce_type=workforce_input_cost.workforce_type,
                        item_symbol=workforce_input_cost.item_symbol,
                        quantity=workforce_input_cost.quantity / recipe_output.quantity,
                        price=workforce_input_cost.price,
                        total=workforce_input_cost.total / recipe_output.quantity,
                    )
                    for workforce_input_cost in recipe_cost.workforce_cost.inputs
                ],
                total=recipe_cost.workforce_cost.total / recipe_output.quantity,
            ),
            repair_cost=recipe_cost.repair_cost / recipe_output.quantity,
            total_cost=recipe_cost.total / recipe_output.quantity,
        )

    def calculate_daily_building_repair_cost(
        self,
        planet_building: PlanetBuilding,
        days_since_last_repair: int,
        get_buy_price: Callable[[str], float],
    ) -> float:
        """
        Calculate the daily repair cost of a building.

        Args:
            building: The building to calculate the repair cost for
            days_since_last_repair: The number of days since the last repair

        Returns:
            The daily repair cost of the building
        """
        total_building_repair_cost: float = 0

        for buliding_cost in planet_building.building_costs:
            price = get_buy_price(buliding_cost.item_symbol)
            total_building_repair_cost += (
                buliding_cost.repair_amount(days_since_last_repair) * price
            )

        daily_building_repair_cost = total_building_repair_cost / days_since_last_repair

        return daily_building_repair_cost

    def calculate_empire_cogm(
        self,
        empire: Empire,
        get_buy_price: Callable[[str], float],
    ) -> CalculatedEmpireCOGM:
        planet_cogms: List[CalculatedPlanetCOGM] = []
        # cache of cogm prices for each item symbol
        cogm_price_cache: dict[str, float] = {}

        # get all planets and their recipes
        planet_recipes: list[tuple[Planet, list[EmpireProductionRecipe]]] = [
            (
                self.planet_service.get_planet(planet.natural_id),
                planet.recipes,
            )
            for planet in empire.planets
        ]

        # we do two passes
        # the first pass fills the cogm cache
        # the second pass calculates final values

        # calculate everythin once, without storing it
        for planet, production_recipes in planet_recipes:
            self.calculate_planet_cogm(
                planet=planet,
                production_recipes=production_recipes,
                get_buy_price=get_buy_price,
                cogm_price_cache=cogm_price_cache,
            )

        # run everything again, but this time store the results
        for planet, production_recipes in planet_recipes:
            planet_cogms.append(
                self.calculate_planet_cogm(
                    planet=planet,
                    production_recipes=production_recipes,
                    get_buy_price=get_buy_price,
                    cogm_price_cache=cogm_price_cache,
                )
            )

        return CalculatedEmpireCOGM(empire_name=empire.name, planets=planet_cogms)

    def calculate_planet_cogm(
        self,
        planet: Planet,
        production_recipes: List[EmpireProductionRecipe],
        get_buy_price: Callable[[str], float],
        cogm_price_cache: Optional[dict[str, float]] = None,
    ) -> CalculatedPlanetCOGM:
        recipe_service = self.recipe_service

        planet_resource: PlanetResource | None = None
        recipe_output_cogms: List[CalculatedRecipeOutputCOGM] = []

        # calculate cogm for each recipe
        for production_recipe in production_recipes:
            planet_resource = next(
                (
                    resource
                    for resource in planet.resources
                    if resource.item.symbol == production_recipe.item_symbol
                ),
                None,
            )
            recipe = recipe_service.find_recipe(
                item_symbol=production_recipe.item_symbol,
                recipe_symbol=production_recipe.recipe_symbol,
                planet_resource=planet_resource,
            )

            if not recipe:
                raise RecipeNotFoundError(production_recipe.recipe_symbol)

            for output in recipe.outputs:
                # Calculate COGM for this output
                recipe_output_cogm = self.calculate_cogm(
                    recipe=recipe,
                    planet=planet,
                    item_symbol=output.item_symbol,
                    get_buy_price=get_buy_price,
                )
                # update the cache if it was provided
                if cogm_price_cache:
                    cogm_price_cache[output.item_symbol] = recipe_output_cogm.total_cost

                recipe_output_cogms.append(recipe_output_cogm)

        return CalculatedPlanetCOGM(
            planet_name=planet.name, recipes=recipe_output_cogms
        )

    def calculate_recipe_cost(
        self, recipe: Recipe, planet: Planet, get_buy_price: Callable[[str], float]
    ) -> CalculatedRecipeCost:
        """Calculate the cost of a recipe.

        Args:
            recipe: Recipe to calculate cost for
            input_prices: List of (RecipeInput, ExchangePrice) tuples

        Returns:
            Dictionary containing cost details
        """
        try:
            total_cost: float = 0
            inputs: List[CalculatedInput] = []

            for input in recipe.inputs:
                price = get_buy_price(input.item_symbol)
                if not price:
                    raise ValueError(f"No price found for item {input.item_symbol}")
                input_cost = input.quantity * price
                total_cost += input_cost
                inputs.append(
                    CalculatedInput(
                        item_symbol=input.item_symbol,
                        quantity=input.quantity,
                        price=price,
                        total=input_cost,
                    )
                )

            # Calculate workforce cost
            workforce_cost = self.calculate_workforce_cost_for_recipe(
                recipe=recipe, planet=planet, get_buy_price=get_buy_price
            )
            total_cost += workforce_cost.total

            # Calculate repair cost
            planet_building = self.planet_service.get_planet_building(
                planet.natural_id, recipe.building
            )
            if planet_building:
                daily_repair_cost = self.calculate_daily_building_repair_cost(
                    planet_building=planet_building,
                    days_since_last_repair=90,
                    get_buy_price=get_buy_price,
                )
                recipe_repair_cost = daily_repair_cost * (
                    recipe.time_ms / (24 * 60 * 60 * 1000)
                )  # Convert ms to days
                total_cost += recipe_repair_cost

            return CalculatedRecipeCost(
                recipe_symbol=recipe.symbol,
                building_symbol=recipe.building_symbol,
                time_ms=recipe.time_ms,
                input_costs=CalculatedInputCosts(
                    inputs=inputs,
                    total=sum(input.total for input in inputs),
                ),
                workforce_cost=workforce_cost,
                repair_cost=recipe_repair_cost,
                total=total_cost,
            )
        except Exception as e:
            logger.error(f"Error calculating recipe cost for {recipe.symbol}: {str(e)}")
            raise

    def calculate_workforce_cost_for_recipe(
        self, recipe: Recipe, planet: Planet, get_buy_price: Callable[[str], float]
    ) -> CalculatedWorkforceCosts:
        """Calculate the workforce cost for a recipe.

        Args:
            recipe: Recipe

        Returns:
            Total workforce cost
        """
        planet_building = self.planet_service.get_planet_building(
            planet.natural_id, recipe.building
        )
        if not planet_building:
            raise ValueError(f"Building {recipe.building.symbol} not found")

        consumable_costs: List[CalculatedWorkforceInput] = []
        # Calculate consumables cost for each workforce type
        for workforce_type, workforce_count in [
            ("PIONEER", planet_building.building.pioneers),
            ("SETTLER", planet_building.building.settlers),
            ("TECHNICIAN", planet_building.building.technicians),
            ("ENGINEER", planet_building.building.engineers),
            ("SCIENTIST", planet_building.building.scientists),
        ]:
            if workforce_count > 0:
                needs = self.workforce_service.get_workforce_needs(workforce_type)
                for need in needs:
                    price = get_buy_price(need.item_symbol)
                    if not price:
                        raise ValueError(
                            f"No price found for workforce need item {need.item_symbol}"
                        )

                    need_per_workforce_per_day = (
                        need.amount_per_worker_per_day * workforce_count
                    )

                    need_per_recipe_run = (
                        need_per_workforce_per_day
                        * self.workforce_service.workforce_days(recipe.time_ms)
                    )

                    price_per_recipe_run = price * need_per_recipe_run

                    consumable_costs.append(
                        CalculatedWorkforceInput(
                            workforce_type=workforce_type,
                            item_symbol=need.item_symbol,
                            quantity=need_per_recipe_run,
                            price=price,
                            total=price_per_recipe_run,
                        )
                    )
        # Convert daily cost to recipe duration cost
        return CalculatedWorkforceCosts(
            inputs=consumable_costs,
            total=sum(consumable_cost.total for consumable_cost in consumable_costs),
        )

    def _calculate_final_costs(
        self,
        recipe_cost: CalculatedRecipeCost,
    ) -> tuple[float, float, List[CalculatedInput]]:
        """Calculate the final costs based on the number of recipe runs needed.

        Args:
            cost_details: The base recipe cost details
            recipe_runs_needed: Number of times the recipe needs to be run

        Returns:
            Tuple of (total_input_cost, total_workforce_cost, scaled_input_costs)
        """
        # Calculate input costs separately from workforce costs
        total_input_cost = sum(
            input_cost.total for input_cost in recipe_cost.input_costs.inputs
        )
        total_workforce_cost = recipe_cost.workforce_cost.total

        # Scale the input costs for the total quantity
        scaled_input_costs = [
            CalculatedInput(
                item_symbol=input_cost.item_symbol,
                quantity=input_cost.quantity,
                price=input_cost.price,
                total=input_cost.total,
            )
            for input_cost in recipe_cost.input_costs.inputs
        ]

        return total_input_cost, total_workforce_cost, scaled_input_costs
