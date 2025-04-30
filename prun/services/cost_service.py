import logging
import math
from typing import List, Optional, Callable

from pydantic import BaseModel, Field

from prun.models import Recipe, PlanetResource
from prun.services.building_service import BuildingService
from prun.services.exchange_service import ExchangeService
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


class CalculatedCOGM(BaseModel):
    """Calculated COGM."""

    recipe_symbol: str
    item_symbol: str
    building_symbol: str
    time_ms: int
    workforce_cost: CalculatedWorkforceCosts
    repair_cost: float
    total_cost: float
    input_costs: CalculatedInputCosts


class CostService:
    """Service for cost-related operations."""

    def __init__(
        self,
        building_service: BuildingService,
        exchange_service: ExchangeService,
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
        self.recipe_service = recipe_service
        self.workforce_service = workforce_service
        self.amortization_days = 180  # Standard amortization period in days

    def calculate_daily_repair_cost(
        self, total_material_cost: float, days_since_build: int = 89
    ) -> float:
        """Calculate daily repair cost based on total material cost and days since build.

        Args:
            total_material_cost: Total cost of materials used in construction
            days_since_build: Number of days since the building was constructed

        Returns:
            Daily repair cost
        """
        return (
            total_material_cost
            - math.floor(
                total_material_cost
                * (
                    (
                        self.amortization_days
                        - min(days_since_build, self.amortization_days)
                    )
                    / self.amortization_days
                )
            )
        ) * (1 / days_since_build)

    def calculate_amortization_cost(self, total_material_cost: float) -> float:
        """Calculate daily amortization cost.

        Args:
            total_material_cost: Total cost of materials used in construction

        Returns:
            Daily amortization cost
        """
        return total_material_cost * (1 / self.amortization_days)

    def calculate_recipe_cost(
        self, recipe: Recipe, get_buy_price: Optional[Callable[[str], float]] = None
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
                price = (
                    get_buy_price(input.item_symbol)
                    if get_buy_price
                    else self.exchange_service.get_buy_price(
                        exchange_code="AI1", item_symbol=input.item_symbol
                    )
                )
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
            workforce_cost = self.calculate_workforce_cost_for_recipe(recipe)
            total_cost += workforce_cost.total

            # Calculate repair cost
            building = self.building_service.get_building(recipe.building_symbol)
            if building:
                total_material_cost = sum(input_cost.total for input_cost in inputs)
                repair_cost = self.calculate_daily_repair_cost(total_material_cost)
                amortization_cost = self.calculate_amortization_cost(
                    total_material_cost
                )
                total_repair_cost = (repair_cost + amortization_cost) * (
                    recipe.time_ms / (24 * 60 * 60 * 1000)
                )  # Convert ms to days
                total_cost += total_repair_cost
            else:
                total_repair_cost = 0

            return CalculatedRecipeCost(
                recipe_symbol=recipe.symbol,
                building_symbol=recipe.building_symbol,
                time_ms=recipe.time_ms,
                input_costs=CalculatedInputCosts(
                    inputs=inputs,
                    total=sum(input.total for input in inputs),
                ),
                workforce_cost=workforce_cost,
                repair_cost=total_repair_cost,
                total=total_cost,
            )
        except Exception as e:
            logger.error(f"Error calculating recipe cost for {recipe.symbol}: {str(e)}")
            raise

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
            input_cost.total for input_cost in recipe_cost.input_costs
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
            for input_cost in recipe_cost.input_costs
        ]

        return total_input_cost, total_workforce_cost, scaled_input_costs

    def calculate_workforce_cost_for_recipe(
        self, recipe: Recipe
    ) -> CalculatedWorkforceCosts:
        """Calculate the workforce cost for a recipe.

        Args:
            recipe: Recipe

        Returns:
            Total workforce cost
        """
        building = self.building_service.get_building(recipe.building_symbol)
        if not building:
            raise ValueError(f"Building {recipe.building_symbol} not found")

        consumable_costs: List[CalculatedInput] = []
        # Calculate consumables cost for each workforce type
        for workforce_type, workforce_count in [
            ("PIONEER", building.pioneers),
            ("SETTLER", building.settlers),
            ("TECHNICIAN", building.technicians),
            ("ENGINEER", building.engineers),
            ("SCIENTIST", building.scientists),
        ]:
            if workforce_count > 0:
                needs = self.workforce_service.get_workforce_needs(workforce_type)
                for need in needs:
                    price = self.exchange_service.get_buy_price(
                        exchange_code="AI1", item_symbol=need.item_symbol
                    )
                    if not price:
                        raise ValueError(
                            f"No price found for workforce need item {need.item_symbol}"
                        )

                    need_per_workforce_per_day = (
                        need.per_worker_per_day * workforce_count
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

    def calculate_cogm(
        self,
        recipe: Recipe,
        item_symbol: str,
        get_buy_price: Optional[Callable[[str], float]] = None,
    ) -> CalculatedCOGM:
        # Calculate base recipe cost
        recipe_cost = self.calculate_recipe_cost(
            recipe=recipe, get_buy_price=get_buy_price
        )
        recipe_output = next(
            output for output in recipe.outputs if output.item_symbol == item_symbol
        )
        # Calculate scaled recipe cost
        return CalculatedCOGM(
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
