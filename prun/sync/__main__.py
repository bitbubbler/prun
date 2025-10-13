import logging

from fast_depends import Depends
from fio_wrapper import FIO
from sqlmodel import Session, delete

from prun.deps import get_fio, get_session
from prun.models import (
    Building,
    BuildingCost,
    COGCProgram,
    COGCVote,
    Company,
    Exchange,
    ExchangePrice,
    Item,
    LocalMarketAd,
    Planet,
    PlanetBuildingRequirement,
    PlanetProductionFee,
    PlanetResource,
    Recipe,
    RecipeInput,
    RecipeOutput,
    Site,
    SiteBuilding,
    SiteBuildingMaterial,
    Storage,
    StorageItem,
    System,
    SystemConnection,
    Warehouse,
    WorkforceNeed,
)

logger = logging.getLogger(__name__)


def update_planet_localmarket_ads(
    planet: Planet,
    fio: FIO = Depends(get_fio),
    session: Session = Depends(get_session),
) -> Planet:
    """Update the database with the latest local market ads for a given planet using the FIO API."""
    logger.info(f"Updating local market ads for planet {planet.natural_id}")

    planet = session.merge(planet)

    # remove all existing ads for this planet
    session.exec(delete(LocalMarketAd).where(LocalMarketAd.planet == planet))

    # get the new ads
    fio_ads = fio.LocalMarket.planet(planet.natural_id)

    for fio_ad in fio_ads.BuyingAds:
        creator_company = Company.get_or_create(fio_ad.CreatorCompanyId)
        ad = LocalMarketAd(
            ad_type="buy",
            contract_natural_id=fio_ad.ContractNaturalId,
            planet=planet,
            creator_company=creator_company,
            delivery_time=fio_ad.DeliveryTime,
            creation_time_epoch_ms=fio_ad.CreationTimeEpochMs,
            expiry_time_epoch_ms=fio_ad.ExpiryTimeEpochMs,
            minimum_rating=fio_ad.MinimumRating,
            material_id=fio_ad.MaterialId,
            material_name=fio_ad.MaterialName,
            material_ticker=fio_ad.MaterialTicker,
            material_category=fio_ad.MaterialCategory,
            material_weight=fio_ad.MaterialWeight,
            material_volume=fio_ad.MaterialVolume,
            material_amount=fio_ad.MaterialAmount,
            price=fio_ad.Price,
            price_currency=fio_ad.PriceCurrency,
        )
    for fio_ad in fio_ads.SellingAds:
        ad = LocalMarketAd(
            ad_type="sell",
            contract_natural_id=fio_ad.ContractNaturalId,
            planet_id=fio_ad.PlanetId,
            planet_natural_id=fio_ad.PlanetNaturalId,
            planet_name=fio_ad.PlanetName,
            creator_company_id=fio_ad.CreatorCompanyId,
            creator_company_name=fio_ad.CreatorCompanyName,
            creator_company_code=fio_ad.CreatorCompanyCode,
            delivery_time=fio_ad.DeliveryTime,
            creation_time_epoch_ms=fio_ad.CreationTimeEpochMs,
            expiry_time_epoch_ms=fio_ad.ExpiryTimeEpochMs,
            minimum_rating=fio_ad.MinimumRating,
            material_id=fio_ad.MaterialId,
            material_name=fio_ad.MaterialName,
            material_ticker=fio_ad.MaterialTicker,
            material_category=fio_ad.MaterialCategory,
            material_weight=fio_ad.MaterialWeight,
            material_volume=fio_ad.MaterialVolume,
            material_amount=fio_ad.MaterialAmount,
            price=fio_ad.Price,
            price_currency=fio_ad.PriceCurrency,
        )
        session.add(ad)
    for fio_ad in fio_ads.ShippingAds:
        ad = LocalMarketAd(
            LocalMarketAd(
                ad_type="shipping",
                contract_natural_id=fio_ad.ContractNaturalId,
                planet_id=fio_ad.PlanetId,
                planet_natural_id=fio_ad.PlanetNaturalId,
                planet_name=fio_ad.PlanetName,
                creator_company_id=fio_ad.CreatorCompanyId,
                creator_company_name=fio_ad.CreatorCompanyName,
                creator_company_code=fio_ad.CreatorCompanyCode,
                delivery_time=fio_ad.DeliveryTime,
                creation_time_epoch_ms=fio_ad.CreationTimeEpochMs,
                expiry_time_epoch_ms=fio_ad.ExpiryTimeEpochMs,
                minimum_rating=fio_ad.MinimumRating,
                origin_planet_id=fio_ad.OriginPlanetId,
                origin_planet_natural_id=fio_ad.OriginPlanetNaturalId,
                origin_planet_name=fio_ad.OriginPlanetName,
                destination_planet_id=fio_ad.DestinationPlanetId,
                destination_planet_natural_id=fio_ad.DestinationPlanetNaturalId,
                destination_planet_name=fio_ad.DestinationPlanetName,
                cargo_weight=fio_ad.CargoWeight,
                cargo_volume=fio_ad.CargoVolume,
                payout_price=fio_ad.PayoutPrice,
                payout_currency=fio_ad.PayoutCurrency,
            )
        )
        session.add(ad)

    logger.info(f"Updated {len(ads)} local market ads for planet {planet_natural_id}")

    return planet


