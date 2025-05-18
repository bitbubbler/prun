from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fio import FIOClientInterface
from fly.interface import SystemRepositoryInterface
from fly.models import System, SystemConnection

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

    def sync_systems(self) -> None:
        """Sync systems from the FIO API to the database.

        Args:
            fio_client: FIO API client
        """
        systems = self.fio_client.get_systems()
        for fio_system in systems:
            # Check if system already exists
            if not self.system_repository.get_system(fio_system.system_id):
                # Create system with connections
                system = System.model_validate(
                    {
                        "system_id": fio_system.system_id,
                        "name": fio_system.name,
                        "natural_id": fio_system.natural_id,
                        "type": fio_system.type,
                        "position_x": float(fio_system.position_x),
                        "position_y": float(fio_system.position_y),
                        "position_z": float(fio_system.position_z),
                        "sector_id": fio_system.sector_id,
                        "sub_sector_id": fio_system.sub_sector_id,
                    }
                )

                system.connections = [
                    SystemConnection.model_validate(
                        {
                            "connecting_id": conn.connecting_id,
                            "system_connection_id": conn.system_connection_id,
                            "system_id": system.system_id,
                        }
                    )
                    for conn in fio_system.connections
                ]

                self.system_repository.create_system(system)

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
