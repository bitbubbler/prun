from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fio import FIOClientInterface
from prun.interface import SystemRepositoryInterface
from prun.models import System, SystemConnection

logger = logging.getLogger(__name__)


class SystemService:
    """Service for handling system operations."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        system_repository: SystemRepositoryInterface,
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.system_repository = system_repository

    def get_system(self, system_id: str) -> Optional[System]:
        """Get a system by ID.

        Args:
            system_id: System ID

        Returns:
            System object if found, None otherwise
        """
        return self.system_repository.get_system(system_id)

    def get_system_by_natural_id(self, natural_id: str) -> Optional[System]:
        """Get a system by natural ID.

        Args:
            natural_id: System natural ID

        Returns:
            System object if found, None otherwise
        """
        return self.system_repository.get_system_by_natural_id(natural_id)
