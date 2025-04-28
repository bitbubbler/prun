import logging

from fio import FIOClientInterface
from prun.interface import WarehouseRepositoryInterface
from prun.models import Warehouse

logger = logging.getLogger(__name__)


class WarehouseService:
    """Service for warehouse-related operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        warehouse_repository: WarehouseRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            fio_client: FIO API client
            warehouse_repository: Repository for warehouse-related database operations
        """
        self.fio_client = fio_client
        self.warehouse_repository = warehouse_repository

    def sync_warehouses(self) -> None:
        """Synchronize warehouses from the API."""
        warehouses = self.fio_client.get_warehouses("CorporateJester")
        # Get all existing warehouses
        existing_warehouses = {
            warehouse.warehouse_id: warehouse
            for warehouse in self.warehouse_repository.get_all_warehouses()
        }

        # Process each warehouse from API
        for fio_warehouse in warehouses:
            # Check if warehouse exists
            existing_warehouse = existing_warehouses.get(fio_warehouse.warehouse_id)
            if existing_warehouse:
                # Update existing warehouse
                existing_warehouse.units = fio_warehouse.units
                existing_warehouse.weight_capacity = fio_warehouse.weight_capacity
                existing_warehouse.volume_capacity = fio_warehouse.volume_capacity
                existing_warehouse.next_payment_timestamp_epoch_ms = (
                    fio_warehouse.next_payment_timestamp_epoch_ms
                )
                existing_warehouse.fee_amount = fio_warehouse.fee_amount
                existing_warehouse.fee_currency = fio_warehouse.fee_currency
                existing_warehouse.fee_collector_id = fio_warehouse.fee_collector_id
                existing_warehouse.fee_collector_name = fio_warehouse.fee_collector_name
                existing_warehouse.fee_collector_code = fio_warehouse.fee_collector_code
                existing_warehouse.location_name = fio_warehouse.location_name
                existing_warehouse.location_natural_id = (
                    fio_warehouse.location_natural_id
                )
            else:
                # Create new warehouse
                warehouse = Warehouse.model_validate(
                    {
                        "warehouse_id": fio_warehouse.warehouse_id,
                        "units": fio_warehouse.units,
                        "weight_capacity": fio_warehouse.weight_capacity,
                        "volume_capacity": fio_warehouse.volume_capacity,
                        "next_payment_timestamp_epoch_ms": fio_warehouse.next_payment_timestamp_epoch_ms,
                        "fee_amount": fio_warehouse.fee_amount,
                        "fee_currency": fio_warehouse.fee_currency,
                        "fee_collector_id": fio_warehouse.fee_collector_id,
                        "fee_collector_name": fio_warehouse.fee_collector_name,
                        "fee_collector_code": fio_warehouse.fee_collector_code,
                        "location_name": fio_warehouse.location_name,
                        "location_natural_id": fio_warehouse.location_natural_id,
                    }
                )
                self.warehouse_repository.create_warehouse(warehouse)
