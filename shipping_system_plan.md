# Prosperous Universe Shipping System - Database Design Plan

## Overview
Design a database-driven system to optimize shipping schedules with a single source of truth, leveraging relationships and foreign keys for data integrity.

## Core Entities and Relationships

### 1. Ships (following existing SQLModel pattern)
```python
class Ship(SQLModel, table=True):
    __tablename__ = "ships"
    
    ship_id: str = Field(primary_key=True)  # maps to ShipId from API
    registration: str  # ship registration (e.g. "AVI-05PNM")
    name: str  # user-defined ship name
    store_id: str  # main cargo storage ID
    stl_fuel_store_id: str  # STL fuel storage ID  
    ftl_fuel_store_id: str  # FTL fuel storage ID
    commissioning_time_epoch_ms: int  # when commissioned
    blueprint_natural_id: str  # ship blueprint reference
    flight_id: str | None = None  # current flight ID if in transit
    acceleration: float  # ship acceleration capability
    thrust: int  # ship thrust
    mass: float  # current total mass
    operating_empty_mass: float  # ship empty mass
    reactor_power: int  # reactor power output
    emitter_power: int  # emitter power
    volume: int  # total cargo volume capacity
    condition: float  # ship condition (0.0 to 1.0)
    last_repair_epoch_ms: int  # last repair timestamp
    location: str  # current location (planet/space)
    stl_fuel_flow_rate: float  # STL fuel consumption rate
    user_name_submitted: str  # owner username
    timestamp: datetime  # last update timestamp
    
    # Relationships
    repair_materials: list["ShipRepairMaterial"] = Relationship(back_populates="ship")
    cargo_storage: "Storage" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Ship.store_id == Storage.storage_id"}
    )
    stl_fuel_storage: "Storage" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Ship.stl_fuel_store_id == Storage.storage_id"}
    )
    ftl_fuel_storage: "Storage" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "Ship.ftl_fuel_store_id == Storage.storage_id"}
    )
```

### 1a. Ship Repair Materials
```python
class ShipRepairMaterial(SQLModel, table=True):
    __tablename__ = "ship_repair_materials"
    
    ship_repair_material_id: str = Field(primary_key=True)
    ship_id: str = Field(foreign_key="ships.ship_id")
    material_id: str = Field(foreign_key="items.material_id")
    material_ticker: str = Field(foreign_key="items.symbol")
    material_name: str
    amount: int
    
    # Relationships  
    ship: "Ship" = Relationship(back_populates="repair_materials")
    item: "Item" = Relationship()
```

### 2. Existing Models Integration

The shipping system leverages existing database models:

**Planets**: Already exists as `Planet` model with comprehensive location data including system relationships and coordinates via `System` model.

**Buildings**: Already exists as `Building` and `SiteBuilding` models - buildings are placed on sites on planets with workforce requirements.

**Items/Materials**: Already exists as `Item` model with `material_id`, `symbol`, `name`, `category`, `weight`, `volume`.

**Storage**: Already exists as `Storage` and `StorageItem` models - tracks material storage on planet sites and warehouses via the site relationship.

**Production**: Already exists as `Recipe`, `RecipeInput`, `RecipeOutput` models with building relationships.

**Production Scheduling**: Handled by existing `QueueItem` model in fly_models.py for production queue management.

### 3. New Shipping-Specific Models Needed

```python
class ShippingRoute(SQLModel, table=True):
    __tablename__ = "shipping_routes"
    
    route_id: str = Field(primary_key=True)
    ship_id: str = Field(foreign_key="ships.ship_id") 
    origin_planet_id: str = Field(foreign_key="planets.natural_id")
    destination_planet_id: str = Field(foreign_key="planets.natural_id")
    departure_time: datetime
    estimated_arrival_time: datetime
    status: str  # "planned", "active", "completed", "cancelled"
    
    # Relationships
    ship: "Ship" = Relationship()
    origin_planet: "Planet" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "ShippingRoute.origin_planet_id == Planet.natural_id"}
    )
    destination_planet: "Planet" = Relationship(
        sa_relationship_kwargs={"primaryjoin": "ShippingRoute.destination_planet_id == Planet.natural_id"}
    )
    cargo_items: list["ShippingCargo"] = Relationship(back_populates="route")
```

```python
class ShippingCargo(SQLModel, table=True):
    __tablename__ = "shipping_cargo"
    
    cargo_id: str = Field(primary_key=True)
    route_id: str = Field(foreign_key="shipping_routes.route_id")
    item_symbol: str = Field(foreign_key="items.symbol")
    quantity: int
    action: str  # "pickup", "dropoff"
    
    # Relationships
    route: "ShippingRoute" = Relationship(back_populates="cargo_items")
    item: "Item" = Relationship()
```