def sync_sites(
    fio_client: FIOClientInterface,
    site_repository: SiteRepositoryInterface,
    character_id: str,
) -> None:
    """Sync sites from the FIO API to the database.

    Args:
        fio_client: FIO API client
        site_repository: Repository for site-related database operations
        character_id: Character ID to sync sites for

    Raises:
        Exception: If there's an error syncing sites
    """
    try:
        sites = fio_client.get_sites(character_id)

        # Get existing sites for comparison
        existing_sites = {
            site.site_id: site for site in site_repository.get_all_sites()
        }

        for fio_site in sites:
            site: Site
            # Update or create site
            if fio_site.site_id in existing_sites:
                # Update existing site
                site = existing_sites[fio_site.site_id]
                site.invested_permits = fio_site.invested_permits
                site.maximum_permits = fio_site.maximum_permits
                site.planet_natural_id = fio_site.planet_identifier
            else:
                site = Site.model_validate(
                    {
                        "site_id": fio_site.site_id,
                        "invested_permits": fio_site.invested_permits,
                        "maximum_permits": fio_site.maximum_permits,
                        "planet_natural_id": fio_site.planet_identifier,
                    }
                )
                site_repository.create_site(site)

            # Delete existing buildings and materials for this site
            site_repository.delete_site_buildings(site)

            # Create new buildings and materials
            for fio_building in site.buildings:
                building = SiteBuilding.model_validate(
                    {
                        "site_building_id": fio_building.site_building_id,
                        "building_created": fio_building.building_created,
                        "building_last_repair": fio_building.building_last_repair,
                        "condition": fio_building.condition,
                        "site_id": site.site_id,
                        "building_symbol": fio_building.building_symbol,
                        "materials": [
                            SiteBuildingMaterial.model_validate(
                                {
                                    "amount": fio_material.amount,
                                    "material_type": fio_material.material_type,
                                    "item_symbol": fio_material.item_symbol,
                                }
                            )
                            for fio_material in fio_building.materials
                        ],
                    }
                )
                site_repository.create_site_building(building)

    except Exception as e:
        logger.error(f"Error syncing sites for character {character_id}: {str(e)}")
        raise


def sync_storage(
    fio_client: FIOClientInterface,
    storage_repository: StorageRepositoryInterface,
    character_id: str,
) -> None:
    """Sync storage data from the FIO API to the database.

    Args:
        fio_client: FIO API client
        storage_repository: Repository for storage-related database operations
        character_id: Character ID to sync storage for
    """
    storage_data = fio_client.get_storage(character_id)

    # Delete existing storage data
    storage_repository.delete_storage()

    # Create new storage facilities
    for fio_storage in storage_data:
        # Create storage facility
        storage = Storage.model_validate(
            {
                "storage_id": fio_storage.storage_id,
                "addressable_id": fio_storage.addressable_id,
                "name": fio_storage.name,
                "type": fio_storage.type,
                "weight_capacity": fio_storage.weight_capacity,
                "volume_capacity": fio_storage.volume_capacity,
                "site_id": fio_storage.addressable_id,
                "warehouse_id": fio_storage.storage_id,  # TODO: Check if this is correct
            }
        )

        for fio_storage_item in fio_storage.storage_items:
            storage.stored_items.append(
                StorageItem.model_validate(
                    {
                        "storage_id": fio_storage.storage_id,
                        "item_symbol": fio_storage_item.material_ticker,
                        "amount": fio_storage_item.material_amount,
                        "type": fio_storage_item.type,
                    }
                )
            )

        storage_repository.create_storage(storage)


