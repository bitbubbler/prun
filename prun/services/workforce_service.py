from decimal import Decimal
from typing import List, Optional

from fio import FIOClientInterface
from prun.interface import WorkforceRepositoryInterface
from prun.models import WorkforceNeed


class WorkforceService:
    """Service for workforce-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        workforce_repository: WorkforceRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.workforce_repository = workforce_repository

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
                        "amount_per_100_workers_per_day": fio_need.amount,
                    }
                )
                self.workforce_repository.create_workforce_need(workforce_need)

    def workforce_days(self, time_ms: int) -> float:
        """Calculate workforce cost for given time.

        Args:
            workforce_cost_daily: Daily cost of workforce needs
            time_ms: time in milliseconds

        Returns:
            Workforce cost for given time
        """
        # Calculate the time needed as a fraction of a day
        return decimal.Decimal(time_ms / 86400000)  # Convert ms to days (24*60*60*1000)
