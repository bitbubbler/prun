import logging

from typing import Optional

from fio import FIOClientInterface
from prun.interface import BuildingRepositoryInterface
from prun.models import Building, BuildingCost

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

    def find_building(self, symbol: str) -> Building:
        """Search for buildings using SQL-like patterns.

        Args:
            pattern: SQL LIKE pattern to search for (e.g. "%FP%")

        Returns:
            List of matching buildings
        """
        return self.building_repository.find_building(symbol)
