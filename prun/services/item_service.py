import logging
from typing import Optional

from fio import FIOClientInterface
from prun.interface import ItemRepositoryInterface
from prun.models import Item

logger = logging.getLogger(__name__)


class ItemService:
    """Service for item-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        item_repository: ItemRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            fio_client: FIO API client
            item_repository: Repository for item-related database operations
        """
        self.fio_client = fio_client
        self.item_repository = item_repository

    def get_item(self, symbol: str) -> Optional[Item]:
        """Get an item by its symbol.

        Args:
            symbol: Item symbol

        Returns:
            Item if found, None otherwise
        """
        return self.item_repository.get_item(symbol)

    def sync_materials(self) -> None:
        """Sync materials from the FIO API to the database."""
        materials = self.fio_client.get_all_materials()
        for material in materials:
            # Check if item already exists
            if not self.item_repository.get_item(material.ticker):
                item = Item.model_validate(
                    {
                        "symbol": material.ticker,
                        "name": material.name,
                        "category": material.category,
                        "weight": float(material.weight),
                        "volume": float(material.volume),
                    }
                )
                self.item_repository.create_item(item)
