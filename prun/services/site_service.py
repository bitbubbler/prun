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