### 4. Computed Demand Forecasting (No Storage)

Instead of storing forecasts, compute them on-demand from existing data:

```python
class DemandForecastService:
    """Service to compute real-time demand forecasts from existing data sources"""
    
    def __init__(self, 
                 storage_service: StorageService,
                 site_service: SiteService,
                 recipe_service: RecipeService,
                 workforce_service: WorkforceService):
        self.storage_service = storage_service
        self.site_service = site_service
        self.recipe_service = recipe_service
        self.workforce_service = workforce_service
    
    def calculate_planet_demand(self, planet_id: str, item_symbol: str) -> PlanetDemand:
        """Calculate current demand for an item on a planet"""
        # Get current storage amount using existing storage service
        current_storage_amount = self.storage_service.get_planet_storage_amount(planet_id, item_symbol)
        
        # Calculate daily consumption from active production queues
        daily_consumption = self._calculate_daily_consumption(planet_id, item_symbol)
        
        # Calculate production rate if planet produces this item
        daily_production = self._calculate_daily_production(planet_id, item_symbol)
        
        # Net burn rate
        net_daily_consumption = daily_consumption - daily_production
        
        # Days until stockout (if consuming more than producing)
        days_until_stockout = current_storage_amount / net_daily_consumption if net_daily_consumption > 0 else float('inf')
        
        return PlanetDemand(
            planet_id=planet_id,
            item_symbol=item_symbol,
            current_storage_amount=current_storage_amount,
            daily_production=daily_production,
            daily_consumption=daily_consumption,
            net_daily_consumption=net_daily_consumption,
            days_until_stockout=days_until_stockout
        )
    
    def _calculate_daily_consumption(self, planet_id: str, item_symbol: str) -> float:
        """Calculate daily consumption from active production queues and workforce needs"""
        # Use site_service to get buildings on planet
        # Use recipe_service to get recipe inputs and efficiency calculations
        # Use workforce_service to calculate workforce consumption
        # Factor in building condition from site_service
        # Return total daily consumption rate
        
    def _calculate_daily_production(self, planet_id: str, item_symbol: str) -> float:
        """Calculate daily production from active production queues"""
        # Use site_service to get buildings and their production queues
        # Use recipe_service to get recipe outputs and efficiency calculations  
        # Factor in building condition and workforce efficiency
        # Return total daily production rate
```

## Key Calculations & Logic

### Material Demand Calculation (Real-time Computation)
For each planet, compute daily material needs from source data:

1. **Current Storage**: Query `Storage` + `StorageItem` for actual current stock on planet sites
2. **Active Production**: Query `SiteBuilding` + active `QueueItem` records  
3. **Material Consumption**: Calculate from `Recipe` + `RecipeInput` relationships
4. **Workforce Efficiency**: Factor in building `condition` and workforce levels
5. **Production Output**: Calculate from `Recipe` + `RecipeOutput` for items produced locally
6. **Net Burn Rate**: `daily_consumption - daily_production`
7. **Stockout Prediction**: `current_storage_amount / net_burn_rate` (if positive)

This ensures forecasts are always current and derived from the single source of truth.

### Shipping Optimization

#### Route Types
1. **Supply Routes**: Move materials from producer planets to consumer planets
2. **Resupply Routes**: Deliver consumables to prevent stockouts  
3. **Export Routes**: Transport finished goods to central exchange
4. **Route Consolidation**: Combine multiple deliveries per planet visit

#### Jump Path Finding Algorithm
Based on the SQL analysis, we need a pathfinding system:

```python
class SystemPathfinder:
    def find_shortest_path(self, origin_system_id: str, dest_system_id: str) -> list[str]:
        """Find shortest jump path between systems using existing SystemConnection table"""
        # Use Dijkstra or BFS on the system connection graph
        # Return list of system IDs representing the jump route
        
    def calculate_route_cost(self, path: list[str], ship: Ship) -> RouteCost:
        """Calculate time, fuel, and other costs for a route"""
        return RouteCost(
            jumps=len(path) - 1,
            travel_time_hours=self._estimate_travel_time(path, ship),
            ftl_fuel_needed=len(path) - 1 * ship.ftl_fuel_per_jump,
            stl_fuel_needed=ship.stl_fuel_flow_rate * travel_time_hours
        )
```

