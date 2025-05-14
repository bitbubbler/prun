import math
from datetime import datetime
from typing import List, Optional, Union

from sqlmodel import SQLModel, Field, Relationship


# =========================================================
#
# Database models are used to represent data in the database.
# They take a similar shape to the fio data from the fio module/api.
#
# =========================================================


# Database Models
class Building(SQLModel, table=True):
    """Database model for buildings in Prosperous Universe."""

    __tablename__ = "buildings"

    symbol: str = Field(primary_key=True)
    name: str
    expertise: str | None = None
    pioneers: int = Field(default=0)
    settlers: int = Field(default=0)
    technicians: int = Field(default=0)
    engineers: int = Field(default=0)
    scientists: int = Field(default=0)
    area_cost: int

    # Relationships
    recipes: list["Recipe"] = Relationship(back_populates="building")
    building_costs: list["BuildingCost"] = Relationship(back_populates="building")


class BuildingCost(SQLModel, table=True):
    """Database model for building construction costs."""

    __tablename__ = "building_costs"

    id: int = Field(default=None, primary_key=True)
    building_symbol: str = Field(foreign_key="buildings.symbol")
    item_symbol: str = Field(foreign_key="items.symbol")
    amount: int

    # Relationships
    building: "Building" = Relationship(back_populates="building_costs")
    item: "Item" = Relationship(back_populates="building_costs")

    def reclaimable_amount(self, days_since_last_repair: int) -> float:
        """Get the reclaimable cost of the building."""
        # https://pct.fnar.net/building-degradation/index.html#repair-costs-and-reclaimables
        return math.floor(
            self.amount * ((180 - min(days_since_last_repair, 180)) / 180)
        )

    def repair_amount(self, days_since_last_repair: int) -> float:
        """Get the repair cost of the building."""
        # https://pct.fnar.net/building-degradation/index.html#repair-costs-and-reclaimables
        return self.amount - self.reclaimable_amount(days_since_last_repair)


class COGCProgram(SQLModel, table=True):
    """Database model for COGC programs."""

    __tablename__ = "cogc_programs"

    id: int = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    program_type: str | None = None
    start_epoch_ms: datetime
    end_epoch_ms: datetime

    # Relationships
    planet: "Planet" = Relationship(back_populates="cogc_programs")


class COGCVote(SQLModel, table=True):
    """Database model for COGC votes."""

    __tablename__ = "cogc_votes"

    id: int = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    company_name: str
    company_code: str | None = None
    influence: float
    vote_type: str
    vote_time_epoch_ms: datetime

    # Relationships
    planet: "Planet" = Relationship(back_populates="cogc_votes")


class Exchange(SQLModel, table=True):
    """Database model for commodity exchanges."""

    __tablename__ = "exchanges"

    comex_exchange_id: str = Field(primary_key=True)
    exchange_name: str
    exchange_code: str
    exchange_operator_id: str | None = None
    exchange_operator_code: str | None = None
    exchange_operator_name: str | None = None
    currency_numeric_code: int
    currency_code: str
    currency_name: str
    currency_decimals: int
    location_id: str
    location_name: str
    location_natural_id: str

    # Relationships
    prices: list["ExchangePrice"] = Relationship(back_populates="exchange")


class ExchangePrice(SQLModel, table=True):
    """Database model for exchange prices."""

    __tablename__ = "exchange_prices"

    id: int = Field(default=None, primary_key=True)
    item_symbol: str = Field(foreign_key="items.symbol")
    exchange_code: str = Field(foreign_key="exchanges.exchange_code")
    timestamp: datetime = Field()

    # Market maker prices
    mm_buy: float | None = Field(default=None)
    mm_sell: float | None = Field(default=None)

    # Exchange data
    average_price: float = Field(default=None)

    # Ask data
    ask_amount: int | None = Field(default=None)
    ask_price: float | None = Field(default=None)
    ask_available: int | None = Field(default=None)

    # Bid data
    bid_amount: int | None = Field(default=None)
    bid_price: float | None = Field(default=None)
    bid_available: int | None = Field(default=None)

    # Relationships
    item: "Item" = Relationship(back_populates="prices")
    exchange: "Exchange" = Relationship(back_populates="prices")


class Item(SQLModel, table=True):
    """Database model for items in Prosperous Universe."""

    __tablename__ = "items"

    material_id: str = Field(index=True)
    symbol: str = Field(primary_key=True)
    name: str
    category: str
    weight: float
    volume: float

    # Relationships
    prices: list[ExchangePrice] = Relationship(back_populates="item")
    recipe_inputs: list["RecipeInput"] = Relationship(back_populates="item")
    recipe_outputs: list["RecipeOutput"] = Relationship(back_populates="item")
    building_costs: list[BuildingCost] = Relationship(back_populates="item")
    workforce_needs: list["WorkforceNeed"] = Relationship(back_populates="item")


