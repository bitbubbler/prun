import logging
from typing import List, Optional, Callable

from pydantic import BaseModel, Field

from fly.config import EmpireIn, EmpireProductionRecipeIn, EmpirePlanetIn
from fly.errors import PlanetNotFoundError, RecipeNotFoundError
from fly.models import (
    EfficientRecipe,
    EfficientPlanetExtractionRecipe,
    PlanetExtractionRecipe,
    Planet,
    PlanetBuilding,
    PlanetResource,
    Recipe,
)
from fly.services.building_service import BuildingService
from fly.services.efficiency_service import EfficiencyService
from fly.services.exchange_service import ExchangeService
from fly.services.planet_service import PlanetService
from fly.services.recipe_service import RecipeService
from fly.services.workforce_service import WorkforceService
from fly.util import round_half_up

logger = logging.getLogger(__name__)


class CalculatedInput(BaseModel):
    """Calculated recipe input cost."""

    item_symbol: str = Field(description="The symbol of the item")
    quantity: float = Field(description="The quantity of the item needed for the recipe run")
    price: float = Field(description="The price of the item per unit")
    total: float = Field(description="The total cost of the item for the recipe run")


class CalculatedInputCosts(BaseModel):
    inputs: List[CalculatedInput] = Field(description="The individual input costs for the recipe run")
    total: float = Field(description="The total cost of all inputs for the recipe run")


class CalculatedWorkforceNeedCost(BaseModel):
    """Calculated workforce need cost."""

    workforce_type: str = Field(description="The type of workforce")
    workforce_count: int = Field(description="The number of workers")
    inputs: List[CalculatedInput] = Field(description="The individual input costs for the workforce")
    total: float = Field(description="The total cost of all inputs for the workforce type")


class CalculatedWorkforceCosts(BaseModel):
    """Calculated workforce cost."""

    needs: List[CalculatedWorkforceNeedCost] = Field(
        description="The individual workforce need costs for the recipe run"
    )
    total: float = Field(description="The total cost of all consumables for the workforce")


class CalculatedBuildingRepairCosts(BaseModel):
    """Calculated building repair cost."""

    inputs: List[CalculatedInput] = Field(description="The individual input costs for the building")
    total: float = Field(description="The total cost of all inputs for the building")


class CalculatedRecipeCost(BaseModel):
    """Calculated recipe cost."""

    recipe_symbol: str
    building_symbol: str
    time_ms: int
    input_costs: CalculatedInputCosts
    workforce_cost: CalculatedWorkforceCosts
    repair_cost: float
    total: float
    expert_efficiency: float


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
    expert_efficiency: float


class CalculatedPlanetCOGM(BaseModel):
    """Calculated planet COGM."""

    planet_name: str
    recipes: List[CalculatedRecipeOutputCOGM]


class CalculatedEmpireCOGM(BaseModel):
    """Calculated empire COGM."""

    empire_name: str
    planets: List[CalculatedPlanetCOGM]


class CostContext(BaseModel):
    """Context for cost calculations."""

    get_buy_price: Callable[[str], float]
    set_cogm_price: Callable[[str, float], None]
    cogm_price_cache: dict[str, float]


