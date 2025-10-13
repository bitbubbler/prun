import logging
from typing import List
from fio import FIOClientInterface
from prun.models.db_models import LocalMarketAd
from prun.repository import LocalMarketAdRepository
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalMarketService:
    """Service for syncing local market ads."""

    def __init__(
        self,
        fio_client: FIOClientInterface,
        localmarket_repository: LocalMarketAdRepository,
    ):
        self.fio_client = fio_client
        self.localmarket_repository = localmarket_repository
