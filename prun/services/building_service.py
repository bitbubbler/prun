import logging

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from fio import FIOClientInterface
from prun.interface import BuildingRepositoryInterface
from prun.models import Building, BuildingCost, Recipe
from prun.services.exchange_service import ExchangeService
from prun.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)


class CalculatedBuildingCost(BaseModel):
    """Calculated building cost."""

    item_symbol: str
    amount: int
    price: float
    total: float


class BuildingService:
    """Service for building-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        building_repository: BuildingRepositoryInterface,
        exchange_service: ExchangeService,
        recipe_service: RecipeService,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.building_repository = building_repository
        self.exchange_service = exchange_service
        self.recipe_service = recipe_service

    def get_building(self, symbol: str) -> Optional[Building]:
        """Get a building by its symbol.

        Args:
            symbol: Building symbol

        Returns:
            Building if found, None otherwise
        """
        return self.building_repository.get_building(symbol)

    def get_building_costs(self, symbol: str) -> List[BuildingCost]:
        """Get construction costs for a building.

        Args:
            symbol: Building symbol

        Returns:
            List of building costs
        """
        building = self.get_building(symbol)
        if not building:
            raise ValueError(f"Building {symbol} not found")
        return building.building_costs

    def calculate_building_cost(self, symbol: str) -> Dict[str, Any]:
        """Calculate the total construction cost of a building.

        Args:
            symbol: Building symbol

        Returns:
            Dictionary containing building cost details
        """
        building = self.get_building(symbol)
        if not building:
            raise ValueError(f"Building {symbol} not found")

        total_cost: float = 0
        costs: List[CalculatedBuildingCost] = []

        for cost in building.building_costs:
            buy_price = self.exchange_service.get_buy_price(
                exchange_code="AI1", item_symbol=cost.item_symbol
            )
            if buy_price:
                cost_value = cost.amount * buy_price
                total_cost += cost_value
                costs.append(
                    CalculatedBuildingCost(
                        item_symbol=cost.item_symbol,
                        amount=cost.amount,
                        price=buy_price,
                        total=cost_value,
                    )
                )

        return {
            "building": symbol,
            "name": building.name,
            "expertise": building.expertise,
            "pioneers": building.pioneers,
            "settlers": building.settlers,
            "technicians": building.technicians,
            "engineers": building.engineers,
            "scientists": building.scientists,
            "area_cost": building.area_cost,
            "total_cost": total_cost,
            "costs": costs,
        }

    def sync_buildings(self) -> None:
        """Sync buildings from the FIO API to the database.

        Args:
            fio_client: FIO API client
        """
        buildings = self.fio_client.get_buildings()

        for fio_building in buildings:
            # Check if building already exists
            if not self.building_repository.get_building(fio_building.ticker):
                recipes: list[Recipe] = []
                for fio_recipe in fio_building.recipes:
                    recipe = self.recipe_service.get_recipe(
                        fio_recipe.standard_recipe_name
                    )
                    if not recipe:
                        raise ValueError(
                            f"Recipe {fio_recipe.standard_recipe_name} not found"
                        )
                    recipes.append(recipe)

                building = Building.model_validate(
                    {
                        "symbol": fio_building.ticker,
                        "name": fio_building.name,
                        "expertise": fio_building.expertise,
                        "pioneers": fio_building.pioneers,
                        "settlers": fio_building.settlers,
                        "technicians": fio_building.technicians,
                        "engineers": fio_building.engineers,
                        "scientists": fio_building.scientists,
                        "area_cost": fio_building.area_cost,
                        "recipes": recipes,
                    }
                )

                building.building_costs = [
                    BuildingCost.model_validate(
                        {
                            "building_symbol": building.symbol,
                            "item_symbol": cost.commodity_ticker,
                            "amount": cost.amount,
                        }
                    )
                    for cost in fio_building.building_costs
                ]

                # Create building with construction costs
                self.building_repository.create_building(building)
