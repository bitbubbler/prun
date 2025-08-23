# Prun Architecture Documentation

This document provides an overview of the architecture for the `prun` application, focusing on the core components within the `prun` directory.

## Data Layer

The data layer is responsible for all interactions with the database. It is composed of the database connection, data models, repositories, and repository interfaces.

### Database (`prun/database.py`)

The `prun/database.py` file sets up the connection to the SQLite database (`prun.db`) using SQLModel and SQLAlchemy.

- `engine`: The SQLAlchemy engine is created to connect to the `sqlite:///prun.db` database file.
- `init_db()`: This function creates all the necessary tables in the database based on the SQLModel metadata.
- `get_session()`: A context manager that provides a database session. It handles the session lifecycle, including committing transactions on success and rolling them back on exceptions. This ensures data integrity.

### Models (`prun/models`)

The `prun/models` directory defines the data structures for the application. It contains two main types of models:

- **`db_models.py`**: Contains the SQLModel classes that map to the database tables. These models define the schema of the application's database.
- **`fly_models.py`**: Contains Pydantic models used for parsing data from external sources, likely the FIO API. These are referred to as "fly" models as they are transient and used for data transfer.

The `__init__.py` file in this directory makes the models easily importable throughout the application.

#### Detailed Model Concepts

The models in `prun` are designed to reflect the core mechanics of the Prosperous Universe game. They are divided into two categories: database models (`db_models.py`) that represent the persistent state of the game world, and "fly" models (`fly_models.py`) that represent transient data used for calculations and business logic.

##### Concept 1: The Production Chain (Items, Buildings, Recipes)

The core economic loop of the game is producing items, which is represented by a chain of linked models.

- **`Item`**: This is the fundamental building block, representing any material, component, or commodity. It has physical properties like `weight` and `volume`.

- **`Building`**: Production happens in buildings. Each `Building` model defines a type of facility (e.g., Smelter, Refinery). A key attribute is its `expertise` (e.g., 'METALLURGY', 'CHEMISTRY'), which is crucial for efficiency calculations.

- **`Recipe`**: This model defines a manufacturing process.

  - It links `Item`s as **inputs** (`RecipeInput`) and **outputs** (`RecipeOutput`).
  - It specifies the `Building` required to execute the recipe.
  - It has a base `time_ms`, which is the unmodified duration of the process.

- **Nuance: Efficiency and "Fly" Models**: The base `time_ms` of a `Recipe` is rarely the actual time. The application uses "fly" models to calculate the real-world performance:
  - **`EfficientRecipe`**: This model takes a base `Recipe` and applies an `efficiency` factor. This factor is calculated in the services layer, considering player `Experts` and planet-wide `COGCProgram` bonuses. The result is a reduced `time_ms`, reflecting faster production.

##### Concept 2: Planet-Specific Resources and Conditions

The game world is not uniform. Planets have unique characteristics that directly impact gameplay, a concept captured in the models.

- **`Planet`**: This model stores the physical attributes of a planet, such as `gravity`, `temperature`, and `pressure`.

- **`PlanetResource`**: This is a critical model that makes certain `Item`s available for extraction on a specific `Planet`.

  - It links a `material_id` (an `Item`) to a `planet_natural_id`.
  - The `factor` field represents the richness or abundance of that resource.
  - The `resource_type` (MINERAL, LIQUID, GASEOUS) determines the type of extractor building needed (EXT, RIG, COL).

- **Nuance: Resource Extraction Recipes**: Resource extraction is a special type of recipe.

  - The base `Recipe` for extraction (e.g., from an Extractor 'EXT') has no fixed output.
  - The **`PlanetExtractionRecipe`** "fly" model calculates the actual output. It uses the `PlanetResource.factor` to determine the yield, resulting in a variable `quantity` for the `RecipeOutput` and an adjusted `time_ms`. This accurately models how richer deposits yield more resources per cycle.

