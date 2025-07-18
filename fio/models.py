from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict, RootModel
from typing import Optional, List, Dict


class FIOMaterial(BaseModel):
    """Material from the /csv/materials endpoint."""

    material_id: str = Field(..., description="Material ID", alias="MaterialId")
    ticker: str = Field(
        ..., description="Material ticker symbol (e.g. 'H2O')", alias="Ticker"
    )
    name: str = Field(..., description="Material name (e.g. 'Water')", alias="Name")
    category: str = Field(
        ..., description="Material category (e.g. 'Resources')", alias="CategoryName"
    )
    weight: float = Field(..., description="Material weight in tons", alias="Weight")
    volume: float = Field(..., description="Material volume in m³", alias="Volume")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "Ticker": "AAR",
                "Name": "antennaArray",
                "Category": "electronic devices",
                "Weight": "0.78",
                "Volume": "0.5",
            }
        },
    )


class FIOBuildingRecipe(BaseModel):
    """Recipe from the /csv/buildingrecipes endpoint."""

    key: str = Field(..., description="Recipe key (e.g. 'FFP:10xH2O-5xOVE=>2xRAT')")
    building: str = Field(..., description="Building ticker symbol (e.g. 'FFP')")
    duration: int = Field(..., description="Recipe duration in seconds")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "Key": "AAF:1xBMF-1xSNM=>1xNV2",
                "Building": "AAF",
                "Duration": "172800",
            }
        },
    )


class FIOPrice(BaseModel):
    """Price from the /exchange/all endpoint."""

    material_ticker: str = Field(
        ..., description="Material ticker symbol (e.g. 'H2O')", alias="MaterialTicker"
    )
    exchange: str = Field(
        ..., description="Exchange code (e.g. 'IC1')", alias="ExchangeCode"
    )
    mm_buy: Optional[float] = Field(
        None, description="Market maker buy price", alias="MMBuy"
    )
    mm_sell: Optional[float] = Field(
        None, description="Market maker sell price", alias="MMSell"
    )
    average_price: float = Field(
        ..., description="Current market average price in A$", alias="PriceAverage"
    )

    # Ask data
    ask_amount: Optional[int] = Field(
        None, description="Total amount available for sale", alias="AskCount"
    )
    ask_price: Optional[float] = Field(
        None, description="Current ask price", alias="Ask"
    )
    ask_available: Optional[int] = Field(
        None, description="Amount available at ask price", alias="Supply"
    )

    # Bid data
    bid_amount: Optional[int] = Field(
        None, description="Total amount requested for purchase", alias="BidCount"
    )
    bid_price: Optional[float] = Field(
        None, description="Current bid price", alias="Bid"
    )
    bid_available: Optional[int] = Field(
        None, description="Amount available at bid price", alias="Demand"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now, description="Price timestamp"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIORecipeInputOutput(BaseModel):
    """Recipe input from the /csv/recipeinputs endpoint."""

    ticker: str = Field(
        ..., description="Input material ticker (e.g. 'H2O')", alias="Ticker"
    )
    amount: float = Field(..., description="Input amount per batch", alias="Amount")

    model_config = ConfigDict(from_attributes=True)


class FIORecipe(BaseModel):
    """Recipe from the /recipes/allrecipes endpoint."""

    recipe_name: str = Field(
        ...,
        description="Recipe Name (e.g. '1xTC 4xREA 4xFLX=>1xETC')",
        alias="RecipeName",
    )
    standard_recipe_name: str = Field(
        ...,
        description="Standard Recipe Name (e.g. 'TNP:4xFLX-4xREA-1xTC=>1xETC')",
        alias="StandardRecipeName",
    )
    building_ticker: str = Field(
        ..., description="Building ticker symbol (e.g. 'FFP')", alias="BuildingTicker"
    )
    inputs: List[FIORecipeInputOutput] = Field(
        ..., description="List of input materials and amounts", alias="Inputs"
    )
    outputs: List[FIORecipeInputOutput] = Field(
        ..., description="List of output materials and amounts", alias="Outputs"
    )
    time_ms: int = Field(
        ..., description="Recipe duration in milliseconds", alias="TimeMs"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "Key": "AAF:1xBMF-1xSNM=>1xNV2",
                "Building": "AAF",
                "Duration": "172800",
                "Inputs": [
                    {"Ticker": "BMF", "Amount": "1"},
                    {"Ticker": "SNM", "Amount": "1"},
                ],
                "Outputs": [{"Ticker": "NV2", "Amount": "1"}],
            }
        },
    )


