import logging
import math

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from prun.errors import MultipleRecipesError
from prun.models import Recipe, RecipeInput, ExchangePrice
from prun.services.building_service import BuildingService
from prun.services.exchange_service import ExchangeService
from prun.services.recipe_service import RecipeService
from prun.services.workforce_service import WorkforceService

logger = logging.getLogger(__name__)


class CalculatedRecipeInputCost(BaseModel):
    """Calculated recipe input cost."""

    item_symbol: str
    quantity: float
    price: float
    total: float


class CalculatedRecipeCost(BaseModel):
    """Calculated recipe cost."""

    recipe: str
    building: str
    time_ms: int
    input_costs: List[CalculatedRecipeInputCost]
    workforce_cost: float
    repair_cost: float
    total_cost: float


class WorkforceNeed(BaseModel):
    """Daily need for a specific item by a workforce type."""

    item: str
    daily_amount: float
    daily_cost: float


class WorkforceTypeNeeds(BaseModel):
    """Needs for a specific workforce type."""

    type: str
    workers: int
    needs: List[WorkforceNeed]


class RecipeOutput(BaseModel):
    """Output from a recipe."""

    item: str
    quantity: float
    is_target: bool = False


class CalculatedCOGM(BaseModel):
    """Calculated COGM."""

    recipe_symbol: str
    item: str
    quantity: int
    recipe: str
    building: str
    time_ms: int
    recipe_runs_needed: float
    input_costs: List[CalculatedRecipeInputCost]
    workforce_cost: float
    repair_cost: float
    total_cost: float
    recipe_outputs: List[RecipeOutput]
    workforce_needs: List[WorkforceTypeNeeds]


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

    def calculate_daily_repair_cost(self, total_material_cost: float, days_since_build: int = 89) -> float:
        """Calculate daily repair cost based on total material cost and days since build.
        
        Args:
            total_material_cost: Total cost of materials used in construction
            days_since_build: Number of days since the building was constructed
            
        Returns:
            Daily repair cost
        """
        return (total_material_cost - math.floor(total_material_cost * ((self.amortization_days - min(days_since_build, self.amortization_days)) / self.amortization_days))) * (1/days_since_build)

    def calculate_amortization_cost(self, total_material_cost: float) -> float:
        """Calculate daily amortization cost.
        
        Args:
            total_material_cost: Total cost of materials used in construction
            
        Returns:
            Daily amortization cost
        """
        return total_material_cost * (1/self.amortization_days)

    def calculate_recipe_cost(
        self, recipe: Recipe, input_prices: List[tuple[RecipeInput, ExchangePrice]]
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
            input_costs: List[CalculatedRecipeInputCost] = []

            for input, price in input_prices:
                input_cost = input.quantity * price.buy_price
                total_cost += input_cost
                input_costs.append(
                    CalculatedRecipeInputCost(
                        item_symbol=input.item_symbol,
                        quantity=input.quantity,
                        price=price.buy_price,
                        total=input_cost,
                    )
                )

            # Calculate workforce cost
            workforce_cost = self.calculate_workforce_cost_for_recipe(recipe)
            total_cost += workforce_cost

            # Calculate repair cost
            building = self.building_service.get_building(recipe.building_symbol)
            if building:
                total_material_cost = sum(input_cost.total for input_cost in input_costs)
                repair_cost = self.calculate_daily_repair_cost(total_material_cost)
                amortization_cost = self.calculate_amortization_cost(total_material_cost)
                total_repair_cost = (repair_cost + amortization_cost) * (recipe.time_ms / (24 * 60 * 60 * 1000))  # Convert ms to days
                total_cost += total_repair_cost
            else:
                total_repair_cost = 0

            return CalculatedRecipeCost(
                recipe=recipe.symbol,
                building=recipe.building_symbol,
                time_ms=recipe.time_ms,
                input_costs=input_costs,
                workforce_cost=workforce_cost,
                repair_cost=total_repair_cost,
                total_cost=total_cost,
            )
        except Exception as e:
            logger.error(f"Error calculating recipe cost for {recipe.symbol}: {str(e)}")
            raise

    def _calculate_recipe_runs_needed(
        self, recipe: Recipe, item_symbol: str, item_quantity: int
    ) -> float:
        """Calculate how many recipe runs are needed to produce the desired quantity.

        For example, if a recipe produces 2 items in 1000ms, and we want 10 items,
        we need to run the recipe 5 times (10/2 = 5).

        Args:
            recipe: The recipe to calculate for
            item_symbol: Symbol of the item being produced
            item_quantity: Desired quantity of the item

        Returns:
            Number of times the recipe needs to be run
        """
        output = next(
            output for output in recipe.outputs if output.item_symbol == item_symbol
        )
        if output.quantity <= 0:
            raise ValueError(
                f"Recipe output quantity for {item_symbol} must be greater than 0"
            )
        return item_quantity / output.quantity

    def _calculate_final_costs(
        self,
        cost_details: CalculatedRecipeCost,
        recipe_runs_needed: float,
        output_quantity: float,
    ) -> tuple[float, float, List[CalculatedRecipeInputCost]]:
        """Calculate the final costs based on the number of recipe runs needed.

        Args:
            cost_details: The base recipe cost details
            recipe_runs_needed: Number of times the recipe needs to be run

        Returns:
            Tuple of (total_input_cost, total_workforce_cost, scaled_input_costs)
        """
        # Calculate input costs separately from workforce costs
        total_input_cost = (
            sum(input_cost.total for input_cost in cost_details.input_costs)
            * recipe_runs_needed
        )
        total_workforce_cost = cost_details.workforce_cost * recipe_runs_needed

        # Scale the input costs for the total quantity
        scaled_input_costs = [
            CalculatedRecipeInputCost(
                item_symbol=input_cost.item_symbol,
                quantity=input_cost.quantity * recipe_runs_needed,
                price=input_cost.price,
                total=input_cost.total * recipe_runs_needed,
            )
            for input_cost in cost_details.input_costs
        ]

        return total_input_cost, total_workforce_cost, scaled_input_costs

    def calculate_workforce_cost_for_recipe(self, recipe: Recipe) -> float:
        """Calculate the workforce cost for a recipe.

        Args:
            recipe: Recipe

        Returns:
            Total workforce cost
        """
        building = self.building_service.get_building(recipe.building_symbol)
        if not building:
            raise ValueError(f"Building {recipe.building_symbol} not found")

        daily_cost: float = 0

        # Calculate cost for each workforce type
        for workforce_type, count in [
            ("PIONEER", building.pioneers),
            ("SETTLER", building.settlers),
            ("TECHNICIAN", building.technicians),
            ("ENGINEER", building.engineers),
            ("SCIENTIST", building.scientists),
        ]:
            if count > 0:
                needs = self.workforce_service.get_workforce_needs(workforce_type)
                for need in needs:
                    price = self.exchange_service.get_buy_price(
                        exchange_code="AI1", item_symbol=need.item_symbol
                    )
                    if not price:
                        raise ValueError(
                            f"No price found for workforce need item {need.item_symbol}"
                        )
                    # Calculate daily cost for this need
                    daily_need_cost = need.amount * count * price
                    daily_cost += daily_need_cost

        # Convert daily cost to recipe duration cost
        return self.workforce_service.workforce_days(daily_cost, recipe.time_ms)

    def calculate_cogm(
        self,
        item_symbol: str,
        item_quantity: int = 1,
        recipe_symbol: Optional[str] = None,
    ) -> CalculatedCOGM:
        """Calculate the cost of goods manufactured (COGM) for a specific quantity of an item.

        Args:
            item_symbol: Symbol of the item to calculate COGM for
            item_quantity: Number of items to calculate COGM for (default: 1)
            recipe_symbol: Optional specific recipe to use

        Returns:
            Dictionary containing COGM details
        """
        # Get and validate the recipe
        recipe: Recipe = self.recipe_service.find_recipe(item_symbol, recipe_symbol)
        recipe_output = next(
            output for output in recipe.outputs if output.item_symbol == item_symbol
        )

        # Get recipe with current prices
        recipe, input_prices = self.recipe_service.get_recipe_with_prices(recipe.symbol)

        # Calculate base recipe cost
        cost_details = self.calculate_recipe_cost(recipe, input_prices)

        # Calculate how many times we need to run the recipe
        recipe_runs_needed = self._calculate_recipe_runs_needed(
            recipe, item_symbol, item_quantity
        )

        # Calculate final costs
        total_input_cost, total_workforce_cost, scaled_input_costs = (
            self._calculate_final_costs(
                cost_details, recipe_runs_needed, recipe_output.quantity
            )
        )

        # Calculate total repair cost
        total_repair_cost = cost_details.repair_cost * recipe_runs_needed

        # Calculate workforce needs
        workforce_needs = []
        if self.workforce_service:
            building = self.building_service.get_building(recipe.building_symbol)
            if building:
                for workforce_type in [
                    "PIONEERS",
                    "SETTLERS",
                    "TECHNICIANS",
                    "ENGINEERS",
                    "SCIENTISTS",
                ]:
                    workers = getattr(building, workforce_type.lower())
                    if workers > 0:
                        needs = self.workforce_service.get_workforce_needs(
                            workforce_type[
                                :-1
                            ]  # Remove the 'S' to get the singular form
                        )
                        if needs:
                            daily_needs = []
                            for need in needs:
                                daily_amount = need.amount * workers
                                daily_cost = (
                                    daily_amount
                                    * self.exchange_service.get_buy_price(
                                        "AI1", need.item_symbol
                                    )
                                )
                                daily_needs.append(
                                    WorkforceNeed(
                                        item=need.item_symbol,
                                        daily_amount=daily_amount,
                                        daily_cost=daily_cost,
                                    )
                                )

                            workforce_needs.append(
                                WorkforceTypeNeeds(
                                    type=workforce_type[
                                        :-1
                                    ],  # Remove the 'S' to get the singular form
                                    workers=workers,
                                    needs=daily_needs,
                                )
                            )

        return CalculatedCOGM(
            recipe_symbol=recipe.symbol,
            item=item_symbol,
            quantity=item_quantity,
            recipe=recipe.symbol,
            building=recipe.building_symbol,
            time_ms=recipe.time_ms,
            recipe_runs_needed=recipe_runs_needed,
            input_costs=scaled_input_costs,
            workforce_cost=total_workforce_cost,
            repair_cost=total_repair_cost,
            total_cost=total_input_cost + total_workforce_cost + total_repair_cost,
            recipe_outputs=[
                RecipeOutput(
                    item=output.item_symbol,
                    quantity=output.quantity,
                    is_target=output.item_symbol == item_symbol,
                )
                for output in recipe.outputs
            ],
            workforce_needs=workforce_needs,
        )