class CostService:
    """Service for cost-related operations."""

    def __init__(
        self,
        building_service: BuildingService,
        efficiency_service: EfficiencyService,
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
        self.efficiency_service = efficiency_service
        self.exchange_service = exchange_service
        self.planet_service = planet_service
        self.recipe_service = recipe_service
        self.workforce_service = workforce_service

    def calculate_cogm(
        self,
        recipe: EfficientRecipe | EfficientPlanetExtractionRecipe,
        planet: Planet,
        item_symbol: str,
        cost_context: CostContext,
    ) -> CalculatedRecipeOutputCOGM:
        # Calculate base recipe cost
        recipe_cost = self.calculate_recipe_cost(
            cost_context=cost_context,
            recipe=recipe,
            planet=planet,
        )
        recipe_output_cogm = self.calculate_recipe_output_cogm(
            recipe=recipe,
            recipe_cost=recipe_cost,
            item_symbol=item_symbol,
        )
        # Calculate scaled recipe cost
        return recipe_output_cogm

    def calculate_total_building_repair_cost(
        self,
        cost_context: CostContext,
        planet_building: PlanetBuilding,
        days_since_last_repair: int,
    ) -> CalculatedBuildingRepairCosts:
        """
        Calculate the daily repair cost of a building.

        Args:
            building: The building to calculate the repair cost for
            days_since_last_repair: The number of days since the last repair

        Returns:
            The daily repair cost of the building
        """
        inputs: List[CalculatedInput] = []

        for buliding_cost in planet_building.building_costs:
            quantity = buliding_cost.repair_amount(days_since_last_repair)
            price = cost_context.get_buy_price(buliding_cost.item_symbol)
            inputs.append(
                CalculatedInput(
                    item_symbol=buliding_cost.item_symbol,
                    quantity=quantity,
                    price=price,
                    total=round(quantity * price, 2),
                )
            )

        return CalculatedBuildingRepairCosts(
            inputs=inputs,
            total=round(sum(input.total for input in inputs), 2),
        )

    def calculate_empire_cogm(
        self,
        cost_context: CostContext,
        empire: EmpireIn,
    ) -> CalculatedEmpireCOGM:
        planet_cogms: List[CalculatedPlanetCOGM] = []
        # cache of cogm prices for each item symbol
        cogm_price_cache: dict[str, float] = {}

        # get all planets and their recipes
        empire_planet_planets = self.get_empire_planet_planets(empire)

        # we do two passes
        # the first pass fills the cogm cache
        # the second pass calculates final values

        # calculate everythin once, without storing it
        for planet, empire_planet in empire_planet_planets:
            self.calculate_planet_cogm(
                cost_context=cost_context,
                planet=planet,
                empire_planet=empire_planet,
            )

        # run everything again, but this time store the results
        for planet, empire_planet in empire_planet_planets:
            planet_cogms.append(
                self.calculate_planet_cogm(
                    cost_context=cost_context,
                    planet=planet,
                    empire_planet=empire_planet,
                )
            )

        return CalculatedEmpireCOGM(empire_name=empire.name, planets=planet_cogms)

    def calculate_planet_cogm(
        self,
        cost_context: CostContext,
        empire_planet: EmpirePlanetIn,
        planet: Planet,
    ) -> CalculatedPlanetCOGM:
        recipe_service = self.recipe_service

        planet_resource: PlanetResource | None = None
        recipe_output_cogms: List[CalculatedRecipeOutputCOGM] = []

        # calculate cogm for each recipe
        for production_recipe in empire_planet.recipes:
            planet_resource = next(
                (resource for resource in planet.resources if resource.item.symbol == production_recipe.item_symbol),
                None,
            )
            recipe = recipe_service.find_recipe(
                item_symbol=production_recipe.item_symbol,
                recipe_symbol=production_recipe.recipe_symbol,
                planet_resource=planet_resource,
            )

            if not recipe:
                raise RecipeNotFoundError(production_recipe.recipe_symbol)

            if recipe.is_resource_extraction_recipe:
                efficient_recipe = recipe_service.get_efficient_planet_extraction_recipe(
                    recipe_symbol=recipe.symbol,
                    planet_resource=planet_resource,
                    experts=empire_planet.experts,
                )
            else:
                efficient_recipe = recipe_service.get_efficient_recipe(
                    recipe_symbol=recipe.symbol,
                    experts=empire_planet.experts,
                )

            recipe_cost = self.calculate_recipe_cost(
                cost_context=cost_context,
                recipe=efficient_recipe,
                planet=planet,
            )

            for output in recipe.outputs:
                # Calculate COGM for this output
                recipe_output_cogm = self.calculate_recipe_output_cogm(
                    recipe=efficient_recipe,
                    recipe_cost=recipe_cost,
                    item_symbol=output.item_symbol,
                )
                # update the cache if it was provided
                cost_context.set_cogm_price(
                    item_symbol=output.item_symbol,
                    price=recipe_output_cogm.total_cost,
                )

                recipe_output_cogms.append(recipe_output_cogm)

        return CalculatedPlanetCOGM(planet_name=planet.name, recipes=recipe_output_cogms)

    def calculate_recipe_cost(
        self,
        cost_context: CostContext,
        recipe: EfficientRecipe | EfficientPlanetExtractionRecipe,
        planet: Planet,
    ) -> CalculatedRecipeCost:
        """Calculate the cost of a recipe.

        Args:
            recipe: Recipe to calculate cost for
            input_prices: List of (RecipeInput, ExchangePrice) tuples

        Returns:
            Dictionary containing cost details
        """
        try:
            inputs: List[CalculatedInput] = []

            for input in recipe.inputs:
                price = cost_context.get_buy_price(input.item_symbol)
                if not price:
                    raise ValueError(f"No price found for item {input.item_symbol}")
                input_cost = input.quantity * price
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
                cost_context=cost_context,
                recipe=recipe,
                planet=planet,
            )

            # Calculate repair cost
            repair_costs = self.calculate_repair_cost_for_recipe(
                cost_context=cost_context,
                recipe=recipe,
                planet=planet,
            )

            return CalculatedRecipeCost(
                recipe_symbol=recipe.symbol,
                building_symbol=recipe.building_symbol,
                time_ms=recipe.time_ms,
                expert_efficiency=recipe.expert_efficiency,
                input_costs=CalculatedInputCosts(
                    inputs=inputs,
                    total=sum(input.total for input in inputs),
                ),
                workforce_cost=workforce_cost,
                repair_cost=repair_costs.total,
                total=(sum(input.total for input in inputs) + repair_costs.total + workforce_cost.total),
            )
        except Exception as e:
            logger.error(f"Error calculating recipe cost for {recipe.symbol}: {str(e)}")
            raise

    def calculate_repair_cost_for_recipe(
        self,
        cost_context: CostContext,
        recipe: Recipe | PlanetExtractionRecipe,
        planet: Planet,
    ) -> CalculatedBuildingRepairCosts:
        """Calculate the repair cost for a recipe.

        Args:
            recipe: Recipe to calculate repair cost for
            planet: Planet where the recipe is being run
            get_buy_price: Function to get the buy price for an item

        Returns:
            CalculatedBuildingRepairCosts containing the breakdown and total repair costs
        """
        planet_building = self.planet_service.get_planet_building(planet.natural_id, recipe.building)
        if not planet_building:
            raise ValueError(f"PlanetBuilding was not found for {recipe.building.symbol} on planet {planet.name}")

        total_repair_cost = self.calculate_total_building_repair_cost(
            cost_context=cost_context,
            planet_building=planet_building,
            days_since_last_repair=180,
        )

        # Calculate the daily repair cost
        daily_repair_cost = round(total_repair_cost.total / 180, 2)

        # Calculate recipe repair cost
        recipe_repair_cost = round(daily_repair_cost * recipe.percent_of_day, 2)

        # Scale the input costs by the recipe duration
        scaled_inputs = [
            CalculatedInput(
                item_symbol=input.item_symbol,
                quantity=round(input.quantity * recipe.percent_of_day / 180, 2),
                price=input.price,
                total=round(input.total * recipe.percent_of_day / 180, 2),
            )
            for input in total_repair_cost.inputs
        ]

        return CalculatedBuildingRepairCosts(inputs=scaled_inputs, total=recipe_repair_cost)

    def calculate_workforce_cost_for_recipe(
        self,
        cost_context: CostContext,
        recipe: Recipe | PlanetExtractionRecipe,
        planet: Planet,
    ) -> CalculatedWorkforceCosts:
        """Calculate the workforce cost for a recipe.

        Args:
            recipe: Recipe

        Returns:
            Total workforce cost
        """
        planet_building = self.planet_service.get_planet_building(planet.natural_id, recipe.building)
        if not planet_building:
            raise ValueError(f"Building {recipe.building.symbol} not found")

        needs: List[CalculatedWorkforceNeedCost] = []
        # Calculate consumables cost for each workforce type
        for workforce_type, workforce_count in [
            ("PIONEER", planet_building.building.pioneers),
            ("SETTLER", planet_building.building.settlers),
            ("TECHNICIAN", planet_building.building.technicians),
            ("ENGINEER", planet_building.building.engineers),
            ("SCIENTIST", planet_building.building.scientists),
        ]:
            if workforce_count > 0:
                workforce_needs = self.workforce_service.get_workforce_needs(workforce_type)
                inputs: List[CalculatedInput] = []

                for workforce_need in workforce_needs:
                    price = cost_context.get_buy_price(workforce_need.item_symbol)
                    if not price:
                        raise ValueError(f"No price found for workforce need item {workforce_need.item_symbol}")

                    # Calculate need per day for all workers of this type
                    # The amount is per 100 workers per day, so we divide by 100 first
                    need_per_workforce_per_day = workforce_need.amount_per_100_workers_per_day / 100 * workforce_count

                    workforce_days = self.workforce_service.workforce_days(recipe.time_ms)

                    need_per_recipe_run = need_per_workforce_per_day * workforce_days

                    price_per_recipe_run = round(price * need_per_recipe_run, 2)

                    inputs.append(
                        CalculatedInput(
                            item_symbol=workforce_need.item_symbol,
                            quantity=need_per_recipe_run,
                            price=price,
                            total=price_per_recipe_run,
                        )
                    )

                needs.append(
                    CalculatedWorkforceNeedCost(
                        workforce_type=workforce_type,
                        workforce_count=workforce_count,
                        inputs=inputs,
                        total=sum(input.total for input in inputs),
                    )
                )

        # Convert daily cost to recipe duration cost
        return CalculatedWorkforceCosts(
            needs=needs,
            total=sum(need.total for need in needs),
        )

    def calculate_recipe_output_cogm(
        self,
        recipe: EfficientRecipe | EfficientPlanetExtractionRecipe,
        recipe_cost: CalculatedRecipeCost,
        item_symbol: str,
    ) -> CalculatedRecipeOutputCOGM:
        """Calculate the final cogm based on the recipe cost and the recipe output.

        Args:
            cost_details: The base recipe cost details
            recipe_runs_needed: Number of times the recipe needs to be run

        Returns:
            Tuple of (total_input_cost, total_workforce_cost, scaled_input_costs)
        """
        print(f"recipe: {recipe}")
        recipe_output = next(output for output in recipe.outputs if output.item_symbol == item_symbol)

        output_quantity = recipe_output.quantity

        return CalculatedRecipeOutputCOGM(
            recipe_symbol=recipe.symbol,
            item_symbol=item_symbol,
            building_symbol=recipe.building_symbol,
            time_ms=recipe.time_ms,
            expert_efficiency=recipe.expert_efficiency,
            input_costs=CalculatedInputCosts(
                inputs=[
                    CalculatedInput(
                        item_symbol=input.item_symbol,
                        quantity=input.quantity,
                        price=input.price,
                        total=round_half_up(input.total / output_quantity),
                    )
                    for input in recipe_cost.input_costs.inputs
                ],
                total=round_half_up(recipe_cost.input_costs.total / output_quantity),
            ),
            workforce_cost=CalculatedWorkforceCosts(
                needs=[
                    CalculatedWorkforceNeedCost(
                        workforce_type=need.workforce_type,
                        workforce_count=need.workforce_count,
                        inputs=[
                            CalculatedInput(
                                item_symbol=input.item_symbol,
                                quantity=input.quantity / output_quantity,
                                price=input.price,
                                total=round_half_up(input.total / output_quantity),
                            )
                            for input in need.inputs
                        ],
                        total=round_half_up(need.total / output_quantity),
                    )
                    for need in recipe_cost.workforce_cost.needs
                ],
                total=round_half_up(recipe_cost.workforce_cost.total / output_quantity),
            ),
            repair_cost=round_half_up(recipe_cost.repair_cost / output_quantity),
            total_cost=round_half_up(recipe_cost.total / output_quantity),
        )

    def get_empire_planet_planets(self, empire: EmpireIn) -> list[tuple[Planet, EmpirePlanetIn]]:
        empire_planet_planets: list[tuple[Planet, EmpirePlanetIn]] = []
        for empire_planet in empire.planets:
            planet = self.planet_service.get_planet(empire_planet.natural_id)
            if not planet:
                raise PlanetNotFoundError(empire_planet.natural_id)

            empire_planet_planets.append(
                (
                    planet,
                    empire_planet,
                )
            )

        return empire_planet_planets
