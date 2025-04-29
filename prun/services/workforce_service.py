from pydantic import BaseModel
from typing import List, Optional

from fio import FIOClientInterface
from prun.interface import (
    WorkforceRepositoryInterface,
)
from prun.models import Recipe, WorkforceNeed
from prun.services.building_service import BuildingService
from prun.services.exchange_service import ExchangeService


class WorkforceService:
    """Service for workforce-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        workforce_repository: WorkforceRepositoryInterface,
        building_service: BuildingService,
        exchange_service: ExchangeService,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.workforce_repository = workforce_repository
        self.building_service = building_service
        self.exchange_service = exchange_service

    def get_workforce_needs(
        self, workforce_type: Optional[str] = None
    ) -> List[WorkforceNeed]:
        """Get workforce needs, optionally filtered by workforce type.

        Args:
            workforce_type: Optional workforce type to filter by

        Returns:
            List of workforce needs
        """
        return self.workforce_repository.get_workforce_needs(workforce_type)

    def sync_workforce_needs(self) -> None:
        """Sync workforce needs from the FIO API to the database.

        Args:
            fio_client: FIO API client
        """
        fio_workforce_needs = self.fio_client.get_workforce_needs()
        # Delete existing workforce needs
        self.workforce_repository.delete_workforce_needs()

        # Create new workforce needs
        for fio_workforce_need in fio_workforce_needs:
            for fio_need in fio_workforce_need.needs:
                workforce_need = WorkforceNeed.model_validate(
                    {
                        "workforce_type": fio_workforce_need.workforce_type,
                        "item_symbol": fio_need.material_ticker,
                        "amount": fio_need.amount / 100,  # Convert from per 100 workers to per worker
                    }
                )
                self.workforce_repository.create_workforce_need(workforce_need)

    def workforce_days(self, workforce_cost_daily: float, time_ms: int) -> float:
        """Calculate workforce cost for given time.

        Args:
            workforce_cost_daily: Daily cost of workforce needs
            time_ms: time in milliseconds

        Returns:
            Workforce cost for given time
        """
        # Calculate the time needed as a fraction of a day
        time_days = time_ms / (24 * 60 * 60 * 1000)  # Convert ms to days

        # Calculate prorated workforce cost based on time needed
        return workforce_cost_daily * time_days


class CalculatedItemNeed(BaseModel):
    item: str
    daily_amount: float
    daily_cost: float


class CalculatedWorkforceNeed(BaseModel):
    type: str
    daily_amount: float
    daily_cost: float