- **Nuance: Environmental Building Costs**: A planet's environment affects construction.
  - The base cost of a `Building` is defined by `BuildingCost`.
  - However, the **`PlanetBuilding`** "fly" model demonstrates how additional costs are added based on the `Planet`'s attributes. For example, a planet with low `pressure` requires `SEA` (Sealing) materials, while a high-temperature planet requires `TSH` (Thermal Shielding), adding to the total construction cost.

##### Concept 3: Economic Models

The application models several ways to trade and acquire goods.

- **`Exchange` and `ExchangePrice`**: Represents the major commodity exchanges (e.g., AI1, NC1). `ExchangePrice` provides real-time market data for an `Item`, including `ask_price` (buy price) and `bid_price` (sell price).
- **`InternalOffer`**: Models a private trading system. A `Company` can create direct offers for an `Item` at a set `price`. This allows for player-to-player trading outside of the public market.
- **`LocalMarketAd`**: Represents ads on a specific planet's local market, for buying, selling, or shipping goods. This is for localized, planet-bound trading.

These models work together to create a rich data ecosystem that mirrors the complex rules and mechanics of the game, allowing the services and CLI tools to perform meaningful calculations and analysis.

### Repository Pattern (`prun/repository.py` and `prun/interface.py`)

The application uses the repository pattern to abstract the data access logic from the business logic.

#### Interfaces (`prun/interface.py`)

This file defines the abstract base classes (ABCs) for each repository. These interfaces define the contract that the concrete repository classes must adhere to. This promotes loose coupling and makes it easier to test the services by allowing for mock repository implementations.

For example, `BuildingRepositoryInterface` defines methods like `get_building` and `create_building`.

#### Repositories (`prun/repository.py`)

This file contains the concrete implementations of the repository interfaces. Each repository class (e.g., `BuildingRepository`) is responsible for querying the database for a specific model or group of related models.

- Repositories are initialized with a `Session` object from `database.py`.
- They use SQLModel's `select` statements to query the database.
- This keeps all the SQL logic contained within the repository layer.

## Business Logic Layer (Services)

The `prun/services` directory is where the core business logic of the application resides. These services are responsible for orchestrating data from the repositories and applying game mechanics to produce meaningful results. They encapsulate the "how" of the application's features.

### Core Feature: COGM Calculation

The most complex feature is the calculation of the Cost of Goods Manufactured (COGM), primarily handled by the `CostService`. This process demonstrates how multiple services collaborate to model the game's economy. The calculation is broken down into several key components:

1.  **Recipe Cost**: The cost of the direct materials required to produce an item.
2.  **Workforce Cost**: The cost of consumables required to support the workforce operating the building.
3.  **Repair Cost**: The cost of materials needed to repair the building, amortized over the duration of the recipe.

The `CostService.calculate_cogm` method orchestrates this process. Let's break down how each component is calculated.

#### 1. Recipe and Efficiency Calculations (`RecipeService`, `EfficiencyService`)

Before calculating costs, the true performance of a recipe must be determined.

- **`RecipeService.find_recipe`**: This is the entry point for getting a recipe. It handles the crucial logic of determining whether a recipe is a standard manufacturing recipe or a planet-specific resource extraction.

  - If it's a standard recipe, it's fetched directly from the database.
  - If it's for resource extraction (e.g., `EXT:=>`), it uses the `PlanetExtractionRecipe` fly model to calculate the actual output based on the `PlanetResource.factor`. This is a key nuance: the richer the resource, the more you get per cycle.

- **`EfficiencyService`**: This service calculates the all-important efficiency bonus.
  - `get_expert_efficiency`: Calculates the time reduction bonus based on the number of `Experts` a player has in a specific field (e.g., Metallurgy).
  - `get_cogc_efficiency`: Calculates the bonus from a planet's active `COGCProgram`.
  - These two bonuses are summed up and passed to the `EfficientRecipe` or `EfficientPlanetExtractionRecipe` fly models, which reduce the recipe's `time_ms`.