class FIOBuildingCost(BaseModel):
    """Building cost from the /building/allbuildings endpoint."""

    commodity_name: str = Field(
        ..., description="Commodity name", alias="CommodityName"
    )
    commodity_ticker: str = Field(
        ..., description="Commodity ticker", alias="CommodityTicker"
    )
    weight: float = Field(..., description="Weight of the commodity", alias="Weight")
    volume: float = Field(..., description="Volume of the commodity", alias="Volume")
    amount: int = Field(..., description="Amount required", alias="Amount")

    model_config = ConfigDict(from_attributes=True)


class FIOBuildingRecipeInputOutput(BaseModel):
    """Recipe input/output from the /building/allbuildings endpoint."""

    commodity_name: str = Field(
        ..., description="Commodity name", alias="CommodityName"
    )
    commodity_ticker: str = Field(
        ..., description="Commodity ticker", alias="CommodityTicker"
    )
    weight: float = Field(..., description="Weight of the commodity", alias="Weight")
    volume: float = Field(..., description="Volume of the commodity", alias="Volume")
    amount: int = Field(..., description="Amount required", alias="Amount")

    model_config = ConfigDict(from_attributes=True)


class FIOBuildingRecipeDetail(BaseModel):
    """Detailed recipe from the /building/allbuildings endpoint."""

    inputs: List[FIOBuildingRecipeInputOutput] = Field(
        ..., description="List of input materials", alias="Inputs"
    )
    outputs: List[FIOBuildingRecipeInputOutput] = Field(
        ..., description="List of output materials", alias="Outputs"
    )
    building_recipe_id: str = Field(
        ..., description="Building recipe ID", alias="BuildingRecipeId"
    )
    duration_ms: int = Field(
        ..., description="Recipe duration in milliseconds", alias="DurationMs"
    )
    recipe_name: str = Field(..., description="Recipe name", alias="RecipeName")
    standard_recipe_name: str = Field(
        ..., description="Standard recipe name", alias="StandardRecipeName"
    )

    model_config = ConfigDict(from_attributes=True)