def sync_warehouses(
    fio_client: FIOClientInterface,
    warehouse_repository: WarehouseRepositoryInterface,
    username: str,
) -> None:
    """Synchronize warehouses from the API."""
    warehouses = fio_client.get_warehouses(username)
    # Get all existing warehouses
    existing_warehouses = {
        warehouse.warehouse_id: warehouse
        for warehouse in warehouse_repository.get_all_warehouses()
    }

    # Process each warehouse from API
    for fio_warehouse in warehouses:
        # Check if warehouse exists
        existing_warehouse = existing_warehouses.get(fio_warehouse.warehouse_id)
        if existing_warehouse:
            # Update existing warehouse
            existing_warehouse.units = fio_warehouse.units
            existing_warehouse.weight_capacity = fio_warehouse.weight_capacity
            existing_warehouse.volume_capacity = fio_warehouse.volume_capacity
            existing_warehouse.next_payment_timestamp_epoch_ms = (
                fio_warehouse.next_payment_timestamp_epoch_ms
            )
            existing_warehouse.fee_amount = fio_warehouse.fee_amount
            existing_warehouse.fee_currency = fio_warehouse.fee_currency
            existing_warehouse.fee_collector_id = fio_warehouse.fee_collector_id
            existing_warehouse.fee_collector_name = fio_warehouse.fee_collector_name
            existing_warehouse.fee_collector_code = fio_warehouse.fee_collector_code
            existing_warehouse.location_name = fio_warehouse.location_name
            existing_warehouse.location_natural_id = fio_warehouse.location_natural_id
        else:
            # Create new warehouse
            warehouse = Warehouse.model_validate(
                {
                    "warehouse_id": fio_warehouse.warehouse_id,
                    "units": fio_warehouse.units,
                    "weight_capacity": fio_warehouse.weight_capacity,
                    "volume_capacity": fio_warehouse.volume_capacity,
                    "next_payment_timestamp_epoch_ms": fio_warehouse.next_payment_timestamp_epoch_ms,
                    "fee_amount": fio_warehouse.fee_amount,
                    "fee_currency": fio_warehouse.fee_currency,
                    "fee_collector_id": fio_warehouse.fee_collector_id,
                    "fee_collector_name": fio_warehouse.fee_collector_name,
                    "fee_collector_code": fio_warehouse.fee_collector_code,
                    "location_name": fio_warehouse.location_name,
                    "location_natural_id": fio_warehouse.location_natural_id,
                }
            )
            warehouse_repository.create_warehouse(warehouse)


def sync_workforce_needs(
    fio_client: FIOClientInterface,
    workforce_repository: WorkforceRepositoryInterface,
) -> None:
    """Sync workforce needs from the FIO API to the database.

    Args:
        fio_client: FIO API client
        workforce_repository: Repository for workforce-related database operations
    """
    fio_workforce_needs = fio_client.get_workforce_needs()
    # Delete existing workforce needs
    workforce_repository.delete_workforce_needs()

    # Create new workforce needs
    for fio_workforce_need in fio_workforce_needs:
        for fio_need in fio_workforce_need.needs:
            workforce_need = WorkforceNeed.model_validate(
                {
                    "workforce_type": fio_workforce_need.workforce_type,
                    "item_symbol": fio_need.material_ticker,
                    "amount_per_100_workers_per_day": fio_need.amount,
                }
            )
            workforce_repository.create_workforce_need(workforce_need)


