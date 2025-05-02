import math
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship


# Database Models
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
    mm_buy: Optional[float] = Field(default=None)
    mm_sell: Optional[float] = Field(default=None)

    # Exchange data
    average_price: float = Field(default=None)

    # Ask data
    ask_amount: Optional[int] = None
    ask_price: Optional[float] = None
    ask_available: Optional[int] = None

    # Bid data
    bid_amount: Optional[int] = None
    bid_price: Optional[float] = None
    bid_available: Optional[int] = None

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

    @property
    def is_resource_extraction_recipe(self) -> bool:
        """Check if the recipe is a resource extraction recipe."""
        return self.building_symbol in ["COL", "RIG", "EXT"]

    @property
    def hours_decimal(self) -> float:
        """Get the recipe time_ms in hours, as a float."""
        return self.time_ms / 3600000.0

    @staticmethod
    def extraction_recipe_from(
        recipe: "Recipe", planet_resource: "PlanetResource"
    ) -> "Recipe":
        """Create an extraction recipe from a normal recipe."""

        if not recipe.is_resource_extraction_recipe:
            raise ValueError("Recipe is not a resource extraction recipe")

        daily_extraction = (
            round(planet_resource.factor * 100 * 0.7, 1)
            if recipe.building_symbol in ["RIG", "EXT"]
            else round(planet_resource.factor * 100 * 0.6, 1)
        )

        fractional_units_per_run = daily_extraction / (24 / recipe.hours_decimal)

        remainder_units_per_run = (
            math.ceil(fractional_units_per_run) - fractional_units_per_run
        )

        extraction_units_per_run = math.ceil(fractional_units_per_run)

        extraction_time_hours_decimal = recipe.hours_decimal + (
            recipe.hours_decimal * (remainder_units_per_run / fractional_units_per_run)
        )

        return Recipe(
            symbol=recipe.symbol,
            building_symbol=recipe.building_symbol,
            time_ms=int(extraction_time_hours_decimal * 3600000),
            inputs=[],
            outputs=[
                RecipeOutput(
                    item_symbol=planet_resource.item.symbol,
                    quantity=extraction_units_per_run,
                )
            ],
        )


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

    def condition(self, days_since_last_repair: int) -> float:
        """Get the condition of the building."""
        c = 100.87
        # There is speculation that the additional 7 days for C is a bug as it happens inconsistently.
        # c = 107.87
        # https://pct.fnar.net/building-degradation/index.html
        return (
            0.67 / (1 + math.exp((1789 / 25000) * (days_since_last_repair - c))) + 0.33
        )


class PlanetBuilding(BaseModel):
    building: "Building"
    planet: "Planet"
    building_costs: List["BuildingCost"]

    @classmethod
    def planet_building_from(
        cls, building: "Building", planet: "Planet"
    ) -> "PlanetBuilding":
        """Create a building from a planet."""
        building_costs = building.building_costs.copy()
        if planet.surface:
            building_costs.append(
                BuildingCost(
                    item_symbol="MCG",
                    amount=building.area_cost * 4,
                )
            )
        else:
            building_costs.append(
                BuildingCost(
                    item_symbol="AEF",
                    amount=building.area_cost / 3,
                )
            )
        if planet.pressure < 0.25:
            building_costs.append(
                BuildingCost(item_symbol="SEA", amount=building.area_cost)
            )
        elif planet.pressure > 2:
            building_costs.append(BuildingCost(item_symbol="HSE", amount=1))
        if planet.gravity < 0.25:
            building_costs.append(BuildingCost(item_symbol="MGC", amount=1))
        elif planet.gravity > 2.5:
            building_costs.append(BuildingCost(item_symbol="BL", amount=1))
        if planet.temperature < -25:
            building_costs.append(
                BuildingCost(item_symbol="INS", amount=building.area_cost * 10)
            )
        elif planet.temperature > 75:
            building_costs.append(BuildingCost(item_symbol="TSH", amount=1))
        return cls(
            building=building,
            planet=planet,
            building_costs=building_costs,
        )


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
    faction_code: Optional[str] = None
    faction_name: Optional[str] = None
    governor_id: Optional[str] = None
    governor_user_name: Optional[str] = None
    governor_corporation_id: Optional[str] = None
    governor_corporation_name: Optional[str] = None
    governor_corporation_code: Optional[str] = None
    currency_name: Optional[str] = None
    currency_code: Optional[str] = None
    collector_id: Optional[str] = None
    collector_name: Optional[str] = None
    collector_code: Optional[str] = None
    base_local_market_fee: int
    local_market_fee_factor: int
    warehouse_fee: int
    population_id: Optional[str] = None
    cogc_program_status: Optional[str] = None
    planet_tier: int
    timestamp: datetime

    # Relationships
    system: "System" = Relationship(back_populates="planets")
    site: "Site" = Relationship(back_populates="planet")
    resources: List["PlanetResource"] = Relationship(back_populates="planet")
    building_requirements: List["PlanetBuildingRequirement"] = Relationship(
        back_populates="planet"
    )
    production_fees: List["PlanetProductionFee"] = Relationship(back_populates="planet")
    cogc_programs: List["COGCProgram"] = Relationship(back_populates="planet")
    cogc_votes: List["COGCVote"] = Relationship(back_populates="planet")


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


class PlanetResource(SQLModel, table=True):
    """Database model for planet resources."""

    __tablename__ = "planet_resources"

    id: Optional[int] = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    material_id: str = Field(foreign_key="items.material_id")
    resource_type: str
    factor: float

    # Relationships
    planet: Planet = Relationship(back_populates="resources")
    item: Item = Relationship()


class PlanetBuildingRequirement(SQLModel, table=True):
    """Database model for planet building requirements."""

    __tablename__ = "planet_building_requirements"

    id: Optional[int] = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    item_symbol: str = Field(foreign_key="items.symbol")
    amount: int
    weight: float
    volume: float

    # Relationships
    planet: Planet = Relationship(back_populates="building_requirements")
    item: Item = Relationship()


class PlanetProductionFee(SQLModel, table=True):
    """Database model for planet production fees."""

    __tablename__ = "planet_production_fees"

    id: Optional[int] = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    category: str
    workforce_level: str
    fee_amount: int
    fee_currency: Optional[str] = None

    # Relationships
    planet: Planet = Relationship(back_populates="production_fees")


class COGCProgram(SQLModel, table=True):
    """Database model for COGC programs."""

    __tablename__ = "cogc_programs"

    id: Optional[int] = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    program_type: Optional[str] = None
    start_epoch_ms: datetime
    end_epoch_ms: datetime

    # Relationships
    planet: Planet = Relationship(back_populates="cogc_programs")


class COGCVote(SQLModel, table=True):
    """Database model for COGC votes."""

    __tablename__ = "cogc_votes"

    id: Optional[int] = Field(default=None, primary_key=True)
    planet_natural_id: str = Field(foreign_key="planets.natural_id")
    company_name: str
    company_code: Optional[str] = None
    influence: float
    vote_type: str
    vote_time_epoch_ms: datetime

    # Relationships
    planet: Planet = Relationship(back_populates="cogc_votes")