class FIOBuilding(BaseModel):
    """Detailed building information from the /building/allbuildings endpoint."""

    building_costs: List[FIOBuildingCost] = Field(
        ..., description="List of building costs", alias="BuildingCosts"
    )
    recipes: List[FIOBuildingRecipeDetail] = Field(
        ..., description="List of recipes", alias="Recipes"
    )
    building_id: str = Field(..., description="Building ID", alias="BuildingId")
    name: str = Field(..., description="Building name", alias="Name")
    ticker: str = Field(..., description="Building ticker", alias="Ticker")
    expertise: str | None = Field(
        None, description="Required expertise", alias="Expertise"
    )
    pioneers: int = Field(
        ..., description="Number of pioneers required", alias="Pioneers"
    )
    settlers: int = Field(
        ..., description="Number of settlers required", alias="Settlers"
    )
    technicians: int = Field(
        ..., description="Number of technicians required", alias="Technicians"
    )
    engineers: int = Field(
        ..., description="Number of engineers required", alias="Engineers"
    )
    scientists: int = Field(
        ..., description="Number of scientists required", alias="Scientists"
    )
    area_cost: int = Field(..., description="Area cost", alias="AreaCost")
    user_name_submitted: str = Field(
        ...,
        description="Username who submitted the building",
        alias="UserNameSubmitted",
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the building was submitted", alias="Timestamp"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOPlanet(BaseModel):
    """Planet from the /planet/allplanets endpoint."""

    planet_natural_id: str = Field(
        ..., description="Planet natural ID (e.g. 'PG-241h')", alias="PlanetNaturalId"
    )
    planet_name: str = Field(
        ..., description="Planet name (e.g. 'PG-241h')", alias="PlanetName"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOSystemConnection(BaseModel):
    """System connection from the /systemstarts endpoint."""

    system_connection_id: str = Field(
        ..., description="System connection ID", alias="SystemConnectionId"
    )
    connecting_id: str = Field(
        ..., description="Connecting system ID", alias="ConnectingId"
    )

    model_config = ConfigDict(from_attributes=True)


class FIOSystem(BaseModel):
    """System from the /systemstarts endpoint."""

    connections: List[FIOSystemConnection] = Field(
        ..., description="List of system connections", alias="Connections"
    )
    system_id: str = Field(..., description="System ID", alias="SystemId")
    name: str = Field(..., description="System name", alias="Name")
    natural_id: str = Field(..., description="System natural ID", alias="NaturalId")
    type: str = Field(..., description="System type", alias="Type")
    position_x: float = Field(
        ..., description="X position coordinate", alias="PositionX"
    )
    position_y: float = Field(
        ..., description="Y position coordinate", alias="PositionY"
    )
    position_z: float = Field(
        ..., description="Z position coordinate", alias="PositionZ"
    )
    sector_id: str = Field(..., description="Sector ID", alias="SectorId")
    sub_sector_id: str = Field(..., description="Sub-sector ID", alias="SubSectorId")
    user_name_submitted: str = Field(
        ..., description="Username who submitted the system", alias="UserNameSubmitted"
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the system was submitted", alias="Timestamp"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOWorkforceNeed(BaseModel):
    """Workforce need from the /global/workforceneeds endpoint."""

    material_id: str = Field(..., description="Material ID", alias="MaterialId")
    material_name: str = Field(..., description="Material name", alias="MaterialName")
    material_ticker: str = Field(
        ..., description="Material ticker", alias="MaterialTicker"
    )
    material_category: str = Field(
        ..., description="Material category ID", alias="MaterialCategory"
    )
    amount: float = Field(..., description="Amount needed per worker", alias="Amount")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOWorkforceNeeds(BaseModel):
    """Workforce needs for a specific workforce type from the /global/workforceneeds endpoint."""

    needs: List[FIOWorkforceNeed] = Field(
        ..., description="List of material needs", alias="Needs"
    )
    workforce_type: str = Field(
        ...,
        description="Type of workforce (e.g. PIONEER, SETTLER, TECHNICIAN)",
        alias="WorkforceType",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOComexExchange(BaseModel):
    """Commodity exchange from the /global/comexexchanges endpoint."""

    comex_exchange_id: str = Field(
        ..., description="Exchange ID", alias="ComexExchangeId"
    )
    exchange_name: str = Field(..., description="Exchange name", alias="ExchangeName")
    exchange_code: str = Field(
        ..., description="Exchange code (e.g. 'IC1')", alias="ExchangeCode"
    )
    exchange_operator_id: str | None = Field(
        None, description="Exchange operator ID", alias="ExchangeOperatorId"
    )
    exchange_operator_code: str | None = Field(
        None, description="Exchange operator code", alias="ExchangeOperatorCode"
    )
    exchange_operator_name: str | None = Field(
        None, description="Exchange operator name", alias="ExchangeOperatorName"
    )
    currency_numeric_code: int = Field(
        ..., description="Currency numeric code", alias="CurrencyNumericCode"
    )
    currency_code: str = Field(
        ..., description="Currency code (e.g. 'ICA')", alias="CurrencyCode"
    )
    currency_name: str = Field(..., description="Currency name", alias="CurrencyName")
    currency_decimals: int = Field(
        ...,
        description="Number of decimal places for currency",
        alias="CurrencyDecimals",
    )
    location_id: str = Field(..., description="Location ID", alias="LocationId")
    location_name: str = Field(..., description="Location name", alias="LocationName")
    location_natural_id: str = Field(
        ..., description="Location natural ID (e.g. 'HRT')", alias="LocationNaturalId"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOSimulation(BaseModel):
    """Simulation settings from the FIO API."""

    simulation_interval: int = Field(
        ..., description="Simulation interval in seconds", alias="SimulationInterval"
    )
    flight_stl_factor: float = Field(
        ..., description="Flight STL factor", alias="FlightSTLFactor"
    )
    flight_ftl_factor: float = Field(
        ..., description="Flight FTL factor", alias="FlightFTLFactor"
    )
    planetary_motion_factor: float = Field(
        ..., description="Planetary motion factor", alias="PlanetaryMotionFactor"
    )
    parsec_length: float = Field(..., description="Parsec length", alias="ParsecLength")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOAuthLoginRequest(BaseModel):
    """Login request model for the /auth/login endpoint."""

    username: str = Field(..., description="FIO username")
    password: str = Field(..., description="FIO password")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {"username": "your_username", "password": "your_password"}
        },
    )


class FIOAuthLoginResponse(BaseModel):
    """Login response model from the /auth/login endpoint."""

    auth_token: str = Field(
        ..., description="Authentication token (GUID)", alias="AuthToken"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOSiteBuildingMaterial(BaseModel):
    """Material from a site building."""

    material_id: str = Field(..., description="Material ID", alias="MaterialId")
    material_name: str = Field(..., description="Material name", alias="MaterialName")
    material_ticker: str = Field(
        ..., description="Material ticker", alias="MaterialTicker"
    )
    material_amount: int = Field(
        ..., description="Material amount", alias="MaterialAmount"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOSiteBuilding(BaseModel):
    """Building from a site."""

    reclaimable_materials: List[FIOSiteBuildingMaterial] = Field(
        ..., description="List of reclaimable materials", alias="ReclaimableMaterials"
    )
    repair_materials: List[FIOSiteBuildingMaterial] = Field(
        ..., description="List of repair materials", alias="RepairMaterials"
    )
    site_building_id: str = Field(
        ..., description="Site building ID", alias="SiteBuildingId"
    )
    building_id: str = Field(..., description="Building ID", alias="BuildingId")
    building_created: int = Field(
        ...,
        description="Building creation timestamp in milliseconds",
        alias="BuildingCreated",
    )
    building_name: str = Field(..., description="Building name", alias="BuildingName")
    building_ticker: str = Field(
        ..., description="Building ticker", alias="BuildingTicker"
    )
    building_last_repair: Optional[int] = Field(
        None,
        description="Last repair timestamp in milliseconds",
        alias="BuildingLastRepair",
    )
    condition: float = Field(
        ..., description="Building condition (0-1)", alias="Condition"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOSite(BaseModel):
    """Site information."""

    buildings: List[FIOSiteBuilding] = Field(
        ..., description="List of buildings", alias="Buildings"
    )
    site_id: str = Field(..., description="Site ID", alias="SiteId")
    planet_id: str = Field(..., description="Planet ID", alias="PlanetId")
    planet_identifier: str = Field(
        ..., description="Planet identifier", alias="PlanetIdentifier"
    )
    planet_name: str = Field(..., description="Planet name", alias="PlanetName")
    planet_founded_epoch_ms: int = Field(
        ...,
        description="Planet founding timestamp in milliseconds",
        alias="PlanetFoundedEpochMs",
    )
    invested_permits: int = Field(
        ..., description="Number of invested permits", alias="InvestedPermits"
    )
    maximum_permits: int = Field(
        ..., description="Maximum number of permits", alias="MaximumPermits"
    )
    user_name_submitted: str = Field(
        ..., description="Username who submitted the site", alias="UserNameSubmitted"
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the site was submitted", alias="Timestamp"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOStorageItem(BaseModel):
    """Storage item from the /storage/{UserName} endpoint."""

    material_id: str = Field(..., description="Material ID", alias="MaterialId")
    material_name: Optional[str] = Field(
        None, description="Material name", alias="MaterialName"
    )
    material_ticker: Optional[str] = Field(
        None, description="Material ticker", alias="MaterialTicker"
    )
    material_category: Optional[str] = Field(
        None, description="Material category ID", alias="MaterialCategory"
    )
    material_weight: float = Field(
        ..., description="Material weight per unit", alias="MaterialWeight"
    )
    material_volume: float = Field(
        ..., description="Material volume per unit", alias="MaterialVolume"
    )
    material_amount: int = Field(
        ..., description="Amount of material", alias="MaterialAmount"
    )
    material_value: float = Field(
        ..., description="Total value of material", alias="MaterialValue"
    )
    material_value_currency: Optional[str] = Field(
        None, description="Currency of material value", alias="MaterialValueCurrency"
    )
    type: str = Field(
        ...,
        description="Type of storage item (e.g. INVENTORY, SHIPMENT, BLOCKED)",
        alias="Type",
    )
    total_weight: float = Field(
        ..., description="Total weight of material", alias="TotalWeight"
    )
    total_volume: float = Field(
        ..., description="Total volume of material", alias="TotalVolume"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOStorage(BaseModel):
    """Storage from the /storage/{UserName} endpoint."""

    storage_items: List[FIOStorageItem] = Field(
        ..., description="List of storage items", alias="StorageItems"
    )
    storage_id: str = Field(..., description="Storage ID", alias="StorageId")
    addressable_id: str = Field(
        ..., description="Addressable ID", alias="AddressableId"
    )
    name: Optional[str] = Field(None, description="Storage name", alias="Name")
    weight_load: float = Field(
        ..., description="Current weight load", alias="WeightLoad"
    )
    weight_capacity: float = Field(
        ..., description="Maximum weight capacity", alias="WeightCapacity"
    )
    volume_load: float = Field(
        ..., description="Current volume load", alias="VolumeLoad"
    )
    volume_capacity: float = Field(
        ..., description="Maximum volume capacity", alias="VolumeCapacity"
    )
    fixed_store: bool = Field(
        ..., description="Whether the store is fixed", alias="FixedStore"
    )
    type: str = Field(
        ...,
        description="Type of storage (e.g. STORE, WAREHOUSE_STORE, FTL_FUEL_STORE)",
        alias="Type",
    )
    user_name_submitted: str = Field(
        ..., description="Username who submitted the storage", alias="UserNameSubmitted"
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the storage was submitted", alias="Timestamp"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOWarehouse(BaseModel):
    """Warehouse from the /sites/warehouses/{UserName} endpoint."""

    warehouse_id: str = Field(..., description="Warehouse ID", alias="WarehouseId")
    store_id: str = Field(..., description="Store ID", alias="StoreId")
    units: int = Field(..., description="Number of units", alias="Units")
    weight_capacity: float = Field(
        ..., description="Weight capacity", alias="WeightCapacity"
    )
    volume_capacity: float = Field(
        ..., description="Volume capacity", alias="VolumeCapacity"
    )
    next_payment_timestamp_epoch_ms: int = Field(
        ...,
        description="Next payment timestamp in milliseconds",
        alias="NextPaymentTimestampEpochMs",
    )
    fee_amount: float = Field(..., description="Fee amount", alias="FeeAmount")
    fee_currency: str = Field(..., description="Fee currency", alias="FeeCurrency")
    fee_collector_id: Optional[str] = Field(
        None, description="Fee collector ID", alias="FeeCollectorId"
    )
    fee_collector_name: Optional[str] = Field(
        None, description="Fee collector name", alias="FeeCollectorName"
    )
    fee_collector_code: Optional[str] = Field(
        None, description="Fee collector code", alias="FeeCollectorCode"
    )
    location_name: str = Field(..., description="Location name", alias="LocationName")
    location_natural_id: str = Field(
        ..., description="Location natural ID", alias="LocationNaturalId"
    )
    user_name_submitted: str = Field(
        ...,
        description="Username who submitted the warehouse",
        alias="UserNameSubmitted",
    )
    timestamp: datetime = Field(
        ..., description="Timestamp when the warehouse was submitted", alias="Timestamp"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOPlanetResource(BaseModel):
    """Planet resource from the /planet/allplanets/full endpoint."""

    material_id: str = Field(..., description="Material ID", alias="MaterialId")
    resource_type: str = Field(..., description="Resource type", alias="ResourceType")
    factor: float = Field(..., description="Resource factor", alias="Factor")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOBuildingRequirement(BaseModel):
    """Building requirement from the /planet/allplanets/full endpoint."""

    material_name: str = Field(..., description="Material name", alias="MaterialName")
    material_id: str = Field(..., description="Material ID", alias="MaterialId")
    material_ticker: str = Field(
        ..., description="Material ticker", alias="MaterialTicker"
    )
    material_category: str = Field(
        ..., description="Material category", alias="MaterialCategory"
    )
    material_amount: int = Field(
        ..., description="Material amount", alias="MaterialAmount"
    )
    material_weight: float = Field(
        ..., description="Material weight", alias="MaterialWeight"
    )
    material_volume: float = Field(
        ..., description="Material volume", alias="MaterialVolume"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOProductionFee(BaseModel):
    """Production fee from the /planet/allplanets/full endpoint."""

    category: str = Field(..., description="Fee category", alias="Category")
    workforce_level: str = Field(
        ..., description="Workforce level", alias="WorkforceLevel"
    )
    fee_amount: int = Field(..., description="Fee amount", alias="FeeAmount")
    fee_currency: Optional[str] = Field(
        None, description="Fee currency", alias="FeeCurrency"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOCOGCProgram(BaseModel):
    """COGC program from the /planet/allplanets/full endpoint."""

    program_type: Optional[str] = Field(
        None, description="Program type", alias="ProgramType"
    )
    start_epoch_ms: datetime = Field(
        ..., description="Start time in milliseconds", alias="StartEpochMs"
    )
    end_epoch_ms: datetime = Field(
        ..., description="End time in milliseconds", alias="EndEpochMs"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOCOGCVote(BaseModel):
    """COGC vote from the /planet/allplanets/full endpoint."""

    company_name: str = Field(..., description="Company name", alias="CompanyName")
    company_code: Optional[str] = Field(
        None, description="Company code", alias="CompanyCode"
    )
    influence: float = Field(..., description="Influence amount", alias="Influence")
    vote_type: str = Field(..., description="Vote type", alias="VoteType")
    vote_time_epoch_ms: datetime = Field(
        ..., description="Vote time in milliseconds", alias="VoteTimeEpochMs"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOPlanetFull(FIOPlanet):
    """Full planet information from the /planet/allplanets/full endpoint."""

    resources: List[FIOPlanetResource] = Field(
        ..., description="List of planet resources", alias="Resources"
    )
    build_requirements: List[FIOBuildingRequirement] = Field(
        ..., description="List of building requirements", alias="BuildRequirements"
    )
    production_fees: List[FIOProductionFee] = Field(
        ..., description="List of production fees", alias="ProductionFees"
    )
    cogc_programs: List[FIOCOGCProgram] = Field(
        ..., description="List of COGC programs", alias="COGCPrograms"
    )
    cogc_votes: List[FIOCOGCVote] = Field(
        ..., description="List of COGC votes", alias="COGCVotes"
    )
    planet_id: str = Field(..., description="Planet ID", alias="PlanetId")
    namer: Optional[str] = Field(None, description="Planet namer", alias="Namer")
    naming_data_epoch_ms: int = Field(
        ...,
        description="Naming data timestamp in milliseconds",
        alias="NamingDataEpochMs",
    )
    nameable: bool = Field(
        ..., description="Whether the planet is nameable", alias="Nameable"
    )
    system_id: str = Field(..., description="System ID", alias="SystemId")
    gravity: float = Field(..., description="Planet gravity", alias="Gravity")
    magnetic_field: float = Field(
        ..., description="Planet magnetic field", alias="MagneticField"
    )
    mass: float = Field(..., description="Planet mass", alias="Mass")
    mass_earth: float = Field(
        ..., description="Planet mass in Earth masses", alias="MassEarth"
    )
    orbit_semi_major_axis: int = Field(
        ..., description="Orbit semi-major axis", alias="OrbitSemiMajorAxis"
    )
    orbit_eccentricity: float = Field(
        ..., description="Orbit eccentricity", alias="OrbitEccentricity"
    )
    orbit_inclination: float = Field(
        ..., description="Orbit inclination", alias="OrbitInclination"
    )
    orbit_right_ascension: int = Field(
        ..., description="Orbit right ascension", alias="OrbitRightAscension"
    )
    orbit_periapsis: int = Field(
        ..., description="Orbit periapsis", alias="OrbitPeriapsis"
    )
    orbit_index: int = Field(..., description="Orbit index", alias="OrbitIndex")
    pressure: float = Field(..., description="Planet pressure", alias="Pressure")
    radiation: float = Field(..., description="Planet radiation", alias="Radiation")
    radius: float = Field(..., description="Planet radius", alias="Radius")
    sunlight: float = Field(..., description="Planet sunlight", alias="Sunlight")
    surface: bool = Field(
        ..., description="Whether the planet has a surface", alias="Surface"
    )
    temperature: float = Field(
        ..., description="Planet temperature", alias="Temperature"
    )
    fertility: float = Field(..., description="Planet fertility", alias="Fertility")
    has_local_market: bool = Field(
        ..., description="Whether the planet has a local market", alias="HasLocalMarket"
    )
    has_chamber_of_commerce: bool = Field(
        ...,
        description="Whether the planet has a chamber of commerce",
        alias="HasChamberOfCommerce",
    )
    has_warehouse: bool = Field(
        ..., description="Whether the planet has a warehouse", alias="HasWarehouse"
    )
    has_administration_center: bool = Field(
        ...,
        description="Whether the planet has an administration center",
        alias="HasAdministrationCenter",
    )
    has_shipyard: bool = Field(
        ..., description="Whether the planet has a shipyard", alias="HasShipyard"
    )
    faction_code: Optional[str] = Field(
        None, description="Faction code", alias="FactionCode"
    )
    faction_name: Optional[str] = Field(
        None, description="Faction name", alias="FactionName"
    )
    governor_id: Optional[str] = Field(
        None, description="Governor ID", alias="GovernorId"
    )
    governor_user_name: Optional[str] = Field(
        None, description="Governor username", alias="GovernorUserName"
    )
    governor_corporation_id: Optional[str] = Field(
        None, description="Governor corporation ID", alias="GovernorCorporationId"
    )
    governor_corporation_name: Optional[str] = Field(
        None, description="Governor corporation name", alias="GovernorCorporationName"
    )
    governor_corporation_code: Optional[str] = Field(
        None, description="Governor corporation code", alias="GovernorCorporationCode"
    )
    currency_name: Optional[str] = Field(
        None, description="Currency name", alias="CurrencyName"
    )
    currency_code: Optional[str] = Field(
        None, description="Currency code", alias="CurrencyCode"
    )
    collector_id: Optional[str] = Field(
        None, description="Collector ID", alias="CollectorId"
    )
    collector_name: Optional[str] = Field(
        None, description="Collector name", alias="CollectorName"
    )
    collector_code: Optional[str] = Field(
        None, description="Collector code", alias="CollectorCode"
    )
    base_local_market_fee: int = Field(
        ..., description="Base local market fee", alias="BaseLocalMarketFee"
    )
    local_market_fee_factor: int = Field(
        ..., description="Local market fee factor", alias="LocalMarketFeeFactor"
    )
    warehouse_fee: int = Field(..., description="Warehouse fee", alias="WarehouseFee")
    population_id: Optional[str] = Field(
        None, description="Population ID", alias="PopulationId"
    )
    cogc_program_status: Optional[str] = Field(
        None, description="COGC program status", alias="COGCProgramStatus"
    )
    planet_tier: int = Field(..., description="Planet tier", alias="PlanetTier")
    timestamp: datetime = Field(
        ..., description="Timestamp when the planet was submitted", alias="Timestamp"
    )
    distance_results: Optional[List[int]] = Field(
        None, description="Distance results", alias="DistanceResults"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FIOAdBase(BaseModel):
    ContractNaturalId: int
    PlanetId: str = Field(min_length=32)
    PlanetNaturalId: str
    PlanetName: str
    CreatorCompanyId: str = Field(min_length=32)
    CreatorCompanyName: str
    CreatorCompanyCode: str
    DeliveryTime: int
    CreationTimeEpochMs: datetime
    ExpiryTimeEpochMs: datetime
    MinimumRating: str


class FIOAd(FIOAdBase):
    MaterialId: str = Field(min_length=32)
    MaterialName: str
    MaterialTicker: str
    MaterialCategory: str = Field(min_length=32)
    MaterialWeight: float
    MaterialVolume: float
    MaterialAmount: int
    Price: float
    PriceCurrency: str


class FIOShippingAd(FIOAdBase):
    OriginPlanetId: str = Field(min_length=32)
    OriginPlanetNaturalId: str
    OriginPlanetName: str
    DestinationPlanetId: str = Field(min_length=32)
    DestinationPlanetNaturalId: str
    DestinationPlanetName: str
    CargoWeight: float
    CargoVolume: float
    PayoutPrice: int
    PayoutCurrency: str


class FIOLocalMarketAds(BaseModel):
    BuyingAds: List[FIOAd]
    SellingAds: List[FIOAd]
    ShippingAds: List[FIOShippingAd]


class FIOLocalMarketAdList(RootModel[List[FIOAd]]):
    def __iter__(self):
        return iter(self.root)


class FIOLocalMarketShippingAdList(RootModel[List[FIOShippingAd]]):
    def __iter__(self):
        return iter(self.root)
