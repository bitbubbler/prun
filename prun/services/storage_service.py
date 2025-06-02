import logging

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlmodel import select
from typing import List, Dict, Any, Optional

from fio import FIOClientInterface
from prun.interface import StorageRepositoryInterface
from prun.models import ExchangePrice, Storage, StorageItem

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storage-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        storage_repository: StorageRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.storage_repository = storage_repository

    def get_storage(self, storage_id: str) -> Optional[Storage]:
        """Get a storage by its ID.

        Args:
            storage_id: Storage ID

        Returns:
            Storage if found, None otherwise
        """
        return self.storage_repository.get_storage(storage_id)

    def get_storage_items(self, storage_id: str) -> List[StorageItem]:
        """Get all items in a storage.

        Args:
            storage_id: Storage ID

        Returns:
            List of storage items
        """
        storage = self.get_storage(storage_id)
        if not storage:
            raise ValueError(f"Storage {storage_id} not found")
        return storage.stored_items

    def calculate_storage_value(self) -> float:
        """Calculate the total value of all items in storage.

        Returns:
            Total value of all stored items
        """
        total_value: float = 0
        items_with_prices = self.storage_repository.get_storage_items_with_prices()

        for item, price in items_with_prices:
            total_value += item.amount * price.sell_price

        return total_value

    def get_storage_utilization(self, storage_id: str) -> Dict[str, Any]:
        """Get storage utilization metrics.

        Args:
            storage_id: Storage ID

        Returns:
            Dictionary containing storage utilization metrics
        """
        storage = self.get_storage(storage_id)
        if not storage:
            raise ValueError(f"Storage {storage_id} not found")

        total_weight: float = 0
        total_volume: float = 0

        for item in storage.stored_items:
            total_weight += item.total_weight
            total_volume += item.total_volume

        return {
            "storage_id": storage_id,
            "name": storage.name,
            "type": storage.type,
            "weight_capacity": storage.weight_capacity,
            "volume_capacity": storage.volume_capacity,
            "total_weight": total_weight,
            "total_volume": total_volume,
            "weight_utilization": (total_weight / storage.weight_capacity if storage.weight_capacity > 0 else 0),
            "volume_utilization": (total_volume / storage.volume_capacity if storage.volume_capacity > 0 else 0),
        }

    def sync_storage(self, character_id: str) -> None:
        """Sync storage data from the FIO API to the database.

        Args:
            fio_client: FIO API client
            character_id: Character ID to sync storage for
        """
        storage_data = self.fio_client.get_storage(character_id)

        # Delete existing storage data
        self.storage_repository.delete_storage()

        # Create new storage facilities
        for fio_storage in storage_data:
            # Create storage facility
            storage = Storage.model_validate(
                {
                    "storage_id": fio_storage.storage_id,
                    "addressable_id": fio_storage.addressable_id,
                    "name": fio_storage.name,
                    "type": fio_storage.type,
                    "weight_capacity": fio_storage.weight_capacity,
                    "volume_capacity": fio_storage.volume_capacity,
                    "site_id": fio_storage.addressable_id,
                    "warehouse_id": fio_storage.storage_id,  # TODO: Check if this is correct
                }
            )

            for fio_storage_item in fio_storage.storage_items:
                storage.stored_items.append(
                    StorageItem.model_validate(
                        {
                            "storage_id": fio_storage.storage_id,
                            "item_symbol": fio_storage_item.material_ticker,
                            "amount": fio_storage_item.material_amount,
                            "type": fio_storage_item.type,
                        }
                    )
                )

            self.storage_repository.create_storage(storage)
