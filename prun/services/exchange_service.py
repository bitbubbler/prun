import logging

from typing import List, Optional

from fio import FIOClientInterface
from prun.interface import ExchangeRepositoryInterface
from prun.models import ExchangePrice, Exchange

logger = logging.getLogger(__name__)


class ExchangeService:
    """Service for exchange-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        exchange_repository: ExchangeRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
            fio_client: Optional FIO API client
        """
        self.fio_client = fio_client
        self.exchange_repository = exchange_repository

    def get_all_comex_exchanges(self) -> List[Exchange]:
        """Get all comex exchanges from the database."""
        return self.exchange_repository.get_all_comex_exchanges()

    def get_buy_price(self, exchange_code: str, item_symbol: str) -> Optional[float]:
        """Get the buy price for an item.

        Args:
            item_symbol: Item symbol

        Returns:
            Buy price for the item
        """
        exchange_price = self.exchange_repository.get_exchange_price(
            exchange_code=exchange_code, item_symbol=item_symbol
        )
        if exchange_price:
            if exchange_price.ask_price:
                return exchange_price.ask_price
            elif exchange_price.mm_buy:
                return exchange_price.mm_buy
            elif exchange_price.average_price:
                return exchange_price.average_price
            elif exchange_price.bid_price:
                return exchange_price.bid_price
        return None

    def get_sell_price(self, exchange_code: str, item_symbol: str) -> Optional[float]:
        """Get the sell price for an item.

        Args:
            item_symbol: Item symbol

        Returns:
            Sell price for the item
        """
        exchange_price = self.exchange_repository.get_exchange_price(
            exchange_code=exchange_code, item_symbol=item_symbol
        )
        if exchange_price:
            if exchange_price.bid_price:
                return exchange_price.bid_price
            elif exchange_price.mm_sell:
                return exchange_price.mm_sell
            elif exchange_price.average_price:
                return exchange_price.average_price
            elif exchange_price.ask_price:
                return exchange_price.ask_price
        return None

    def delete_exchange_prices(self) -> None:
        """Delete all exchange prices from the database."""
        self.exchange_repository.delete_exchange_prices()
