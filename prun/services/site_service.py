import logging

from pydantic import BaseModel
from typing import List, Optional

from fio import FIOClientInterface
from prun.interface import SiteRepositoryInterface
from prun.models import Site, SiteBuilding, SiteBuildingMaterial

logger = logging.getLogger(__name__)


class SiteService:
    """Service for site-related operations."""

    def __init__(
        self, fio_client: FIOClientInterface, site_repository: SiteRepositoryInterface
    ):
        """Initialize the service.

        Args:
            repository: Repository for database operations
        """
        self.fio_client = fio_client
        self.site_repository = site_repository

    def sync_sites(self, character_id: str) -> None:
        """Sync sites from the FIO API to the database.

        Args:
            fio_client: FIO API client
            character_id: Character ID to sync sites for

        Raises:
            Exception: If there's an error syncing sites
        """
        try:
            sites = self.fio_client.get_sites(character_id)

            # Get existing sites for comparison
            existing_sites = {
                site.site_id: site for site in self.site_repository.get_all_sites()
            }

            for fio_site in sites:
                site: Site
                # Update or create site
                if fio_site.site_id in existing_sites:
                    # Update existing site
                    site = existing_sites[fio_site.site_id]
                    site.invested_permits = fio_site.invested_permits
                    site.maximum_permits = fio_site.maximum_permits
                    site.planet_natural_id = fio_site.planet_identifier
                else:
                    site = Site.model_validate(
                        {
                            "site_id": fio_site.site_id,
                            "invested_permits": fio_site.invested_permits,
                            "maximum_permits": fio_site.maximum_permits,
                            "planet_natural_id": fio_site.planet_identifier,
                        }
                    )
                    self.site_repository.create_site(site)

                # Delete existing buildings and materials for this site
                self.site_repository.delete_site_buildings(site)

                # Create new buildings and materials
                for fio_building in site.buildings:
                    building = SiteBuilding.model_validate(
                        {
                            "site_building_id": fio_building.site_building_id,
                            "building_created": fio_building.building_created,
                            "building_last_repair": fio_building.building_last_repair,
                            "condition": fio_building.condition,
                            "site_id": site.site_id,
                            "building_symbol": fio_building.building_symbol,
                            "materials": [
                                SiteBuildingMaterial.model_validate(
                                    {
                                        "amount": fio_material.amount,
                                        "material_type": fio_material.material_type,
                                        "item_symbol": fio_material.item_symbol,
                                    }
                                )
                                for fio_material in fio_building.materials
                            ],
                        }
                    )
                    self.site_repository.create_site_building(building)

        except Exception as e:
            logger.error(f"Error syncing sites for character {character_id}: {str(e)}")
            raise
