import logging
from typing import Optional

from prun.errors import PlanetNotFoundError, RecipeNotFoundError
from prun.models import (
    EfficientRecipe,
    EfficientPlanetExtractionRecipe,
    InputPriceBand,
    Planet,
    RecipeComparison,
    RecipePriceBands,
)
from prun.services.cost_service import CostContext, CostService
from prun.services.exchange_service import ExchangeService
from prun.services.planet_service import PlanetService
from prun.services.recipe_service import RecipeService
from prun.util import round_half_up

logger = logging.getLogger(__name__)


class InputPricingService:
    """Service for calculating input price bands for profitable production."""

    def __init__(
        self,
        cost_service: CostService,
        exchange_service: ExchangeService,
        recipe_service: RecipeService,
        planet_service: PlanetService,
    ):
        self.cost_service = cost_service
        self.exchange_service = exchange_service
        self.recipe_service = recipe_service
        self.planet_service = planet_service

    def calculate_price_bands(
        self,
        item_symbol: str,
        planet_name: str,
        profit_margin_percent: float,
        recipe_symbol: Optional[str] = None,
        exchange_code: str = "NC1",
    ) -> RecipePriceBands:
        """Calculate price bands automatically from market data.

        Args:
            item_symbol: Output item to produce (e.g., "SI")
            planet_name: Planet where production occurs
            profit_margin_percent: Target profit margin (e.g., 25.0 for 25%)
            recipe_symbol: Optional specific recipe, otherwise finds best one
            exchange_code: Exchange to get market prices from

        Returns:
            Complete price band analysis with recommendations
        """
        # 1. Get planet
        planet = self.planet_service.find_planet(planet_name)
        if not planet:
            raise PlanetNotFoundError(planet_name)

        # 2. Get current market selling price automatically
        target_selling_price = self.exchange_service.get_sell_price(
            exchange_code, item_symbol
        )
        if not target_selling_price:
            raise ValueError(
                f"No sell price found for {item_symbol} on {exchange_code}"
            )

        # 3. Calculate target profit from margin
        target_profit = target_selling_price * (profit_margin_percent / 100)

        # 4. Find recipe (or get specified one)
        if recipe_symbol:
            recipe = self.recipe_service.find_recipe(
                item_symbol=item_symbol,
                recipe_symbol=recipe_symbol,
                planet=planet,
            )
        else:
            # Find all recipes and use the first one as default
            all_recipes = self.recipe_service.find_all_recipes(
                item_symbol=item_symbol,
                planet=planet,
            )
            if not all_recipes:
                raise RecipeNotFoundError(
                    f"No recipes found for {item_symbol} on {planet_name}"
                )
            recipe = all_recipes[0]  # Use first recipe as default

        if not recipe:
            if recipe_symbol:
                raise RecipeNotFoundError(f"Recipe {recipe_symbol} not found")
            else:
                raise RecipeNotFoundError(
                    f"No recipe found for {item_symbol} on {planet_name}"
                )

        # 5. Get efficient recipe with default (no) experts for baseline calculation
        from prun.models import Experts  # Import here to avoid circular import

        default_experts = Experts()  # Empty experts object (all zeros)

        if recipe.is_resource_extraction_recipe:
            # For resource extraction, we need planet resource
            planet_resource = next(
                (
                    resource
                    for resource in planet.resources
                    if resource.item.symbol == item_symbol
                ),
                None,
            )
            efficient_recipe = (
                self.recipe_service.get_efficient_planet_extraction_recipe(
                    recipe_symbol=recipe.symbol,
                    planet_resource=planet_resource,
                    experts=default_experts,  # Default experts for baseline
                    cogc_program=None,
                )
            )
        else:
            efficient_recipe = self.recipe_service.get_efficient_recipe(
                recipe_symbol=recipe.symbol,
                experts=default_experts,  # Default experts for baseline
                cogc_program=None,
            )

        # 6. Calculate fixed costs using temporary cost context
        mock_cost_context = self._create_mock_cost_context(exchange_code)

        workforce_cost = self.cost_service.calculate_workforce_cost_for_recipe(
            cost_context=mock_cost_context,
            recipe=efficient_recipe,
            planet=planet,
        )

        repair_cost = self.cost_service.calculate_repair_cost_for_recipe(
            cost_context=mock_cost_context,
            recipe=efficient_recipe,
            planet=planet,
        )

        fixed_costs_total = workforce_cost.total + repair_cost.total

        # 7. Calculate budget tiers
        excellent_budget = (
            target_selling_price - (target_profit * 1.4) - fixed_costs_total
        )  # 40% better margin
        good_budget = target_selling_price - target_profit - fixed_costs_total
        acceptable_budget = (
            target_selling_price - (target_profit * 0.5) - fixed_costs_total
        )  # Half margin
        break_even_budget = target_selling_price - fixed_costs_total

        # 8. Allocate budgets across inputs using market proportional strategy
        input_bands = self._calculate_input_bands(
            efficient_recipe,
            exchange_code,
            excellent_budget,
            good_budget,
            acceptable_budget,
            break_even_budget,
        )

        # 9. Calculate current profitability assessment
        total_current_input_cost = sum(
            (band.current_ask_price or 0) * band.quantity for band in input_bands
        )
        actual_profit = (
            target_selling_price - total_current_input_cost - fixed_costs_total
        )
        actual_margin_percent = (
            (actual_profit / target_selling_price) * 100
            if target_selling_price > 0
            else 0
        )

        # Determine current profitability tier
        current_profitability = self._assess_profitability(
            actual_margin_percent, profit_margin_percent
        )

        return RecipePriceBands(
            recipe_symbol=efficient_recipe.symbol,
            item_symbol=item_symbol,
            planet_name=planet_name,
            target_selling_price=target_selling_price,
            target_profit_margin_percent=profit_margin_percent,
            target_profit=target_profit,
            workforce_cost=workforce_cost.total,
            repair_cost=repair_cost.total,
            fixed_costs_total=fixed_costs_total,
            excellent_budget=excellent_budget,
            good_budget=good_budget,
            acceptable_budget=acceptable_budget,
            break_even_budget=break_even_budget,
            input_bands=input_bands,
            current_profitability=current_profitability,
            total_current_input_cost=total_current_input_cost,
            actual_profit=actual_profit,
            actual_margin_percent=actual_margin_percent,
        )

    def compare_all_recipes(
        self,
        item_symbol: str,
        planet_name: str,
        profit_margin_percent: float,
        exchange_code: str = "NC1",
    ) -> RecipeComparison:
        """Compare all recipes for an item and recommend the best one."""
        # Get planet
        planet = self.planet_service.find_planet(planet_name)
        if not planet:
            raise PlanetNotFoundError(planet_name)

        # Find all recipes for this item
        recipes = self.recipe_service.find_all_recipes(
            item_symbol=item_symbol,
            planet=planet,
        )

        if not recipes:
            raise RecipeNotFoundError(
                f"No recipes found for {item_symbol} on {planet_name}"
            )

        # Calculate price bands for each recipe
        recipe_analyses = []
        for recipe in recipes:
            try:
                analysis = self.calculate_price_bands(
                    item_symbol=item_symbol,
                    planet_name=planet_name,
                    profit_margin_percent=profit_margin_percent,
                    recipe_symbol=recipe.symbol,
                    exchange_code=exchange_code,
                )
                recipe_analyses.append(analysis)
            except Exception as e:
                logger.warning(f"Failed to analyze recipe {recipe.symbol}: {e}")
                continue

        if not recipe_analyses:
            raise ValueError("No recipes could be analyzed")

        # Find the best recipe (highest actual profit)
        best_recipe = max(recipe_analyses, key=lambda r: r.actual_profit)

        reasoning = f"Recommended {best_recipe.recipe_symbol} with {best_recipe.actual_margin_percent:.1f}% margin (${best_recipe.actual_profit:.2f} profit)"

        return RecipeComparison(
            item_symbol=item_symbol,
            planet_name=planet_name,
            target_profit_margin_percent=profit_margin_percent,
            recipe_analyses=recipe_analyses,
            recommended_recipe=best_recipe.recipe_symbol,
            reasoning=reasoning,
        )

    def _create_mock_cost_context(self, exchange_code: str) -> CostContext:
        """Create a mock cost context for calculating fixed costs."""

        def get_buy_price(item_symbol: str) -> float:
            price = self.exchange_service.get_buy_price(exchange_code, item_symbol)
            if price is None:
                # Fallback to a reasonable default if no price found
                return 100.0
            return price

        def set_cogm_price(item_symbol: str, price: float) -> None:
            pass  # Not needed for fixed cost calculation

        return CostContext(
            get_buy_price=get_buy_price,
            set_cogm_price=set_cogm_price,
            cogm_price_cache={},
        )

    def _calculate_input_bands(
        self,
        recipe: EfficientRecipe | EfficientPlanetExtractionRecipe,
        exchange_code: str,
        excellent_budget: float,
        good_budget: float,
        acceptable_budget: float,
        break_even_budget: float,
    ) -> list[InputPriceBand]:
        """Calculate price bands for recipe inputs using market proportional allocation."""
        input_bands = []

        # First, get current market prices to calculate proportions
        total_current_cost = 0
        input_market_data = []

        for recipe_input in recipe.inputs:
            current_ask_price = self.exchange_service.get_buy_price(
                exchange_code, recipe_input.item_symbol
            )
            if current_ask_price is None:
                current_ask_price = 100.0  # Fallback price

            current_cost = current_ask_price * recipe_input.quantity
            total_current_cost += current_cost

            input_market_data.append(
                {
                    "input": recipe_input,
                    "current_ask_price": current_ask_price,
                    "current_cost": current_cost,
                }
            )

        # Calculate price bands for each input
        for data in input_market_data:
            recipe_input = data["input"]
            current_ask_price = data["current_ask_price"]

            # Calculate proportion of this input in total cost
            if total_current_cost > 0:
                proportion = data["current_cost"] / total_current_cost
            else:
                proportion = 1.0 / len(
                    input_market_data
                )  # Equal split if no market data

            # Allocate budget proportionally
            excellent_allocation = excellent_budget * proportion
            good_allocation = good_budget * proportion
            acceptable_allocation = acceptable_budget * proportion
            break_even_allocation = break_even_budget * proportion

            # Calculate price per unit
            quantity = recipe_input.quantity
            excellent_price = excellent_allocation / quantity if quantity > 0 else 0
            good_price = good_allocation / quantity if quantity > 0 else 0
            acceptable_price = acceptable_allocation / quantity if quantity > 0 else 0
            break_even_price = break_even_allocation / quantity if quantity > 0 else 0

            # Set loss threshold slightly above break even
            loss_threshold = break_even_price * 1.1

            # Determine recommendation
            recommendation = self._get_input_recommendation(
                current_ask_price,
                excellent_price,
                good_price,
                acceptable_price,
                break_even_price,
            )

            input_bands.append(
                InputPriceBand(
                    item_symbol=recipe_input.item_symbol,
                    quantity=quantity,
                    excellent_buy=float(round_half_up(excellent_price)),
                    good_buy=float(round_half_up(good_price)),
                    acceptable_buy=float(round_half_up(acceptable_price)),
                    break_even=float(round_half_up(break_even_price)),
                    loss_threshold=float(round_half_up(loss_threshold)),
                    current_ask_price=current_ask_price,
                    recommendation=recommendation,
                )
            )

        return input_bands

    def _get_input_recommendation(
        self,
        current_price: float,
        excellent_price: float,
        good_price: float,
        acceptable_price: float,
        break_even_price: float,
    ) -> str:
        """Determine recommendation based on current price vs. price bands."""
        if current_price <= excellent_price:
            return "EXCELLENT"
        elif current_price <= good_price:
            return "GOOD"
        elif current_price <= acceptable_price:
            return "ACCEPTABLE"
        elif current_price <= break_even_price:
            return "BREAK_EVEN"
        else:
            return "AVOID"

    def _assess_profitability(
        self, actual_margin_percent: float, target_margin_percent: float
    ) -> str:
        """Assess current profitability tier."""
        if actual_margin_percent >= target_margin_percent * 1.3:
            return "EXCELLENT"
        elif actual_margin_percent >= target_margin_percent:
            return "GOOD"
        elif actual_margin_percent >= target_margin_percent * 0.5:
            return "ACCEPTABLE"
        elif actual_margin_percent > 0:
            return "BREAK_EVEN"
        else:
            return "LOSS"
