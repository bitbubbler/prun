import logging

from fio import FIOClientInterface
from prun.errors import BuildingNotFoundError, PlanetNotFoundError
from prun.interface import SystemRepositoryInterface
from prun.models import (
    Building,
    COGCProgram,
    COGCVote,
    Planet,
    PlanetBuilding,
    PlanetBuildingRequirement,
    PlanetProductionFee,
    PlanetResource,
)

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

    def get_planet(self, natural_id: str) -> Planet | None:
        """Get a planet by natural ID."""
        return self.system_repository.get_planet(natural_id)

    def get_planet_building(
        self, natural_id: str, building: Building
    ) -> PlanetBuilding | None:
        """Get a planet building by natural ID."""
        planet = self.get_planet(natural_id)

        if not planet:
            raise PlanetNotFoundError(f"Planet {natural_id} not found")

        return PlanetBuilding.planet_building_from(building, planet)

    def get_cogc_program(self, natural_id: str) -> COGCProgram | None:
        """Get a COGC program by natural ID."""
        return self.system_repository.get_cogc_program(natural_id)

    def find_planet(self, name: str) -> Planet | None:
        """Find a planet by name."""
        planet = self.get_planet(name)
        if planet:
            return planet

        return self.system_repository.get_planet_by_name(name)
