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