class Planet(SQLModel, table=True):
    """Database model for planets in Prosperous Universe."""

    __tablename__ = "planets"

    natural_id: str = Field(primary_key=True)
    name: str
    system_id: str = Field(foreign_key="systems.system_id")
    planet_id: str
    gravity: float
    magnetic_field: float
    mass: float
    mass_earth: float
    orbit_semi_major_axis: int
    orbit_eccentricity: float
    orbit_inclination: float
    orbit_right_ascension: int
    orbit_periapsis: int
    orbit_index: int
    pressure: float
    radiation: float
    radius: float
    sunlight: float
    surface: bool
    temperature: float
    fertility: float
    has_local_market: bool
    has_chamber_of_commerce: bool
    has_warehouse: bool
    has_administration_center: bool
    has_shipyard: bool
    faction_code: str | None = None
    faction_name: str | None = None
    governor_id: str | None = None
    governor_user_name: str | None = None
    governor_corporation_id: str | None = None
    governor_corporation_name: str | None = None
    governor_corporation_code: str | None = None
    currency_name: str | None = None
    currency_code: str | None = None
    collector_id: str | None = None
    collector_name: str | None = None
    collector_code: str | None = None
    base_local_market_fee: int
    local_market_fee_factor: int
    warehouse_fee: int
    population_id: str | None = None
    cogc_program_status: str | None = None
    planet_tier: int
    timestamp: datetime

    # Relationships
    system: "System" = Relationship(back_populates="planets")
    site: "Site" = Relationship(back_populates="planet")
    resources: list["PlanetResource"] = Relationship(back_populates="planet")
    building_requirements: list["PlanetBuildingRequirement"] = Relationship(
        back_populates="planet"
    )
    production_fees: list["PlanetProductionFee"] = Relationship(back_populates="planet")
    cogc_programs: list["COGCProgram"] = Relationship(back_populates="planet")
    cogc_votes: list["COGCVote"] = Relationship(back_populates="planet")


class PlanetBuildingRequirement(SQLModel, table=True):
    """Database model for planet building requirements."""

    __tablename__ = "planet_building_requirements"

    id: int = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    item_symbol: str = Field(foreign_key="items.symbol")
    amount: int
    weight: float
    volume: float

    # Relationships
    planet: "Planet" = Relationship(back_populates="building_requirements")
    item: "Item" = Relationship()


class PlanetProductionFee(SQLModel, table=True):
    """Database model for planet production fees."""

    __tablename__ = "planet_production_fees"

    id: int = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    category: str
    workforce_level: str
    fee_amount: int
    fee_currency: str | None = None

    # Relationships
    planet: "Planet" = Relationship(back_populates="production_fees")


class PlanetResource(SQLModel, table=True):
    """Database model for planet resources."""

    __tablename__ = "planet_resources"

    id: int = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    material_id: str = Field(foreign_key="items.material_id")
    resource_type: str
    factor: float

    # Relationships
    planet: "Planet" = Relationship(back_populates="resources")
    item: "Item" = Relationship()


class Recipe(SQLModel, table=True):
    """Database model for recipes in Prosperous Universe."""

    __tablename__ = "recipes"

    symbol: str = Field(primary_key=True)
    building_symbol: str = Field(foreign_key="buildings.symbol")
    time_ms: int

    # Relationships
    inputs: list["RecipeInput"] = Relationship(back_populates="recipe")
    outputs: list["RecipeOutput"] = Relationship(back_populates="recipe")
    building: "Building" = Relationship(back_populates="recipes")

    @property
    def is_resource_extraction_recipe(self) -> bool:
        """Check if the recipe is a resource extraction recipe."""
        return self.building_symbol in ["COL", "RIG", "EXT"]

    @property
    def hours_decimal(self) -> float:
        """Get the recipe time_ms in hours, as a float."""
        return self.time_ms / 3600000.0

    @property
    def percent_of_day(self) -> float:
        """Get the recipe time_ms as a percentage of a day (31.2 hours / 24 hours). with 2 decimal places."""
        return round(self.hours_decimal / 24, 2)


class RecipeInput(SQLModel, table=True):
    """Database model for recipe inputs."""

    __tablename__ = "recipe_inputs"

    id: int = Field(default=None, primary_key=True)
    recipe_symbol: str = Field(foreign_key="recipes.symbol")
    item_symbol: str = Field(foreign_key="items.symbol")
    quantity: int

    # Relationships
    recipe: "Recipe" = Relationship(back_populates="inputs")
    item: "Item" = Relationship(back_populates="recipe_inputs")


class RecipeOutput(SQLModel, table=True):
    """Database model for recipe outputs."""

    __tablename__ = "recipe_outputs"

    id: int = Field(default=None, primary_key=True)
    recipe_symbol: str = Field(foreign_key="recipes.symbol")
    item_symbol: str = Field(foreign_key="items.symbol")
    quantity: int

    # Relationships
    recipe: "Recipe" = Relationship(back_populates="outputs")
    item: "Item" = Relationship(back_populates="recipe_outputs")


