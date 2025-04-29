from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from decimal import Decimal


# Database Models
class Item(SQLModel, table=True):
    """Database model for items in Prosperous Universe."""

    __tablename__ = "items"

    symbol: str = Field(primary_key=True)
    name: str
    category: str
    weight: float
    volume: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}
    )

    # Relationships
    prices: List["ExchangePrice"] = Relationship(back_populates="item")
    recipe_inputs: List["RecipeInput"] = Relationship(back_populates="item")
    recipe_outputs: List["RecipeOutput"] = Relationship(back_populates="item")
    building_costs: List["BuildingCost"] = Relationship(back_populates="item")
    workforce_needs: List["WorkforceNeed"] = Relationship(back_populates="item")


class ExchangePrice(SQLModel, table=True):
    """Database model for exchange prices."""

    __tablename__ = "exchange_prices"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_symbol: str = Field(foreign_key="items.symbol")
    exchange_code: str = Field(foreign_key="exchanges.exchange_code")
    timestamp: datetime = Field()

    # Market maker prices
    mm_buy: Optional[float] = None
    mm_sell: Optional[float] = None

    # Exchange data
    average_price: float

    # Ask data
    ask_amount: Optional[float] = None
    ask_price: Optional[float] = None
    ask_available: Optional[float] = None

    # Bid data
    bid_amount: Optional[float] = None
    bid_price: Optional[float] = None
    bid_available: Optional[float] = None

    # Relationships
    item: Item = Relationship(back_populates="prices")
    exchange: "ComexExchange" = Relationship(back_populates="prices")

    @property
    def buy_price(self) -> float:
        """Get the ask price."""
        return self.ask_price or 0

    @property
    def sell_price(self) -> float:
        """Get the bid price."""
        return self.bid_price or 0


class RecipeInput(SQLModel, table=True):
    """Database model for recipe inputs."""

    __tablename__ = "recipe_inputs"

    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_symbol: str = Field(foreign_key="recipes.symbol")
    item_symbol: str = Field(foreign_key="items.symbol")
    quantity: int

    # Relationships
    recipe: "Recipe" = Relationship(back_populates="inputs")
    item: Item = Relationship(back_populates="recipe_inputs")


class RecipeOutput(SQLModel, table=True):
    """Database model for recipe outputs."""

    __tablename__ = "recipe_outputs"

    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_symbol: str = Field(foreign_key="recipes.symbol")
    item_symbol: str = Field(foreign_key="items.symbol")
    quantity: int

    # Relationships
    recipe: "Recipe" = Relationship(back_populates="outputs")
    item: Item = Relationship(back_populates="recipe_outputs")


class Recipe(SQLModel, table=True):
    """Database model for recipes in Prosperous Universe."""

    __tablename__ = "recipes"

    symbol: str = Field(primary_key=True)
    building_symbol: str = Field(foreign_key="buildings.symbol")
    time_ms: int

    # Relationships
    inputs: List[RecipeInput] = Relationship(back_populates="recipe")
    outputs: List[RecipeOutput] = Relationship(back_populates="recipe")
    building: "Building" = Relationship(back_populates="recipes")


class Building(SQLModel, table=True):
    """Database model for buildings in Prosperous Universe."""

    __tablename__ = "buildings"

    symbol: str = Field(primary_key=True)
    name: str
    expertise: Optional[str] = None
    pioneers: int = Field(default=0)
    settlers: int = Field(default=0)
    technicians: int = Field(default=0)
    engineers: int = Field(default=0)
    scientists: int = Field(default=0)
    area_cost: int

    # Relationships
    recipes: List[Recipe] = Relationship(back_populates="building")
    building_costs: List["BuildingCost"] = Relationship(back_populates="building")


class BuildingCost(SQLModel, table=True):
    """Database model for building construction costs."""

    __tablename__ = "building_costs"

    id: Optional[int] = Field(default=None, primary_key=True)
    building_symbol: str = Field(foreign_key="buildings.symbol")
    item_symbol: str = Field(foreign_key="items.symbol")
    amount: int

    # Relationships
    building: Building = Relationship(back_populates="building_costs")
    item: Item = Relationship(back_populates="building_costs")