def sync_planets(
    fio_client: FIOClientInterface,
    system_repository: SystemRepositoryInterface,
) -> None:
    """Sync planets from the FIO API to the database.

    This method syncs planet information and all related data (resources,
    building requirements, production fees, COGC programs, and votes) in a single
    call to the FIO API.

    Args:
        fio_client: FIO API client
        system_repository: Repository for system-related database operations

    Raises:
        ValueError: If a planet's system cannot be found in the database
    """
    planets = fio_client.get_planets_full()
    for fio_planet in planets:
        # Extract system natural_id from planet natural_id
        # Format is like "PG-241h", "NL-534a", "PD-175d", "MG-630g" etc
        # The system ID is everything except the last character
        system_natural_id = fio_planet.planet_natural_id[:-1]

        # Get the system
        system = system_repository.get_system_by_natural_id(system_natural_id)
        if not system:
            raise ValueError(
                f"System {system_natural_id} for planet {fio_planet.planet_natural_id} "
                f"not found in database. Please sync systems first."
            )

        # Check if planet already exists
        existing_planet = system_repository.get_planet(fio_planet.planet_natural_id)
        if not existing_planet:
            planet = Planet.model_validate(
                {
                    "natural_id": fio_planet.planet_natural_id,
                    "name": fio_planet.planet_name,
                    "system_id": system.system_id,
                    "planet_id": fio_planet.planet_id,
                    "gravity": fio_planet.gravity,
                    "magnetic_field": fio_planet.magnetic_field,
                    "mass": fio_planet.mass,
                    "mass_earth": fio_planet.mass_earth,
                    "orbit_semi_major_axis": fio_planet.orbit_semi_major_axis,
                    "orbit_eccentricity": fio_planet.orbit_eccentricity,
                    "orbit_inclination": fio_planet.orbit_inclination,
                    "orbit_right_ascension": fio_planet.orbit_right_ascension,
                    "orbit_periapsis": fio_planet.orbit_periapsis,
                    "orbit_index": fio_planet.orbit_index,
                    "pressure": fio_planet.pressure,
                    "radiation": fio_planet.radiation,
                    "radius": fio_planet.radius,
                    "sunlight": fio_planet.sunlight,
                    "surface": fio_planet.surface,
                    "temperature": fio_planet.temperature,
                    "fertility": fio_planet.fertility,
                    "has_local_market": fio_planet.has_local_market,
                    "has_chamber_of_commerce": fio_planet.has_chamber_of_commerce,
                    "has_warehouse": fio_planet.has_warehouse,
                    "has_administration_center": fio_planet.has_administration_center,
                    "has_shipyard": fio_planet.has_shipyard,
                    "faction_code": fio_planet.faction_code,
                    "faction_name": fio_planet.faction_name,
                    "governor_id": fio_planet.governor_id,
                    "governor_user_name": fio_planet.governor_user_name,
                    "governor_corporation_id": fio_planet.governor_corporation_id,
                    "governor_corporation_name": fio_planet.governor_corporation_name,
                    "governor_corporation_code": fio_planet.governor_corporation_code,
                    "currency_name": fio_planet.currency_name,
                    "currency_code": fio_planet.currency_code,
                    "collector_id": fio_planet.collector_id,
                    "collector_name": fio_planet.collector_name,
                    "collector_code": fio_planet.collector_code,
                    "base_local_market_fee": fio_planet.base_local_market_fee,
                    "local_market_fee_factor": fio_planet.local_market_fee_factor,
                    "warehouse_fee": fio_planet.warehouse_fee,
                    "population_id": fio_planet.population_id,
                    "cogc_program_status": fio_planet.cogc_program_status,
                    "planet_tier": fio_planet.planet_tier,
                    "timestamp": fio_planet.timestamp,
                }
            )
            system_repository.create_planet(planet)
        else:
            planet = existing_planet
            # Update existing planet with new data
            existing_planet.name = fio_planet.planet_name
            existing_planet.system_id = system.system_id
            existing_planet.planet_id = fio_planet.planet_id
            existing_planet.gravity = fio_planet.gravity
            existing_planet.magnetic_field = fio_planet.magnetic_field
            existing_planet.mass = fio_planet.mass
            existing_planet.mass_earth = fio_planet.mass_earth
            existing_planet.orbit_semi_major_axis = fio_planet.orbit_semi_major_axis
            existing_planet.orbit_eccentricity = fio_planet.orbit_eccentricity
            existing_planet.orbit_inclination = fio_planet.orbit_inclination
            existing_planet.orbit_right_ascension = fio_planet.orbit_right_ascension
            existing_planet.orbit_periapsis = fio_planet.orbit_periapsis
            existing_planet.orbit_index = fio_planet.orbit_index
            existing_planet.pressure = fio_planet.pressure
            existing_planet.radiation = fio_planet.radiation
            existing_planet.radius = fio_planet.radius
            existing_planet.sunlight = fio_planet.sunlight
            existing_planet.surface = fio_planet.surface
            existing_planet.temperature = fio_planet.temperature
            existing_planet.fertility = fio_planet.fertility
            existing_planet.has_local_market = fio_planet.has_local_market
            existing_planet.has_chamber_of_commerce = fio_planet.has_chamber_of_commerce
            existing_planet.has_warehouse = fio_planet.has_warehouse
            existing_planet.has_administration_center = (
                fio_planet.has_administration_center
            )
            existing_planet.has_shipyard = fio_planet.has_shipyard
            existing_planet.faction_code = fio_planet.faction_code
            existing_planet.faction_name = fio_planet.faction_name
            existing_planet.governor_id = fio_planet.governor_id
            existing_planet.governor_user_name = fio_planet.governor_user_name
            existing_planet.governor_corporation_id = fio_planet.governor_corporation_id
            existing_planet.governor_corporation_name = (
                fio_planet.governor_corporation_name
            )
            existing_planet.governor_corporation_code = (
                fio_planet.governor_corporation_code
            )
            existing_planet.currency_name = fio_planet.currency_name
            existing_planet.currency_code = fio_planet.currency_code
            existing_planet.collector_id = fio_planet.collector_id
            existing_planet.collector_name = fio_planet.collector_name
            existing_planet.collector_code = fio_planet.collector_code
            existing_planet.base_local_market_fee = fio_planet.base_local_market_fee
            existing_planet.local_market_fee_factor = fio_planet.local_market_fee_factor
            existing_planet.warehouse_fee = fio_planet.warehouse_fee
            existing_planet.population_id = fio_planet.population_id
            existing_planet.cogc_program_status = fio_planet.cogc_program_status
            existing_planet.planet_tier = fio_planet.planet_tier
            existing_planet.timestamp = fio_planet.timestamp
            system_repository.update_planet(existing_planet)

        # Delete existing related data
        system_repository.delete_planet_resources(planet)
        system_repository.delete_planet_building_requirements(planet)
        system_repository.delete_planet_production_fees(planet)
        system_repository.delete_planet_cogc_programs(planet)
        system_repository.delete_planet_cogc_votes(planet)

        # Create new resources
        for resource in fio_planet.resources:
            planet_resource = PlanetResource(
                planet_natural_id=planet.natural_id,
                material_id=resource.material_id,
                resource_type=resource.resource_type,
                factor=resource.factor,
            )
            system_repository.create_planet_resource(planet_resource)

        # Create new building requirements
        for requirement in fio_planet.build_requirements:
            planet_requirement = PlanetBuildingRequirement(
                planet_natural_id=planet.natural_id,
                item_symbol=requirement.material_id,
                amount=requirement.material_amount,
                weight=requirement.material_weight,
                volume=requirement.material_volume,
            )
            system_repository.create_planet_building_requirement(planet_requirement)

        # Create new production fees
        for fee in fio_planet.production_fees:
            planet_fee = PlanetProductionFee(
                planet_natural_id=planet.natural_id,
                category=fee.category,
                workforce_level=fee.workforce_level,
                fee_amount=fee.fee_amount,
                fee_currency=fee.fee_currency,
            )
            system_repository.create_planet_production_fee(planet_fee)

        # Create new COGC programs
        for program in fio_planet.cogc_programs:
            cogc_program = COGCProgram(
                planet_natural_id=planet.natural_id,
                program_type=program.program_type,
                start_epoch_ms=program.start_epoch_ms,
                end_epoch_ms=program.end_epoch_ms,
            )
            system_repository.create_cogc_program(cogc_program)

        # Create new COGC votes
        for vote in fio_planet.cogc_votes:
            cogc_vote = COGCVote(
                planet_natural_id=planet.natural_id,
                company_name=vote.company_name,
                company_code=vote.company_code,
                influence=vote.influence,
                vote_type=vote.vote_type,
                vote_time_epoch_ms=vote.vote_time_epoch_ms,
            )
            system_repository.create_cogc_vote(cogc_vote)


