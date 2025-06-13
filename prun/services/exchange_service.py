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
            return exchange_price.sell_price
        return None

    def delete_exchange_prices(self) -> None:
        """Delete all exchange prices from the database."""
        self.exchange_repository.delete_exchange_prices()

    def sync_prices(self) -> None:
        """Sync exchange prices from the FIO API to the database.

        Args:
            fio_client: FIO API client
        """
        prices = self.fio_client.get_prices()

        # Delete existing prices
        self.exchange_repository.delete_exchange_prices()

        # Create new prices
        for fio_price in prices:
            exchange_price = ExchangePrice.model_validate(
                {
                    "timestamp": fio_price.timestamp,
                    "mm_buy": fio_price.mm_buy,
                    "mm_sell": fio_price.mm_sell,
                    "average_price": fio_price.average_price,
                    "ask_amount": fio_price.ask_amount,
                    "ask_price": fio_price.ask_price,
                    "ask_available": fio_price.ask_available,
                    "bid_amount": fio_price.bid_amount,
                    "bid_price": fio_price.bid_price,
                    "bid_available": fio_price.bid_available,
                    "item_symbol": fio_price.material_ticker,
                    "exchange_code": fio_price.exchange,
                }
            )
            self.exchange_repository.create_exchange_price(exchange_price)

    def sync_comex_exchanges(self) -> None:
        """Sync commodity exchanges from the FIO API to the database.

        Args:
            fio_client: FIO API client
        """
        exchanges = self.fio_client.get_comex_exchanges()

        # Get existing exchanges for comparison
        existing_exchanges = {
            exchange.comex_exchange_id: exchange
            for exchange in self.exchange_repository.get_all_comex_exchanges()
        }

        for fio_exchange in exchanges:
            # Check if exchange already exists
            if fio_exchange.comex_exchange_id in existing_exchanges:
                # Update existing exchange
                exchange = existing_exchanges[fio_exchange.comex_exchange_id]
                exchange.exchange_name = fio_exchange.exchange_name
                exchange.exchange_code = fio_exchange.exchange_code
                exchange.exchange_operator_id = fio_exchange.exchange_operator_id
                exchange.exchange_operator_code = fio_exchange.exchange_operator_code
                exchange.exchange_operator_name = fio_exchange.exchange_operator_name
                exchange.currency_numeric_code = fio_exchange.currency_numeric_code
                exchange.currency_code = fio_exchange.currency_code
                exchange.currency_name = fio_exchange.currency_name
                exchange.currency_decimals = fio_exchange.currency_decimals
                exchange.location_id = fio_exchange.location_id
                exchange.location_name = fio_exchange.location_name
                exchange.location_natural_id = fio_exchange.location_natural_id
            else:
                # Create new exchange
                comex_exchange = Exchange.model_validate(
                    {
                        "comex_exchange_id": fio_exchange.comex_exchange_id,
                        "exchange_name": fio_exchange.exchange_name,
                        "exchange_code": fio_exchange.exchange_code,
                        "exchange_operator_id": fio_exchange.exchange_operator_id,
                        "exchange_operator_code": fio_exchange.exchange_operator_code,
                        "exchange_operator_name": fio_exchange.exchange_operator_name,
                        "currency_numeric_code": fio_exchange.currency_numeric_code,
                        "currency_code": fio_exchange.currency_code,
                        "currency_name": fio_exchange.currency_name,
                        "currency_decimals": fio_exchange.currency_decimals,
                        "location_id": fio_exchange.location_id,
                        "location_name": fio_exchange.location_name,
                        "location_natural_id": fio_exchange.location_natural_id,
                    }
                )
                self.exchange_repository.create_comex_exchange(comex_exchange)