class Planet(SQLModel, table=True):
    """Database model for planets in Prosperous Universe."""

    __tablename__ = "planets"

    natural_id: str = Field(primary_key=True)
    name: str
    system_id: str = Field(foreign_key="systems.system_id")

    # Relationships
    system: "System" = Relationship(back_populates="planets")
    site: "Site" = Relationship(back_populates="planet")


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
    connections: List[SystemConnection] = Relationship(
        back_populates="system",
        sa_relationship_kwargs={
            "primaryjoin": "System.system_id == SystemConnection.system_id"
        },
    )
    connected_to: List[SystemConnection] = Relationship(
        back_populates="connecting_system",
        sa_relationship_kwargs={
            "primaryjoin": "System.system_id == SystemConnection.connecting_id"
        },
    )
    planets: List[Planet] = Relationship(back_populates="system")


class WorkforceNeed(SQLModel, table=True):
    """Database model for workforce needs."""

    __tablename__ = "workforce_needs"

    id: Optional[int] = Field(default=None, primary_key=True)
    workforce_type: str
    item_symbol: str = Field(foreign_key="items.symbol")
    amount: float

    # Relationships
    item: Item = Relationship(back_populates="workforce_needs")

    @property
    def per_worker_per_day(self) -> float:
        """Get the amount of the item needed per worker per day. FIO gives us the amount per 100 workers per day."""
        return self.amount / 100


class ComexExchange(SQLModel, table=True):
    """Database model for commodity exchanges."""

    __tablename__ = "exchanges"

    comex_exchange_id: str = Field(primary_key=True)
    exchange_name: str
    exchange_code: str
    exchange_operator_id: Optional[str] = None
    exchange_operator_code: Optional[str] = None
    exchange_operator_name: Optional[str] = None
    currency_numeric_code: int
    currency_code: str
    currency_name: str
    currency_decimals: int
    location_id: str
    location_name: str
    location_natural_id: str

    # Relationships
    prices: List[ExchangePrice] = Relationship(back_populates="exchange")


class Storage(SQLModel, table=True):
    """Database model for storage facilities."""

    __tablename__ = "storages"

    storage_id: str = Field(primary_key=True, max_length=32)
    addressable_id: str = Field(max_length=32)
    name: Optional[str] = None
    type: str
    weight_capacity: int
    volume_capacity: int
    site_id: Optional[str] = Field(default=None, foreign_key="sites.site_id")
    warehouse_id: Optional[str] = Field(
        default=None, foreign_key="warehouses.warehouse_id"
    )

    # Relationships
    stored_items: List["StorageItem"] = Relationship(back_populates="storage")
    site: "Site" = Relationship(back_populates="storages")
    warehouse: "Warehouse" = Relationship(back_populates="storage")


class StorageItem(SQLModel, table=True):
    """Database model for items stored in storage facilities."""

    __tablename__ = "storage_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    storage_id: str = Field(foreign_key="storages.storage_id")
    item_symbol: str | None = Field(foreign_key="items.symbol")
    amount: int
    type: str  # eg "BLOCKED"

    # Relationships
    storage: Storage = Relationship(back_populates="stored_items")
    item: Item = Relationship()

    @property
    def total_weight(self) -> float:
        """Calculate total weight of stored items."""
        return self.amount * self.item.weight if self.item else 0

    @property
    def total_volume(self) -> float:
        """Calculate total volume of stored items."""
        return self.amount * self.item.volume if self.item else 0


class SiteBuildingMaterial(SQLModel, table=True):
    """Database model for materials associated with site buildings."""

    __tablename__ = "site_building_materials"

    id: Optional[int] = Field(default=None, primary_key=True)
    amount: int
    site_building_id: str = Field(foreign_key="site_buildings.site_building_id")
    material_type: str
    item_symbol: str = Field(foreign_key="items.symbol")

    # Relationships
    site_building: "SiteBuilding" = Relationship(back_populates="materials")
    item: Item = Relationship()


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
    materials: List[SiteBuildingMaterial] = Relationship(back_populates="site_building")
    building: Building = Relationship()