def sync_recipes(
    fio_client: FIOClientInterface,
    recipe_repository: RecipeRepositoryInterface,
) -> None:
    """Sync recipes from the FIO API to the database.

    Args:
        fio_client: FIO API client
        recipe_repository: Repository for recipe-related database operations

    Raises:
        Exception: If there's an error syncing recipes
    """
    try:
        recipes = fio_client.get_recipes()
        for fio_recipe in recipes:
            # Check if recipe already exists
            if not recipe_repository.get_recipe(fio_recipe.standard_recipe_name):
                recipe = Recipe.model_validate(
                    {
                        "symbol": fio_recipe.standard_recipe_name,
                        "building_symbol": fio_recipe.building_ticker,
                        "time_ms": fio_recipe.time_ms,
                    }
                )

                recipe.inputs = [
                    RecipeInput.model_validate(
                        {
                            "recipe_symbol": recipe.symbol,
                            "item_symbol": input.ticker,
                            "quantity": float(input.amount),
                        }
                    )
                    for input in fio_recipe.inputs
                ]

                recipe.outputs = [
                    RecipeOutput.model_validate(
                        {
                            "recipe_symbol": recipe.symbol,
                            "item_symbol": output.ticker,
                            "quantity": float(output.amount),
                        }
                    )
                    for output in fio_recipe.outputs
                ]

                # Create recipe with its inputs and output
                recipe_repository.create_recipe(recipe)
    except Exception as e:
        logger.error(f"Error syncing recipes: {str(e)}")
        raise