#### Multi-Stop Route Optimization
For efficient shipping, we need to solve a variant of the Traveling Salesman Problem:
- **Input**: List of planets to visit with pickup/delivery requirements
- **Constraints**: Ship cargo capacity, fuel capacity, travel time limits
- **Dynamic Priority**: Calculate route urgency based on real-time burn rates and days until stockout
- **Output**: Optimal route order that minimizes total travel time/cost while prioritizing critical shipments

```python
class RouteOptimizationService:
    def calculate_route_priority(self, route: ShippingRoute) -> float:
        """Calculate dynamic priority based on cargo urgency"""
        max_urgency = 0.0
        
        for cargo in route.cargo_items:
            if cargo.action == "dropoff":
                # Calculate urgency for deliveries based on destination stockout risk
                demand = self.demand_service.calculate_planet_demand(
                    route.destination_planet_id, cargo.item_symbol
                )
                # Higher urgency = lower days until stockout
                urgency = 1.0 / max(demand.days_until_stockout, 0.1)
                max_urgency = max(max_urgency, urgency)
        
        return max_urgency
```

## Remaining Questions for Implementation

A few details still need clarification:

1. **Travel Time Per Jump**: What's the base time for each jump, and how does ship acceleration affect it?

2. **Fuel Consumption Rates**: 
   - How much FTL fuel does each jump consume?
   - Is STL fuel consumption truly time-based or distance-based?

3. **Multi-Stop Routes**: Can ships make multiple stops in a single system before jumping to the next system?

4. **Buffer Requirements**: How many buffer days should be maintained for different types of materials (critical vs non-critical)?

## FIO API Integration

### Ship Data Sync
Ships can be synced from the FIO API using the endpoint:
```
GET https://rest.fnar.net/ship/ships/{username}
Authorization: {api_key}
```

This should be integrated into the existing sync system in `cli.py`:
- Add ship sync to the `sync` command
- Use existing FIO client authentication 
- Store ship data in database with proper relationships to materials

### Fuel Store Management
The API provides separate store IDs for:
- Main cargo (`StoreId`)
- STL fuel (`StlFuelStoreId`) 
- FTL fuel (`FtlFuelStoreId`)

These store IDs likely correspond to inventory/storage records that can be queried separately to get actual fuel levels and cargo contents.

## Key Insights from Real Data & Game Mechanics

### Jump-Based Travel System
From the SQL query analysis, travel in Prosperous Universe is **jump-based**:
- Ships travel between **systems** via jump connections, not direct routes
- Travel time is measured in **jumps** (hops between connected systems)
- Path finding requires recursive algorithms to find shortest routes
- Maximum practical jump distance appears to be ~10 jumps for efficient travel

### Fuel Consumption Model
- **STL Fuel**: Used for in-system travel and potentially short jumps
  - `StlFuelFlowRate` from ship data (0.015 in examples)
  - Rate likely per unit of time or per jump
- **FTL Fuel**: Used for jump travel between systems
  - Separate fuel store (`FtlFuelStoreId`)
  - Consumption likely per jump rather than time-based

### Ship Performance Factors
- **Mass affects acceleration**: Higher cargo load = slower acceleration
- **Volume capacity**: Fixed cargo space (1632 units in examples)
- **Current location**: Ships have a `location` field for tracking position

### Travel Time Calculation
Travel time will depend on:
```python
# Pseudo-algorithm for travel time
def calculate_travel_time(origin_system, destination_system, ship):
    jumps = find_shortest_path(origin_system, destination_system)
    
    # Each jump has base time + ship-specific factors
    time_per_jump = base_jump_time / (ship.acceleration * mass_factor)
    ftl_fuel_needed = jumps * fuel_per_jump
    
    return jumps * time_per_jump
```

### Ship Condition & Repairs
- `Condition` field tracks degradation (0.962-0.958 in examples)
- `RepairMaterials` shows exact materials needed for maintenance
- Condition likely affects performance and fuel efficiency

## Next Steps
1. **Implement Ship Models**: Add `Ship` and `ShipRepairMaterial` models to `db_models.py`
2. **Create Ship Service**: Add `ship_service.py` following existing service patterns
3. **Add Ship Sync to FIO Client**: Integrate ship API endpoint into existing sync system
4. **Implement DemandForecastService**: Create service with dependencies on existing services
5. **Add Storage Service Method**: Add `get_planet_storage_amount()` method to existing storage service
6. **Create RouteOptimizationService**: Implement pathfinding and route optimization algorithms
7. **Add Ship Models to __init__.py**: Export new models following existing patterns

Would you like me to start implementing the ship models in your database schema? 