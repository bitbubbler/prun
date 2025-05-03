from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from prun.models import (
    Building,
    ComexExchange,
    ExchangePrice,
    Item,
    Planet,
    Recipe,
    RecipeInput,
    Site,
    SiteBuilding,
    SiteBuildingMaterial,
    Storage,
    StorageItem,
    System,
    Warehouse,
    WorkforceNeed,
    PlanetResource,
    PlanetBuildingRequirement,
    PlanetProductionFee,
    COGCProgram,
    COGCVote,
)


class BuildingRepositoryInterface(ABC):
    """Interface for building-related operations."""

    @abstractmethod
    def get_building(self, symbol: str) -> Optional[Building]:
        """Get a building by symbol."""
        pass

    @abstractmethod
    def create_building(self, building: Building) -> None:
        """Create a new building."""
        pass


class ItemRepositoryInterface(ABC):
    """Interface for item-related operations."""

    @abstractmethod
    def get_item(self, symbol: str) -> Optional[Item]:
        """Get an item by symbol."""
        pass

    @abstractmethod
    def create_item(self, item: Item) -> None:
        """Create a new item."""
        pass


class ExchangeRepositoryInterface(ABC):
    """Interface for exchange and price-related operations."""

    @abstractmethod
    def get_all_comex_exchanges(self) -> List[ComexExchange]:
        """Get all comex exchanges."""
        pass

    @abstractmethod
    def get_comex_exchange(self, exchange_code: str) -> Optional[ComexExchange]:
        """Get a comex exchange by exchange code."""
        pass

    @abstractmethod
    def get_exchange_price(
        self, exchange_code: str, item_symbol: str
    ) -> Optional[ExchangePrice]:
        """Get an exchange price by item symbol and exchange code."""
        pass

    @abstractmethod
    def delete_exchange_prices(self) -> None:
        """Delete all exchange prices."""
        pass

    @abstractmethod
    def create_exchange_price(self, exchange_price: ExchangePrice) -> ExchangePrice:
        """Create a new exchange price."""
        pass

    @abstractmethod
    def create_comex_exchange(self, comex_exchange: ComexExchange) -> ComexExchange:
        """Create a new comex exchange."""
        pass


class RecipeRepositoryInterface(ABC):
    """Interface for recipe-related operations."""

    @abstractmethod
    def get_recipe(self, symbol: str) -> Optional[Recipe]:
        """Get a recipe by symbol."""
        pass

    @abstractmethod
    def create_recipe(self, recipe: Recipe) -> None:
        """Create a new recipe."""
        pass

    @abstractmethod
    def get_recipe_with_prices(
        self, symbol: str
    ) -> tuple[Recipe, List[tuple[RecipeInput, ExchangePrice]]]:
        """Get a recipe with current prices for its inputs."""
        pass

    @abstractmethod
    def get_all_recipes(self) -> List[Recipe]:
        """Get all recipes."""
        pass

    @abstractmethod
    def get_recipes_for_item(self, item_symbol: str) -> List[Recipe]:
        """Get all recipes for an item."""
        pass


class SiteRepositoryInterface(ABC):
    """Interface for site-related operations."""

    @abstractmethod
    def get_all_sites(self) -> List[Site]:
        """Get all sites."""
        pass

    @abstractmethod
    def get_site(self, site_id: str) -> Optional[Site]:
        """Get a site by ID."""
        pass

    @abstractmethod
    def create_site(self, site: Site) -> None:
        """Create a new site."""
        pass

    @abstractmethod
    def delete_site_buildings(self, site: Site) -> None:
        """Delete all buildings for a site."""
        pass

    @abstractmethod
    def create_site_building(self, site_building: SiteBuilding) -> SiteBuilding:
        """Create a new site building."""
        pass

    @abstractmethod
    def create_site_building_material(
        self, site_building_material: SiteBuildingMaterial
    ) -> SiteBuildingMaterial:
        """Create a new site building material."""
        pass

    @abstractmethod
    def get_site_building(self, site_building_id: str) -> Optional[SiteBuilding]:
        """Get a site building by ID."""
        pass

    @abstractmethod
    def delete_site_building_materials(self, site_building: SiteBuilding) -> None:
        """Delete all materials for a site building."""
        pass