def sync_prices(
    fio_client: FIOClientInterface,
    exchange_repository: ExchangeRepositoryInterface,
) -> None:
    """Sync exchange prices from the FIO API to the database.

    Args:
        fio_client: FIO API client
        exchange_repository: Repository for exchange-related database operations
    """
    prices = fio_client.get_prices()

    # Delete existing prices
    exchange_repository.delete_exchange_prices()

    # Create new prices
    for fio_price in prices:
        exchange_price = ExchangePrice.model_validate(
            {
                "timestamp": fio_price.timestamp,
                "mm_buy": fio_price.mm_buy,
                "mm_sell": fio_price.mm_sell,
                "average_price": fio_price.average_price,
                "ask_amount": fio_price.ask_amount,
                "ask_price": fio_price.ask_price,
                "ask_available": fio_price.ask_available,
                "bid_amount": fio_price.bid_amount,
                "bid_price": fio_price.bid_price,
                "bid_available": fio_price.bid_available,
                "item_symbol": fio_price.material_ticker,
                "exchange_code": fio_price.exchange,
            }
        )
        exchange_repository.create_exchange_price(exchange_price)


def sync_comex_exchanges(
    fio_client: FIOClientInterface,
    exchange_repository: ExchangeRepositoryInterface,
) -> None:
    """Sync commodity exchanges from the FIO API to the database.

    Args:
        fio_client: FIO API client
        exchange_repository: Repository for exchange-related database operations
    """
    exchanges = fio_client.get_comex_exchanges()

    # Get existing exchanges for comparison
    existing_exchanges = {
        exchange.comex_exchange_id: exchange
        for exchange in exchange_repository.get_all_comex_exchanges()
    }

    for fio_exchange in exchanges:
        # Check if exchange already exists
        if fio_exchange.comex_exchange_id in existing_exchanges:
            # Update existing exchange
            exchange = existing_exchanges[fio_exchange.comex_exchange_id]
            exchange.exchange_name = fio_exchange.exchange_name
            exchange.exchange_code = fio_exchange.exchange_code
            exchange.exchange_operator_id = fio_exchange.exchange_operator_id
            exchange.exchange_operator_code = fio_exchange.exchange_operator_code
            exchange.exchange_operator_name = fio_exchange.exchange_operator_name
            exchange.currency_numeric_code = fio_exchange.currency_numeric_code
            exchange.currency_code = fio_exchange.currency_code
            exchange.currency_name = fio_exchange.currency_name
            exchange.currency_decimals = fio_exchange.currency_decimals
            exchange.location_id = fio_exchange.location_id
            exchange.location_name = fio_exchange.location_name
            exchange.location_natural_id = fio_exchange.location_natural_id
        else:
            # Create new exchange
            comex_exchange = Exchange.model_validate(
                {
                    "comex_exchange_id": fio_exchange.comex_exchange_id,
                    "exchange_name": fio_exchange.exchange_name,
                    "exchange_code": fio_exchange.exchange_code,
                    "exchange_operator_id": fio_exchange.exchange_operator_id,
                    "exchange_operator_code": fio_exchange.exchange_operator_code,
                    "exchange_operator_name": fio_exchange.exchange_operator_name,
                    "currency_numeric_code": fio_exchange.currency_numeric_code,
                    "currency_code": fio_exchange.currency_code,
                    "currency_name": fio_exchange.currency_name,
                    "currency_decimals": fio_exchange.currency_decimals,
                    "location_id": fio_exchange.location_id,
                    "location_name": fio_exchange.location_name,
                    "location_natural_id": fio_exchange.location_natural_id,
                }
            )
            exchange_repository.create_comex_exchange(comex_exchange)


