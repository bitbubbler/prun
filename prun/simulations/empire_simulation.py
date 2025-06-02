import heapq
from datetime import datetime, timedelta
from typing import Callable

from pydantic import BaseModel

from prun.config import EmpireConfig
from prun.models import (
    Transaction,
    ConsumeTransaction,
    ProduceTransaction,
    ShippingTransaction,
)


class EmpireSimulation(BaseModel):
    """
    A runner for the simulation.
    """

    _events: list[tuple[datetime, Callable[[datetime], None]]]
    empire: EmpireConfig
    transactions: list[Transaction]

    def schedule(self, ts: datetime, fn: Callable[[datetime], None]):
        heapq.heappush(self._events, (ts, fn))

    def run(self, until: datetime) -> None:
        # process events
        while self._events:
            ts, fn = heapq.heappop(self._events)
            if ts > until:
                break
            fn(ts)

    def _process_cycle(self, bld_id: str, ts: datetime):

    def ship(
        self,
        origin,
        destination,
        qty: float,
        depart: datetime,
        travel: timedelta,
        cost: float,
    ):
        """Example of scheduling a shipment departure/arrival."""

        # departure event
        def _depart(ts: datetime):
            self._txns.append(
                SimulationShippingTransaction(
                    timestamp=ts,
                    item_symbol=origin,  # or use a separate field
                    amount=qty,
                    origin=origin,
                    destination=destination,
                    total_price=cost,
                )
            )
            # schedule arrival
            self.schedule(ts + travel, _arrive)

        def _arrive(ts: datetime):
            self._txns.append(
                SimulationShippingTransaction(
                    timestamp=ts,
                    item_symbol=destination,
                    amount=qty,
                    origin=origin,
                    destination=destination,
                    total_price=0.0,  # or record fees on departure only
                )
            )
            # add to inventory on arrival
            self.world.inventories[destination][item_symbol] = (
                self.world.inventories[destination].get(item_symbol, 0) + qty
            )

        self.schedule(depart, _depart)
