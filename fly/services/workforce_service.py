from typing import List, Literal, Optional

from pydantic import BaseModel

from fio import FIOClientInterface
from fly.interface import WorkforceRepositoryInterface
from fly.models import WorkforceNeed, WorkforceFulfillment

WorkforceType = Literal["pioneer", "settler", "technician", "engineer", "scientist"]


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

    def get_workforce_needs(self, workforce_type: str | None = None) -> List[WorkforceNeed]:
        """Get workforce needs, optionally filtered by workforce type.

        Args:
            workforce_type: Optional workforce type to filter by

        Returns:
            List of workforce needs
        """
        return self.workforce_repository.get_workforce_needs(workforce_type)

    def get_workforce_efficiency(
        self, workforce_fulfillment: WorkforceFulfillment, workforce_type: WorkforceType
    ) -> float:
        """Get the workforce efficiency for a given workforce type.

        Args:
            workforce_type: The type of workforce to get efficiency for

        Returns:
            The workforce efficiency for the given workforce type
        """
        if workforce_type == "pioneer":
            p = workforce_fulfillment.pioneer
            return (
                0.02
                * (1 + (p.dw * 10 / 3))
                * (1 + (p.rat * 4))
                * (1 + (p.ove * 5 / 6))
                * (1 + (p.pwo * 1 / 11))
                * (1 + (p.cof * 2 / 13))
            )
        elif workforce_type == "settler":
            s = workforce_fulfillment.settler
            return (
                0.01
                * (1 + (s.dw * 10 / 3))
                * (1 + (s.rat * 4))
                * (1 + (s.exo))
                * (1 + (s.pt * 5 / 6))
                * (1 + (s.rep * 1 / 11))
                * (1 + (s.kom * 2 / 13))
            )
        elif workforce_type == "technician":
            t = workforce_fulfillment.technician
            return (
                0.005
                * (1 + (t.dw * 10 / 3))
                * (1 + (t.rat * 4))
                * (1 + (t.med * 5 / 6))
                * (1 + t.hms)
                * (1 + t.scn)
                * (1 + (t.ale * 2 / 13))
                * (1 + (t.sc / 11))
            )
        elif workforce_type == "engineer":
            e = workforce_fulfillment.engineer
            return (
                0.005
                * (1 + (e.dw * 10 / 3))
                * (1 + (e.fim * 4))
                * (1 + (e.med * 5 / 6))
                * (1 + e.hss)
                * (1 + e.pda)
                * (1 + (e.gin * 2 / 13))
                * (1 + (e.vg / 11))
            )
        elif workforce_type == "scientist":
            sc = workforce_fulfillment.scientist
            return (
                0.005
                * (1 + (sc.dw * 10 / 3))
                * (1 + (sc.mea * 4))
                * (1 + (sc.med * 5 / 6))
                * (1 + sc.lc)
                * (1 + sc.ws)
                * (1 + (sc.win * 2 / 13))
                * (1 + (sc.nst / 11))
            )
        # ... existing code ...

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
        return time_ms / 86400000  # Convert ms to days (24*60*60*1000)
