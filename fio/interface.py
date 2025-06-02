from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .models import (
    FIOMaterial,
    FIOBuilding,
    FIOPrice,
    FIORecipe,
    FIOPlanet,
    FIOPlanetFull,
    FIOSystem,
    FIOWorkforceNeeds,
    FIOComexExchange,
    FIOSite,
    FIOStorage,
    FIOWarehouse,
    FIOLocalMarketAds,
)


class FIOClientInterface(ABC):
    """Interface for FIO API client operations."""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> None:
        """Authenticate with the FIO API."""
        pass

    @abstractmethod
    def get_recipes(self) -> List[FIORecipe]:
        """Get all recipes from the FIO API."""
        pass

    @abstractmethod
    def get_prices(self) -> List[FIOPrice]:
        """Get all prices from the FIO API."""
        pass

    @abstractmethod
    def get_all_materials(self) -> List[FIOMaterial]:
        """Get all materials from the FIO API."""
        pass

    @abstractmethod
    def get_buildings(self) -> List[FIOBuilding]:
        """Get all buildings from the FIO API."""
        pass

    @abstractmethod
    def get_planets(self) -> List[FIOPlanet]:
        """Get all planets from the FIO API."""
        pass

    @abstractmethod
    def get_planets_full(self) -> List[FIOPlanetFull]:
        """Get full information for all planets from the FIO API."""
        pass

    @abstractmethod
    def get_systems(self) -> List[FIOSystem]:
        """Get all systems from the FIO API."""
        pass

    @abstractmethod
    def get_workforce_needs(self) -> List[FIOWorkforceNeeds]:
        """Get all workforce needs from the FIO API."""
        pass

    @abstractmethod
    def get_comex_exchanges(self) -> List[FIOComexExchange]:
        """Get all commodity exchanges from the FIO API."""
        pass

    @abstractmethod
    def get_sites(self, username: str) -> List[FIOSite]:
        """Get all sites for a user from the FIO API."""
        pass

    @abstractmethod
    def get_storage(self, username: str) -> List[FIOStorage]:
        """Get all storage for a user from the FIO API."""
        pass

    @abstractmethod
    def get_warehouses(self, username: str) -> List[FIOWarehouse]:
        """Get all warehouses for a user from the FIO API."""
        pass

    @abstractmethod
    def get_localmarket_ads(self, planet: str) -> FIOLocalMarketAds:
        """Get local market ads for a specific planet from the FIO API."""
        pass
