import logging
import math

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from prun.errors import MultipleRecipesError
from prun.models import Recipe, RecipeInput, ExchangePrice
from prun.services.building_service import BuildingService
from prun.services.exchange_service import ExchangeService
from prun.services.recipe_service import RecipeService
from prun.services.workforce_service import WorkforceService

logger = logging.getLogger(__name__)


class CalculatedInputCost(BaseModel):
    """Calculated recipe input cost."""

    item_symbol: str = Field(description="The symbol of the item")
    quantity: float = Field(description="The quantity of the item needed for the recipe run")
    price: float = Field(description="The price of the item per unit")
    total: float = Field(description="The total cost of the item for the recipe run")

class CalculatedWorkforceCost(BaseModel):
    """Calculated workforce cost."""
    input_costs: List[CalculatedInputCost]
    total: float

class CalculatedRecipeCost(BaseModel):
    """Calculated recipe cost."""

    recipe_symbol: str
    building_symbol: str
    time_ms: int
    input_costs: List[CalculatedInputCost]
    workforce_cost: CalculatedWorkforceCost
    repair_cost: float
    total: float



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


class CalculatedCOGM(BaseModel):
    """Calculated COGM."""

    recipe_symbol: str
    item_symbol: str
    building_symbol: str
    time_ms: int
    workforce_cost: float
    repair_cost: float
    total_cost: float
    input_costs: List[CalculatedInputCost]
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
            input_costs: List[CalculatedInputCost] = []

            for input, price in input_prices:
                input_cost = input.quantity * price.buy_price
                total_cost += input_cost
                input_costs.append(
                    CalculatedInputCost(
                        item_symbol=input.item_symbol,
                        quantity=input.quantity,
                        price=price.buy_price,
                        total=input_cost,
                    )
                )

            # Calculate workforce cost
            workforce_cost = self.calculate_workforce_cost_for_recipe(recipe)

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
                recipe_symbol=recipe.symbol,
                building_symbol=recipe.building_symbol,
                time_ms=recipe.time_ms,
                input_costs=input_costs,
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
    ) -> tuple[float, float, List[CalculatedInputCost]]:
        """Calculate the final costs based on the number of recipe runs needed.

        Args:
            cost_details: The base recipe cost details
            recipe_runs_needed: Number of times the recipe needs to be run

        Returns:
            Tuple of (total_input_cost, total_workforce_cost, scaled_input_costs)
        """
        # Calculate input costs separately from workforce costs
        total_input_cost = (
            sum(input_cost.total for input_cost in recipe_cost.input_costs)
        )
        total_workforce_cost = recipe_cost.workforce_cost.total

        # Scale the input costs for the total quantity
        scaled_input_costs = [
            CalculatedInputCost(
                item_symbol=input_cost.item_symbol,
                quantity=input_cost.quantity,
                price=input_cost.price,
                total=input_cost.total,
            )
            for input_cost in recipe_cost.input_costs
        ]

        return total_input_cost, total_workforce_cost, scaled_input_costs

    def calculate_workforce_cost_for_recipe(self, recipe: Recipe) -> CalculatedWorkforceCost:
        """Calculate the workforce cost for a recipe.

        Args:
            recipe: Recipe

        Returns:
            Total workforce cost
        """
        building = self.building_service.get_building(recipe.building_symbol)
        if not building:
            raise ValueError(f"Building {recipe.building_symbol} not found")

        consumable_costs: List[CalculatedInputCost] = []
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
                    print(f"item_symbol: {need.item_symbol}")
                    print(f"workforce_count: {workforce_count}")
                    need_per_workforce_per_day = need.per_worker_per_day * workforce_count
                    print(f"need_per_workforce_per_day: {need_per_workforce_per_day}")
                    need_per_recipe_run = need_per_workforce_per_day * self.workforce_service.workforce_days(recipe.time_ms)
                    print(f"need_per_recipe_run: {need_per_recipe_run}")
                    price_per_recipe_run = price * need_per_recipe_run
                    print(f"price_per_recipe_run: {price_per_recipe_run}")
                    
                    consumable_costs.append(
                        CalculatedInputCost(
                            item_symbol=need.item_symbol,
                            quantity=need_per_recipe_run,
                            price=price,
                            total=price_per_recipe_run,
                        )
                    )
        # Convert daily cost to recipe duration cost
        return CalculatedWorkforceCost(
            input_costs=consumable_costs,
            total=sum(consumable_cost.total for consumable_cost in consumable_costs),
        )

    def calculate_cogm(
        self,
        item_symbol: str,
        recipe_symbol: Optional[str] = None,
    ) -> CalculatedCOGM:
        # Get and validate the recipe
        recipe: Recipe = self.recipe_service.find_recipe(item_symbol, recipe_symbol)
        recipe_output = next(
            output for output in recipe.outputs if output.item_symbol == item_symbol
        )

        # Get recipe with current prices
        recipe, input_prices = self.recipe_service.get_recipe_with_prices(recipe.symbol)

        # Calculate base recipe cost
        recipe_cost = self.calculate_recipe_cost(recipe, input_prices)

        # Calculate the proportion of target output to total recipe output
        total_recipe_output = sum(output.quantity for output in recipe.outputs)
        output_proportion = recipe_output.quantity / total_recipe_output if total_recipe_output > 0 else 1.0

        # Calculate final costs
        total_input_cost, total_workforce_cost, scaled_input_costs = (
            self._calculate_final_costs(
                recipe_cost
            )
        )

        # Scale input costs by output proportion
        scaled_input_costs = [
            CalculatedInputCost(
                item_symbol=input_cost.item_symbol,
                quantity=input_cost.quantity * output_proportion,
                price=input_cost.price,
                total=input_cost.total * output_proportion,
            )
            for input_cost in scaled_input_costs
        ]


        # Calculate total repair cost, scaled by the output proportion
        total_repair_cost = recipe_cost.repair_cost * output_proportion
       
        # Calculate the final total cost as the sum of all scaled costs
        final_total_cost = sum(input_cost.total for input_cost in scaled_input_costs) + scaled_workforce_cost + total_repair_cost

        return CalculatedCOGM(
            recipe_symbol=recipe.symbol,
            item_symbol=item_symbol,
            building_symbol=recipe.building_symbol,
            time_ms=recipe.time_ms,
            input_costs=scaled_input_costs,
            workforce_cost=scaled_workforce_cost,
            repair_cost=total_repair_cost,
            total_cost=final_total_cost,
            workforce_needs=workforce_needs,
        )