def sync_buildings(
    fio_client: FIOClientInterface,
    building_repository: BuildingRepositoryInterface,
) -> None:
    """Sync buildings from the FIO API to the database.

    Args:
        fio_client: FIO API client
        building_repository: Repository for building-related database operations
    """
    buildings = fio_client.get_buildings()

    for fio_building in buildings:
        # Check if building already exists
        if not building_repository.get_building(fio_building.ticker):
            building = Building.model_validate(
                {
                    "symbol": fio_building.ticker,
                    "name": fio_building.name,
                    "expertise": fio_building.expertise,
                    "pioneers": fio_building.pioneers,
                    "settlers": fio_building.settlers,
                    "technicians": fio_building.technicians,
                    "engineers": fio_building.engineers,
                    "scientists": fio_building.scientists,
                    "area_cost": fio_building.area_cost,
                }
            )

            building.building_costs = [
                BuildingCost.model_validate(
                    {
                        "building_symbol": building.symbol,
                        "item_symbol": cost.commodity_ticker,
                        "amount": cost.amount,
                    }
                )
                for cost in fio_building.building_costs
            ]

            # Create building with construction costs
            building_repository.create_building(building)


def sync_systems(
    fio_client: FIOClientInterface,
    system_repository: SystemRepositoryInterface,
) -> None:
    """Sync systems from the FIO API to the database.

    Args:
        fio_client: FIO API client
        system_repository: Repository for system-related database operations
    """
    systems = fio_client.get_systems()
    for fio_system in systems:
        # Check if system already exists
        if not system_repository.get_system(fio_system.system_id):
            # Create system with connections
            system = System.model_validate(
                {
                    "system_id": fio_system.system_id,
                    "name": fio_system.name,
                    "natural_id": fio_system.natural_id,
                    "type": fio_system.type,
                    "position_x": float(fio_system.position_x),
                    "position_y": float(fio_system.position_y),
                    "position_z": float(fio_system.position_z),
                    "sector_id": fio_system.sector_id,
                    "sub_sector_id": fio_system.sub_sector_id,
                }
            )

            system.connections = [
                SystemConnection.model_validate(
                    {
                        "connecting_id": conn.connecting_id,
                        "system_connection_id": conn.system_connection_id,
                        "system_id": system.system_id,
                    }
                )
                for conn in fio_system.connections
            ]

            system_repository.create_system(system)


def sync_materials(
    fio_client: FIOClientInterface,
    item_repository: ItemRepositoryInterface,
) -> None:
    """Sync materials from the FIO API to the database.

    Args:
        fio_client: FIO API client
        item_repository: Repository for item-related database operations
    """
    materials = fio_client.get_all_materials()
    for fio_material in materials:
        # Check if item already exists
        if not item_repository.get_item(fio_material.ticker):
            item = Item.model_validate(
                {
                    "material_id": fio_material.material_id,
                    "symbol": fio_material.ticker,
                    "name": fio_material.name,
                    "category": fio_material.category,
                    "weight": float(fio_material.weight),
                    "volume": float(fio_material.volume),
                }
            )
            item_repository.create_item(item)