class Site(SQLModel, table=True):
    """Database model for sites in Prosperous Universe."""

    __tablename__ = "sites"

    site_id: str = Field(primary_key=True)
    invested_permits: int
    maximum_permits: int
    planet_natural_id: str = Field(foreign_key="planets.natural_id")

    # Relationships
    buildings: List[SiteBuilding] = Relationship(back_populates="site")
    planet: Planet = Relationship(back_populates="site")
    storages: List[Storage] = Relationship(back_populates="site")


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
    fee_collector_id: Optional[str] = None
    fee_collector_name: Optional[str] = None
    fee_collector_code: Optional[str] = None
    location_name: str
    location_natural_id: str

    # Relationships
    storage: Storage = Relationship(back_populates="warehouse")


class Transaction(SQLModel, table=True):
    """Model for tracking credit transactions."""

    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    amount: float
    category: str
    ref: str
    notes: Optional[str] = None


class Commitment(SQLModel, table=True):
    """Model for future commitments."""

    __tablename__ = "commitments"

    id: Optional[int] = Field(default=None, primary_key=True)
    eta: datetime
    amount: float
    category: str
    ref: str
    notes: Optional[str] = None
    status: str = Field(default="PENDING")
    variance: Optional[float] = None
    actual_ts: Optional[datetime] = None
    predicted_amount: Optional[float] = None


class ReconciliationEvent(SQLModel, table=True):
    """Model for tracking reconciliation events."""

    __tablename__ = "reconciliation_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    commitment_id: int = Field(foreign_key="commitments.id")
    event_type: str
    variance: Optional[float] = None
    notes: Optional[str] = None

    # Relationships
    commitment: Commitment = Relationship()


class RawEvent(SQLModel, table=True):
    """Model for storing raw events for event sourcing."""

    __tablename__ = "raw_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    data: str
    processed: bool = Field(default=False)
    processing_ts: Optional[datetime] = None
    processing_error: Optional[str] = None


class WalletSnapshot(SQLModel, table=True):
    """Model for tracking historical wallet balances."""

    __tablename__ = "wallet_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    balance: float
    notes: Optional[str] = None


class ProjectionBucket(SQLModel, table=True):
    """Projection bucket for cash flow analysis."""

    __tablename__ = "projection_buckets"

    id: Optional[int] = Field(default=None, primary_key=True)
    start_ts: datetime
    end_ts: datetime
    inflow: float
    outflow: float
    balance_start: float
    balance_end: float
    is_negative: bool

    @property
    def net_flow(self) -> float:
        """Calculate net flow (inflow - outflow)."""
        return self.inflow - self.outflow

    @property
    def balance_change(self) -> float:
        """Calculate change in balance (end - start)."""
        return self.balance_end - self.balance_start


# Pydantic Models
class RecipeInputModel(BaseModel):
    """Pydantic model for recipe inputs."""

    item_symbol: str
    quantity: float


class RecipeOutputModel(BaseModel):
    """Pydantic model for recipe outputs."""

    item_symbol: str
    quantity: float
    is_target: bool = False


class RecipeModel(BaseModel):
    """Pydantic model for recipes."""

    symbol: str
    building_symbol: str
    time_ms: int
    inputs: List[RecipeInputModel]
    outputs: List[RecipeOutputModel]
    workforce_cost: Optional[float] = None
    total_cost: Optional[float] = None


class RecipeCostModel(BaseModel):
    """Pydantic model for recipe costs."""

    item: str
    quantity: float
    price: float
    total: float


class WorkforceNeedModel(BaseModel):
    """Pydantic model for workforce needs."""

    type: str
    workers: int
    needs: List[Dict[str, Any]]