#### 2. Workforce Cost Calculation (`WorkforceService`)

- `WorkforceService.calculate_workforce_cost_for_recipe`: This method calculates the cost of keeping the required workforce happy for the duration of one recipe cycle.
  - It first determines the number of workers of each tier (`PIONEERS`, `SETTLERS`, etc.) required by the `Building`.
  - It fetches the `WorkforceNeed` for each tier, which defines the required consumable items (e.g., DW, RAT).
  - The `workforce_days` method calculates what fraction of a 24-hour day the recipe's runtime represents.
  - The cost of each consumable is then multiplied by this fraction to get the cost per recipe run.

#### 3. Building Repair Cost Calculation

- `CostService.calculate_repair_cost_for_recipe`: This method calculates the building degradation cost for a single recipe run.
  - It first calculates the total cost to fully repair a building from 0% condition (`days_since_last_repair=180`).
  - This total repair cost is then divided by 180 to get a `daily_repair_cost`.
  - This daily cost is then multiplied by the recipe's duration as a fraction of a day (`recipe.percent_of_day`) to determine the portion of repair cost attributable to that single production run.

#### 4. Assembling the Final COGM

- `CostService.calculate_recipe_output_cogm`: This is the final step.
  - It takes the total calculated costs (inputs + workforce + repair).
  - It then divides this total cost by the `quantity` of the item produced in the recipe's output.
  - The result is the final **Cost of Goods Manufactured** for a single unit of the item, a critical metric for determining profitability.

This layered approach, with clear separation of concerns between services, allows the application to model complex, interconnected game mechanics in a manageable and testable way.

## Future Features

This section outlines potential new features that can be built upon the existing architecture.

### Feature: Building ROI Calculator

This feature introduces a new CLI command, `prun roi <item_symbol> --planet <planet_name>`, to calculate the return on investment for constructing a new building.

#### 1. Goal

To calculate the "payback period" for a new production building—that is, the number of days it will take for the profit from selling a product to cover the initial investment cost of the building.

#### 2. CLI Command Structure

The new CLI command is defined in `prun/cli.py` using the `click` library:

```python
@cli.command()
@click.argument('item_symbol')
@click.option('--planet', required=True, help='The name of the planet.')
@click.option('--json', is_flag=True, help='Output in JSON format.')
def roi(item_symbol, planet, json):
    # Logic to calculate ROI using ROIService
    pass
```

Example usage:

```bash
prun roi CL --planet Terra
prun roi H2O --planet Europa --json
```

#### 3. Underlying Services Implementation

The ROI calculation reuses existing services but is encapsulated in a new `ROIService`:

- **ROIService**: Orchestrates the ROI calculation using existing services
  - **Dependencies**: `BuildingService`, `PlanetService`, `ExchangeService`, `CostService`
  - **Methods**:
    - `calculate_investment()`: Calculates the total investment cost
    - `calculate_return()`: Calculates the daily return (profit)
    - `calculate_payback_period()`: Calculates the payback period in days

#### 4. Data Models for ROI Calculations

New Pydantic models are defined in `prun/models/roi_models.py`:

```python
class MaterialPrice(BaseModel):
    symbol: str
    price: float

class BuildingCost(BaseModel):
    material: MaterialPrice
    quantity: float
    total_cost: float

class PlanetBuildingCost(BaseModel):
    base_costs: List[BuildingCost]
    planetary_costs: List[BuildingCost]
    total_cost: float

class Investment(BaseModel):
    building_costs: PlanetBuildingCost
    total_investment: float

class Return(BaseModel):
    cogm: float
    sell_price: float
    profit_per_unit: float
    daily_profit: float

class ROICalculation(BaseModel):
    investment: Investment
    return_: Return
    payback_period: float
```

#### 5. Integration with Existing Services

The `ROIService` is integrated with existing services through dependency injection:

1. **Dependency Injection Container**:

   - Add `ROIService` to the dependency injection container in `prun/di.py`
   - Register `ROIService` as a factory provider
   - Inject dependencies: `BuildingService`, `PlanetService`, `ExchangeService`, `CostService`

2. **Service Registration**:

   - In `prun/di.py`, add a new provider for `ROIService`
   - Ensure that the `ROIService` is properly initialized with its dependencies

3. **Accessing the Service**:
   - Access the `ROIService` through the container in the new `roi` command
   - Use the service to perform ROI calculations

#### 6. Display Mechanism for ROI Results

The display mechanism is consistent with existing CLI commands:

1. **Table Display**:

   - Uses the `rich` library for formatted output
   - Shows investment details, return details, and payback period

2. **JSON Display**:
   - Provides a structured JSON output for programmatic use

#### 7. Implementation Checklist

- [x] Design new CLI command structure for ROI display
- [x] Plan underlying services implementation
- [x] Design data models for ROI calculations
- [x] Plan integration with existing services
- [x] Design display mechanism for ROI results
- [x] Create implementation checklist for ROI feature

This updated feature implementation provides a comprehensive solution for calculating and displaying ROI for building investments in the game.

## Application Core

The core of the application resides in the `prun` directory, orchestrating the overall functionality. This includes handling dependencies, configuration, user interactions, and the main application entry points.

### Dependency Injection (`prun/di.py`)

The application utilizes the `dependency-injector` library to manage dependencies, which promotes loose coupling and testability.

- A `Container` class is defined to declare and wire up all the components (services, repositories, etc.).
- `providers.Singleton` is used for objects that should only be created once, like the database engine and the `FIOClient`.
- `providers.Factory` is used for objects that should be created on each request, such as repository and service instances. This ensures that each request gets a fresh instance with its own session.
- The `session` is managed as a `providers.Resource`, which handles the setup and teardown of the database session for each transaction.

### Configuration (`prun/config.py`)

Configuration is managed using Pydantic models, which provides data validation and type hints.

- `YAMLConfigBase` is a base class that provides a `from_yaml` classmethod to load configurations from YAML files. It uses `pydantic` for strict validation, ensuring that the configuration files adhere to the defined schema.
- Various configuration models like `EmpireIn`, `InternalOfferConfig`, and `BuyListConfig` define the structure for different YAML configuration files used in the CLI commands.

### Command-Line Interface (`prun/cli.py`)

The `prun/cli.py` file implements the command-line interface for the application using the `click` library. This is the primary way for users to interact with the application.

- The file defines a main `cli` group and several commands:
  - `sync`: Synchronizes data from the FIO API.
  - `cogm`: Calculates the Cost of Goods Manufactured for a specific item on a given planet.
  - `analyze-empire`: Analyzes a player's empire based on a YAML configuration file.
  - `buy-list`: Processes a shopping list from a YAML file.
  - `insert-offers`: Inserts internal trade offers from a YAML file.
  - `recipe-search`: Searches for recipes for a given item.
- It uses the `rich` library to produce formatted and colored output in the terminal, making it more user-friendly.

### API (`prun/main.py`)

The `prun/main.py` file provides a web-facing API built with `FastAPI`.

- It defines several endpoints to expose the application's data over HTTP (e.g., `/materials`, `/recipes`, `/planets`).
- It uses a dependency (`get_session`) to manage database sessions for each API request.
- The API also includes CRUD (Create, Read, Update, Delete) operations for internal offers.
- CORS (Cross-Origin Resource Sharing) is enabled to allow web frontends to interact with the API.
- The server can be run using `uvicorn`.

### Error Handling (`prun/errors.py`)

The `prun/errors.py` file defines custom exception classes for the application.

- These custom exceptions, such as `MultipleRecipesError` and `RecipeNotFoundError`, allow for more specific error handling throughout the application.
- This makes the code more readable and helps in providing more specific feedback to the user when something goes wrong.
