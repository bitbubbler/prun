import logging

from datetime import datetime
from typing import List, Dict, Any, Optional

from fio import FIOClientInterface
from prun.interface import SystemRepositoryInterface
from prun.models import Planet

logger = logging.getLogger(__name__)


class PlanetService:
    """Service for handling planet operations."""

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

    def sync_planets(self) -> None:
        """Sync planets from the FIO API to the database.

        Args:
            fio_client: FIO API client

        Raises:
            ValueError: If a planet's system cannot be found in the database
        """
        planets = self.fio_client.get_planets()
        for fio_planet in planets:
            # Extract system natural_id from planet natural_id
            # Format is like "PG-241h", "NL-534a", "PD-175d", "MG-630g" etc
            # The system ID is everything except the last character
            system_natural_id = fio_planet.planet_natural_id[:-1]

            # Get the system
            system = self.system_repository.get_system_by_natural_id(system_natural_id)
            if not system:
                raise ValueError(
                    f"System {system_natural_id} for planet {fio_planet.planet_natural_id} "
                    f"not found in database. Please sync systems first."
                )
            # Check if planet already exists
            if not self.system_repository.get_planet(fio_planet.planet_natural_id):
                planet = Planet.model_validate(
                    {
                        "natural_id": fio_planet.planet_natural_id,
                        "name": fio_planet.planet_name,
                        "system_id": system.system_id,
                    }
                )
                self.system_repository.create_planet(planet)
