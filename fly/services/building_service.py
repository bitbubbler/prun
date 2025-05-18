import logging

from typing import Optional

from fio import FIOClientInterface
from fly.interface import BuildingRepositoryInterface
from fly.models import Building, BuildingCost

logger = logging.getLogger(__name__)


class BuildingService:
    """Service for building-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        building_repository: BuildingRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.building_repository = building_repository

    def get_building(self, symbol: str) -> Optional[Building]:
        """Get a building by its symbol.

        Args:
            symbol: Building symbol

        Returns:
            Building if found, None otherwise
        """
        return self.building_repository.get_building(symbol)

    def sync_buildings(self) -> None:
        """Sync buildings from the FIO API to the database.

        Args:
            fio_client: FIO API client
        """
        buildings = self.fio_client.get_buildings()

        for fio_building in buildings:
            # Check if building already exists
            if not self.building_repository.get_building(fio_building.ticker):
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
