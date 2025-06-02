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

    def get_planet_building(self, natural_id: str, building: Building) -> PlanetBuilding | None:
        """Get a planet building by natural ID."""
        planet = self.get_planet(natural_id)

        if not planet:
            raise PlanetNotFoundError(f"Planet {natural_id} not found")

        return PlanetBuilding.planet_building_from(building, planet)

    def find_planet(self, name: str) -> Planet | None:
        """Find a planet by name."""
        planet = self.get_planet(name)
        if planet:
            return planet

        return self.system_repository.get_planet_by_name(name)

    def sync_planets(self) -> None:
        """Sync planets from the FIO API to the database.

        This method syncs planet information and all related data (resources,
        building requirements, production fees, COGC programs, and votes) in a single
        call to the FIO API.

        Raises:
            ValueError: If a planet's system cannot be found in the database
        """
        planets = self.fio_client.get_planets_full()
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
            existing_planet = self.system_repository.get_planet(fio_planet.planet_natural_id)
            if not existing_planet:
                planet = Planet.model_validate(
                    {
                        "natural_id": fio_planet.planet_natural_id,
                        "name": fio_planet.planet_name,
                        "system_id": system.system_id,
                        "planet_id": fio_planet.planet_id,
                        "gravity": fio_planet.gravity,
                        "magnetic_field": fio_planet.magnetic_field,
                        "mass": fio_planet.mass,
                        "mass_earth": fio_planet.mass_earth,
                        "orbit_semi_major_axis": fio_planet.orbit_semi_major_axis,
                        "orbit_eccentricity": fio_planet.orbit_eccentricity,
                        "orbit_inclination": fio_planet.orbit_inclination,
                        "orbit_right_ascension": fio_planet.orbit_right_ascension,
                        "orbit_periapsis": fio_planet.orbit_periapsis,
                        "orbit_index": fio_planet.orbit_index,
                        "pressure": fio_planet.pressure,
                        "radiation": fio_planet.radiation,
                        "radius": fio_planet.radius,
                        "sunlight": fio_planet.sunlight,
                        "surface": fio_planet.surface,
                        "temperature": fio_planet.temperature,
                        "fertility": fio_planet.fertility,
                        "has_local_market": fio_planet.has_local_market,
                        "has_chamber_of_commerce": fio_planet.has_chamber_of_commerce,
                        "has_warehouse": fio_planet.has_warehouse,
                        "has_administration_center": fio_planet.has_administration_center,
                        "has_shipyard": fio_planet.has_shipyard,
                        "faction_code": fio_planet.faction_code,
                        "faction_name": fio_planet.faction_name,
                        "governor_id": fio_planet.governor_id,
                        "governor_user_name": fio_planet.governor_user_name,
                        "governor_corporation_id": fio_planet.governor_corporation_id,
                        "governor_corporation_name": fio_planet.governor_corporation_name,
                        "governor_corporation_code": fio_planet.governor_corporation_code,
                        "currency_name": fio_planet.currency_name,
                        "currency_code": fio_planet.currency_code,
                        "collector_id": fio_planet.collector_id,
                        "collector_name": fio_planet.collector_name,
                        "collector_code": fio_planet.collector_code,
                        "base_local_market_fee": fio_planet.base_local_market_fee,
                        "local_market_fee_factor": fio_planet.local_market_fee_factor,
                        "warehouse_fee": fio_planet.warehouse_fee,
                        "population_id": fio_planet.population_id,
                        "cogc_program_status": fio_planet.cogc_program_status,
                        "planet_tier": fio_planet.planet_tier,
                        "timestamp": fio_planet.timestamp,
                    }
                )
                self.system_repository.create_planet(planet)
            else:
                planet = existing_planet
                # Update existing planet with new data
                existing_planet.name = fio_planet.planet_name
                existing_planet.system_id = system.system_id
                existing_planet.planet_id = fio_planet.planet_id
                existing_planet.gravity = fio_planet.gravity
                existing_planet.magnetic_field = fio_planet.magnetic_field
                existing_planet.mass = fio_planet.mass
                existing_planet.mass_earth = fio_planet.mass_earth
                existing_planet.orbit_semi_major_axis = fio_planet.orbit_semi_major_axis
                existing_planet.orbit_eccentricity = fio_planet.orbit_eccentricity
                existing_planet.orbit_inclination = fio_planet.orbit_inclination
                existing_planet.orbit_right_ascension = fio_planet.orbit_right_ascension
                existing_planet.orbit_periapsis = fio_planet.orbit_periapsis
                existing_planet.orbit_index = fio_planet.orbit_index
                existing_planet.pressure = fio_planet.pressure
                existing_planet.radiation = fio_planet.radiation
                existing_planet.radius = fio_planet.radius
                existing_planet.sunlight = fio_planet.sunlight
                existing_planet.surface = fio_planet.surface
                existing_planet.temperature = fio_planet.temperature
                existing_planet.fertility = fio_planet.fertility
                existing_planet.has_local_market = fio_planet.has_local_market
                existing_planet.has_chamber_of_commerce = fio_planet.has_chamber_of_commerce
                existing_planet.has_warehouse = fio_planet.has_warehouse
                existing_planet.has_administration_center = fio_planet.has_administration_center
                existing_planet.has_shipyard = fio_planet.has_shipyard
                existing_planet.faction_code = fio_planet.faction_code
                existing_planet.faction_name = fio_planet.faction_name
                existing_planet.governor_id = fio_planet.governor_id
                existing_planet.governor_user_name = fio_planet.governor_user_name
                existing_planet.governor_corporation_id = fio_planet.governor_corporation_id
                existing_planet.governor_corporation_name = fio_planet.governor_corporation_name
                existing_planet.governor_corporation_code = fio_planet.governor_corporation_code
                existing_planet.currency_name = fio_planet.currency_name
                existing_planet.currency_code = fio_planet.currency_code
                existing_planet.collector_id = fio_planet.collector_id
                existing_planet.collector_name = fio_planet.collector_name
                existing_planet.collector_code = fio_planet.collector_code
                existing_planet.base_local_market_fee = fio_planet.base_local_market_fee
                existing_planet.local_market_fee_factor = fio_planet.local_market_fee_factor
                existing_planet.warehouse_fee = fio_planet.warehouse_fee
                existing_planet.population_id = fio_planet.population_id
                existing_planet.cogc_program_status = fio_planet.cogc_program_status
                existing_planet.planet_tier = fio_planet.planet_tier
                existing_planet.timestamp = fio_planet.timestamp
                self.system_repository.update_planet(existing_planet)

            # Delete existing related data
            self.system_repository.delete_planet_resources(planet)
            self.system_repository.delete_planet_building_requirements(planet)
            self.system_repository.delete_planet_production_fees(planet)
            self.system_repository.delete_planet_cogc_programs(planet)
            self.system_repository.delete_planet_cogc_votes(planet)

            # Create new resources
            for resource in fio_planet.resources:
                planet_resource = PlanetResource(
                    planet_natural_id=planet.natural_id,
                    material_id=resource.material_id,
                    resource_type=resource.resource_type,
                    factor=resource.factor,
                )
                self.system_repository.create_planet_resource(planet_resource)

            # Create new building requirements
            for requirement in fio_planet.build_requirements:
                planet_requirement = PlanetBuildingRequirement(
                    planet_natural_id=planet.natural_id,
                    item_symbol=requirement.material_id,
                    amount=requirement.material_amount,
                    weight=requirement.material_weight,
                    volume=requirement.material_volume,
                )
                self.system_repository.create_planet_building_requirement(planet_requirement)

            # Create new production fees
            for fee in fio_planet.production_fees:
                planet_fee = PlanetProductionFee(
                    planet_natural_id=planet.natural_id,
                    category=fee.category,
                    workforce_level=fee.workforce_level,
                    fee_amount=fee.fee_amount,
                    fee_currency=fee.fee_currency,
                )
                self.system_repository.create_planet_production_fee(planet_fee)

            # Create new COGC programs
            for program in fio_planet.cogc_programs:
                cogc_program = COGCProgram(
                    planet_natural_id=planet.natural_id,
                    program_type=program.program_type,
                    start_epoch_ms=program.start_epoch_ms,
                    end_epoch_ms=program.end_epoch_ms,
                )
                self.system_repository.create_cogc_program(cogc_program)

            # Create new COGC votes
            for vote in fio_planet.cogc_votes:
                cogc_vote = COGCVote(
                    planet_natural_id=planet.natural_id,
                    company_name=vote.company_name,
                    company_code=vote.company_code,
                    influence=vote.influence,
                    vote_type=vote.vote_type,
                    vote_time_epoch_ms=vote.vote_time_epoch_ms,
                )
                self.system_repository.create_cogc_vote(cogc_vote)