class StorageRepositoryInterface(ABC):
    """Interface for storage-related operations."""

    @abstractmethod
    def get_storage(self, storage_id: str) -> Optional[Storage]:
        """Get a storage by ID."""
        pass

    @abstractmethod
    def create_storage(self, storage: Storage) -> None:
        """Create a new storage."""
        pass

    @abstractmethod
    def create_storage_item(self, storage_item: StorageItem) -> None:
        """Create a new storage item."""
        pass

    @abstractmethod
    def delete_storage_items(self, storage: Storage) -> None:
        """Delete all items in a storage."""
        pass

    @abstractmethod
    def get_storage_items_with_prices(self) -> List[tuple[StorageItem, ExchangePrice]]:
        """Get all storage items with their current market prices."""
        pass

    @abstractmethod
    def delete_storage(self) -> None:
        """Delete all storage data."""
        pass


class SystemRepositoryInterface(ABC):
    """Interface for system and planet-related operations."""

    @abstractmethod
    def get_system(self, system_id: str) -> Optional[System]:
        """Get a system by ID."""
        pass

    @abstractmethod
    def get_system_by_natural_id(self, natural_id: str) -> Optional[System]:
        """Get a system by its natural ID."""
        pass

    @abstractmethod
    def create_system(self, system: System) -> None:
        """Create a new system."""
        pass

    @abstractmethod
    def get_planet(self, natural_id: str) -> Optional[Planet]:
        """Get a planet by its natural ID."""
        pass

    @abstractmethod
    def create_planet(self, planet: Planet) -> None:
        """Create a new planet."""
        pass

    @abstractmethod
    def update_planet(self, planet: Planet) -> None:
        """Update an existing planet."""
        pass

    @abstractmethod
    def delete_planet_resources(self, planet: Planet) -> None:
        """Delete all resources for a planet."""
        pass

    @abstractmethod
    def delete_planet_building_requirements(self, planet: Planet) -> None:
        """Delete all building requirements for a planet."""
        pass

    @abstractmethod
    def delete_planet_production_fees(self, planet: Planet) -> None:
        """Delete all production fees for a planet."""
        pass

    @abstractmethod
    def delete_planet_cogc_programs(self, planet: Planet) -> None:
        """Delete all COGC programs for a planet."""
        pass

    @abstractmethod
    def delete_planet_cogc_votes(self, planet: Planet) -> None:
        """Delete all COGC votes for a planet."""
        pass

    @abstractmethod
    def create_planet_resource(self, resource: PlanetResource) -> None:
        """Create a new planet resource."""
        pass

    @abstractmethod
    def create_planet_building_requirement(
        self, requirement: PlanetBuildingRequirement
    ) -> None:
        """Create a new planet building requirement."""
        pass

    @abstractmethod
    def create_planet_production_fee(self, fee: PlanetProductionFee) -> None:
        """Create a new planet production fee."""
        pass

    @abstractmethod
    def create_cogc_program(self, program: COGCProgram) -> None:
        """Create a new COGC program."""
        pass

    @abstractmethod
    def create_cogc_vote(self, vote: COGCVote) -> None:
        """Create a new COGC vote."""
        pass


class WarehouseRepositoryInterface(ABC):
    """Interface for warehouse-related operations."""

    @abstractmethod
    def get_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        """Get a warehouse by ID."""
        pass

    @abstractmethod
    def create_warehouse(self, warehouse: Warehouse) -> None:
        """Create a new warehouse."""
        pass

    @abstractmethod
    def get_all_warehouses(self) -> List[Warehouse]:
        """Get all warehouses."""
        pass


class WorkforceRepositoryInterface(ABC):
    """Interface for workforce-related operations."""

    @abstractmethod
    def get_workforce_needs(
        self, workforce_type: Optional[str] = None
    ) -> List[WorkforceNeed]:
        """Get workforce needs, optionally filtered by workforce type."""
        pass

    @abstractmethod
    def create_workforce_need(self, workforce_need: WorkforceNeed) -> WorkforceNeed:
        """Create a new workforce need."""
        pass

    @abstractmethod
    def delete_workforce_needs(self) -> None:
        """Delete all workforce needs."""
        pass