class Site(SQLModel, table=True):
    """Database model for sites in Prosperous Universe."""

    __tablename__ = "sites"

    site_id: str = Field(primary_key=True)
    invested_permits: int
    maximum_permits: int
    planet_natural_id: str = Field(foreign_key="planets.natural_id")

    # Relationships
    buildings: list["SiteBuilding"] = Relationship(back_populates="site")
    planet: "Planet" = Relationship(back_populates="site")
    storages: list["Storage"] = Relationship(back_populates="site")


class SiteBuilding(SQLModel, table=True):
    """Database model for buildings on a site."""

    __tablename__ = "site_buildings"

    site_building_id: str = Field(primary_key=True)
    building_created: datetime
    building_last_repair: Optional[datetime] = None
    condition: float
    site_id: str = Field(foreign_key="sites.site_id")
    building_symbol: str = Field(foreign_key="buildings.symbol")

    # Relationships
    site: "Site" = Relationship(back_populates="buildings")
    materials: list["SiteBuildingMaterial"] = Relationship(
        back_populates="site_building"
    )
    building: "Building" = Relationship()


class SiteBuildingMaterial(SQLModel, table=True):
    """Database model for materials associated with site buildings."""

    __tablename__ = "site_building_materials"

    id: int = Field(primary_key=True)
    amount: int
    site_building_id: str = Field(foreign_key="site_buildings.site_building_id")
    material_type: str
    item_symbol: str = Field(foreign_key="items.symbol")

    # Relationships
    site_building: "SiteBuilding" = Relationship(back_populates="materials")
    item: "Item" = Relationship()


class Storage(SQLModel, table=True):
    """Database model for storage facilities."""

    __tablename__ = "storages"

    storage_id: str = Field(primary_key=True, max_length=32)
    addressable_id: str = Field(max_length=32)
    name: str | None = None
    type: str
    weight_capacity: int
    volume_capacity: int
    site_id: str | None = Field(default=None, foreign_key="sites.site_id")
    warehouse_id: str | None = Field(
        default=None, foreign_key="warehouses.warehouse_id"
    )

    # Relationships
    stored_items: list["StorageItem"] = Relationship(back_populates="storage")
    site: Union["Site", None] = Relationship(back_populates="storages")
    warehouse: Union["Warehouse", None] = Relationship(back_populates="storage")


class StorageItem(SQLModel, table=True):
    """Database model for items stored in storage facilities."""

    __tablename__ = "storage_items"

    id: int = Field(default=None, primary_key=True)
    storage_id: str = Field(foreign_key="storages.storage_id")
    item_symbol: str | None = Field(foreign_key="items.symbol")
    amount: int
    type: str  # eg "BLOCKED"

    # Relationships
    storage: "Storage" = Relationship(back_populates="stored_items")
    item: "Item" = Relationship()


class System(SQLModel, table=True):
    """Database model for systems in Prosperous Universe."""

    __tablename__ = "systems"

    system_id: str = Field(primary_key=True)
    name: str
    natural_id: str
    type: str
    position_x: float
    position_y: float
    position_z: float
    sector_id: str
    sub_sector_id: str

    # Relationships
    connections: list["SystemConnection"] = Relationship(
        back_populates="system",
        sa_relationship_kwargs={
            "primaryjoin": "System.system_id == SystemConnection.system_id"
        },
    )
    connected_to: list["SystemConnection"] = Relationship(
        back_populates="connecting_system",
        sa_relationship_kwargs={
            "primaryjoin": "System.system_id == SystemConnection.connecting_id"
        },
    )
    planets: list["Planet"] = Relationship(back_populates="system")


class SystemConnection(SQLModel, table=True):
    """System connection model."""

    system_connection_id: str = Field(primary_key=True)
    system_id: str = Field(foreign_key="systems.system_id")
    connecting_id: str = Field(foreign_key="systems.system_id")

    # Relationships
    system: "System" = Relationship(
        back_populates="connections",
        sa_relationship_kwargs={
            "primaryjoin": "SystemConnection.system_id == System.system_id"
        },
    )
    connecting_system: "System" = Relationship(
        back_populates="connected_to",
        sa_relationship_kwargs={
            "primaryjoin": "SystemConnection.connecting_id == System.system_id"
        },
    )


class Warehouse(SQLModel, table=True):
    """Database model for warehouses."""

    __tablename__ = "warehouses"

    warehouse_id: str = Field(primary_key=True)
    units: int
    weight_capacity: float
    volume_capacity: float
    next_payment_timestamp_epoch_ms: int
    fee_amount: float
    fee_currency: str
    fee_collector_id: str | None = None
    fee_collector_name: str | None = None
    fee_collector_code: str | None = None
    location_name: str
    location_natural_id: str

    # Relationships
    storage: "Storage" = Relationship(back_populates="warehouse")


class WorkforceNeed(SQLModel, table=True):
    """Database model for workforce needs."""

    __tablename__ = "workforce_needs"

    id: int = Field(default=None, primary_key=True)
    workforce_type: str
    item_symbol: str = Field(foreign_key="items.symbol")
    amount_per_100_workers_per_day: float

    # Relationships
    item: "Item" = Relationship(back_populates="workforce_needs")
