import logging
from typing import Callable, Optional, Sequence, ContextManager
from datetime import datetime

from sqlmodel import Session, select, desc, and_

from prun.models.db_models import (
    Item,
    Recipe,
    RecipeInput,
    RecipeOutput,
    ExchangePrice,
    Building,
    BuildingCost,
    Planet,
    System,
    WorkforceNeed,
    Exchange,
    Site,
    SiteBuilding,
    SiteBuildingMaterial,
    Storage,
    StorageItem,
    Warehouse,
    PlanetResource,
    PlanetBuildingRequirement,
    PlanetProductionFee,
    COGCProgram,
    COGCVote,
    InternalOffer,
    Company,
    LocalMarketAd,
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository class that provides session management."""

    def __init__(self, session: Session):
        """Initialize repository with a session factory.

        Args:
            session: SQLModel Session
        """
        self.session = session


class BuildingRepository(BaseRepository):
    """Repository for building-related operations."""

    def get_building(self, symbol: str) -> Optional[Building]:
        """Get a building by symbol.

        Args:
            symbol: Building symbol

        Returns:
            Building if found, None otherwise
        """
        return self.session.get(Building, symbol)

    def create_building(
        self,
        building: Building,
    ) -> Building:
        """Create a new building with its construction costs.

        Args:
            symbol: Building symbol
            name: Building name
            expertise: Required expertise
            pioneers: Number of pioneers required
            settlers: Number of settlers required
            technicians: Number of technicians required
            engineers: Number of engineers required
            scientists: Number of scientists required
            area_cost: Area cost
            costs: List of construction costs with item symbol and amount

        Returns:
            Created building
        """
        self.session.add(building)
        return building

    def get_building_costs_with_prices(
        self,
    ) -> Sequence[tuple[BuildingCost, ExchangePrice]]:
        """Get all building costs with their current market prices.

        Returns:
            List of tuples containing (BuildingCost, ExchangePrice)
        """
        statement = select(BuildingCost, ExchangePrice).join(
            ExchangePrice,
            and_(
                BuildingCost.item_symbol == ExchangePrice.item_symbol,
                ExchangePrice.exchange_code == "AI1",
            ),
        )
        return list(self.session.exec(statement).all())


class ExchangeRepository(BaseRepository):
    """Repository for exchange and price-related operations."""

    def create_exchange_price(
        self,
        exchange_price: ExchangePrice,
    ) -> ExchangePrice:
        """Create a new exchange price.

        Args:
            exchange_price: Exchange price

        Returns:
            Created exchange price
        """
        self.session.add(exchange_price)
        return exchange_price

    def delete_exchange_prices(self) -> None:
        """Delete all exchange prices."""
        statement = select(ExchangePrice)
        prices = self.session.exec(statement).all()
        for price in prices:
            self.session.delete(price)

    def get_exchange_price(self, exchange_code: str, item_symbol: str) -> Optional[ExchangePrice]:
        """Get an exchange price by item symbol and exchange code.

        Args:
            exchange_code: Exchange code
            item_symbol: Item symbol

        Returns:
            Exchange price if found, None otherwise
        """
        statement = (
            select(ExchangePrice)
            .where(ExchangePrice.item_symbol == item_symbol)
            .where(ExchangePrice.exchange_code == exchange_code)
        )
        return self.session.exec(statement).first()

    def get_all_comex_exchanges(self) -> Sequence[Exchange]:
        """Get all commodity exchanges."""
        statement = select(Exchange)
        return self.session.exec(statement).all()

    def get_comex_exchange(self, exchange_code: str) -> Optional[Exchange]:
        """Get a commodity exchange by exchange code.

        Returns:
            ComexExchange if found, None otherwise
        """
        statement = select(Exchange).where(Exchange.exchange_code == exchange_code)
        return self.session.exec(statement).first()

    def create_comex_exchange(
        self,
        comex_exchange: Exchange,
    ) -> Exchange:
        """Create a new commodity exchange.

        Args:
            comex_exchange: Commodity exchange

        Returns:
            Created commodity exchange
        """
        self.session.add(comex_exchange)
        return comex_exchange

    def delete_comex_exchanges(self) -> None:
        """Delete all commodity exchanges."""
        statement = select(Exchange)
        exchanges = self.session.exec(statement).all()
        for exchange in exchanges:
            self.session.delete(exchange)


class ItemRepository(BaseRepository):
    """Repository for item-related operations."""

    def get_item(self, symbol: str) -> Optional[Item]:
        """Get an item by symbol.

        Args:
            symbol: Item symbol

        Returns:
            Item if found, None otherwise
        """
        return self.session.get(Item, symbol)

    def create_item(self, item: Item) -> Item:
        """Create a new item.

        Args:
            item: Item object

        Returns:
            Created item
        """
        self.session.add(item)
        return item


class RecipeRepository(BaseRepository):
    """Repository for recipe-related operations."""

    def get_recipe(self, item_symbol: str) -> Optional[Recipe]:
        """Get a recipe by symbol.

        Args:
            symbol: Recipe symbol

        Returns:
            Recipe if found, None otherwise
        """
        statement = select(Recipe).where(Recipe.symbol == item_symbol)
        return self.session.exec(statement).first()

    def create_recipe(
        self,
        recipe: Recipe,
    ) -> Recipe:
        """Create a new recipe with its inputs and output.

        Args:
            recipe: Recipe object


        Returns:
            Created recipe
        """
        self.session.add(recipe)
        return recipe

    def get_recipe_with_prices(self, symbol: str) -> tuple[Recipe, list[tuple[RecipeInput, ExchangePrice]]]:
        """Get a recipe with current prices for its inputs from AI1 exchange.

        Args:
            symbol: Recipe symbol

        Returns:
            Tuple of (Recipe, list of (RecipeInput, ExchangePrice))
        """
        recipe = self.get_recipe(symbol)
        if not recipe:
            raise ValueError(f"Recipe {symbol} not found")

        # Get latest prices for all inputs from AI1 exchange
        input_prices = []
        for input in recipe.inputs:
            statement = (
                select(ExchangePrice)
                .where(ExchangePrice.item_symbol == input.item_symbol)
                .where(ExchangePrice.exchange_code == "AI1")
                .order_by(desc(ExchangePrice.timestamp))
            )
            price = self.session.exec(statement).first()

            if not price:
                raise ValueError(f"No AI1 price found for {input.item_symbol}")

            input_prices.append((input, price))

        return recipe, input_prices

    def get_all_recipes(self) -> Sequence[Recipe]:
        """Get all recipes with basic information.

        Returns:
            List of dictionaries containing recipe information
        """
        statement = select(Recipe)
        recipes = self.session.exec(statement).all()
        return recipes

    def get_recipes_for_item(self, item_symbol: str) -> Sequence[Recipe]:
        """Get all recipes for an item.

        Args:
            item_symbol: Item symbol

        Returns:
            List of recipes
        """
        statement = select(Recipe).join(RecipeOutput).where(RecipeOutput.item_symbol == item_symbol)
        recipes = self.session.exec(statement).all()
        return recipes


class SiteRepository(BaseRepository):
    """Repository for site-related operations."""

    def get_all_sites(self) -> Sequence[Site]:
        """Get all sites."""
        statement = select(Site)
        return self.session.exec(statement).all()

    def get_site(self, site_id: str) -> Optional[Site]:
        """Get a site by ID.

        Args:
            site_id: Site ID

        Returns:
            Site if found, None otherwise
        """
        return self.session.get(Site, site_id)

    def create_site(
        self,
        site: Site,
    ) -> Site:
        """Create a new site.

        Args:
            site_id: Site ID
            invested_permits: Number of invested permits
            maximum_permits: Maximum number of permits
            planet_natural_id: Planet natural ID

        Returns:
            Created site
        """
        self.session.add(site)
        return site

    def delete_site_buildings(self, site: Site) -> None:
        """Delete all buildings for a site.

        Args:
            site: Site
        """
        statement = select(SiteBuilding).where(SiteBuilding.site_id == site.site_id)
        buildings = self.session.exec(statement).all()
        for building in buildings:
            # Delete building materials first
            self.delete_site_building_materials(building.site_building_id)
            # Then delete the building
            self.session.delete(building)

    def create_site_building(
        self,
        site_building: SiteBuilding,
    ) -> SiteBuilding:
        """Create a new site building.

        Args:
            site_building: Site building

        Returns:
            Created site building
        """
        self.session.add(site_building)
        return site_building

    def create_site_building_material(self, site_building_material: SiteBuildingMaterial) -> SiteBuildingMaterial:
        """Create a new site building material.

        Args:
            site_building_material: Site building material

        Returns:
            Created site building material
        """
        self.session.add(site_building_material)
        return site_building_material

    def get_site_building(self, site_building_id: str) -> Optional[SiteBuilding]:
        """Get a site building by ID.

        Args:
            site_building_id: Site building ID

        Returns:
            SiteBuilding if found, None otherwise
        """
        return self.session.get(SiteBuilding, site_building_id)

    def delete_site_building_materials(self, site_building_id: str) -> None:
        """Delete all materials for a site building.

        Args:
            site_building_id: Site building ID
        """
        statement = select(SiteBuildingMaterial).where(SiteBuildingMaterial.site_building_id == site_building_id)
        materials = self.session.exec(statement).all()
        for material in materials:
            self.session.delete(material)

    def get_building_materials_with_prices(
        self,
    ) -> Sequence[tuple[SiteBuildingMaterial, ExchangePrice]]:
        """Get all building materials with their current market prices.

        Returns:
            List of tuples containing (SiteBuildingMaterial, ExchangePrice)
        """
        statement = select(SiteBuildingMaterial, ExchangePrice).join(
            ExchangePrice,
            and_(
                SiteBuildingMaterial.item_symbol == ExchangePrice.item_symbol,
                ExchangePrice.exchange_code == "AI1",
            ),
        )
        return self.session.exec(statement).all()


class StorageRepository(BaseRepository):
    """Repository for storage-related operations."""

    def get_storage(self, storage_id: str) -> Optional[Storage]:
        """Get a storage by ID.

        Args:
            storage_id: Storage ID

        Returns:
            Storage if found, None otherwise
        """
        return self.session.get(Storage, storage_id)

    def create_storage(
        self,
        storage: Storage,
    ) -> Storage:
        """Create a new storage.

        Args:
            storage: Storage

        Returns:
            Created storage
        """
        self.session.add(storage)
        return storage

    def create_storage_item(self, storage_item: StorageItem) -> StorageItem:
        """Create a new storage item.

        Args:
            storage_item: Storage item

        Returns:
            Created storage item
        """
        self.session.add(storage_item)
        return storage_item

    def delete_storage(self) -> None:
        """Delete all storage data."""
        items = self.session.exec(select(StorageItem)).all()
        for item in items:
            self.session.delete(item)

        storages = self.session.exec(select(Storage)).all()
        for storage in storages:
            self.session.delete(storage)

    def get_all_storage(self) -> Sequence[Storage]:
        """Get all storage facilities.

        Returns:
            List of all storage facilities
        """
        statement = select(Storage).select_from(Storage)
        return self.session.exec(statement).all()

    def delete_storage_items(self, storage_id: str) -> None:
        """Delete all items for a specific storage.

        Args:
            storage_id: Storage ID
        """
        statement = select(StorageItem).where(StorageItem.storage_id == storage_id)
        items = self.session.exec(statement).all()
        for item in items:
            self.session.delete(item)

    def get_storage_items_with_prices(
        self,
    ) -> Sequence[tuple[StorageItem, ExchangePrice]]:
        """Get all storage items with their current market prices.

        Returns:
            List of tuples containing (StorageItem, ExchangePrice)
        """
        statement = select(StorageItem, ExchangePrice).join(
            ExchangePrice,
            and_(
                StorageItem.item_symbol == ExchangePrice.item_symbol,
                ExchangePrice.exchange_code == "AI1",
            ),
        )
        return self.session.exec(statement).all()


class SystemRepository(BaseRepository):
    """Repository for system-related operations."""

    def get_planet(self, natural_id: str) -> Planet | None:
        """Get a planet by natural ID.

        Args:
            natural_id: Planet natural ID

        Returns:
            Planet if found, None otherwise
        """
        return self.session.get(Planet, natural_id)

    def get_planet_by_name(self, name: str) -> Planet | None:
        """Get a planet by name.

        Args:
            name: Planet name

        Returns:
            Planet if found, None otherwise
        """
        print(f"Getting planet by name: {name}")
        statement = select(Planet).where(Planet.name.like(name))
        return self.session.exec(statement).first()

    def create_planet(self, planet: Planet) -> Planet:
        """Create a new planet.

        Args:
            planet: Planet to create

        Returns:
            Created planet
        """
        self.session.add(planet)
        return planet

    def update_planet(self, planet: Planet) -> Planet:
        """Update an existing planet.

        Args:
            planet: Planet to update

        Returns:
            Updated planet
        """
        self.session.add(planet)
        return planet

    def get_system(self, system_id: str) -> System | None:
        """Get a system by ID.

        Args:
            system_id: System ID

        Returns:
            System if found, None otherwise
        """
        return self.session.get(System, system_id)

    def get_system_by_natural_id(self, natural_id: str) -> System | None:
        """Get a system by natural ID.

        Args:
            natural_id: System natural ID

        Returns:
            System if found, None otherwise
        """
        statement = select(System).where(System.natural_id == natural_id)
        return self.session.exec(statement).first()

    def create_system(
        self,
        system: System,
    ) -> System:
        """Create a new system with its connections.

        Args:
            system: System

        Returns:
            Created system
        """
        self.session.add(system)
        return system

    def delete_planet_resources(self, planet: Planet) -> None:
        """Delete all resources for a planet.

        Args:
            planet: Planet
        """
        statement = select(PlanetResource).where(PlanetResource.planet_natural_id == planet.natural_id)
        resources = self.session.exec(statement).all()
        for resource in resources:
            self.session.delete(resource)

    def delete_planet_building_requirements(self, planet: Planet) -> None:
        """Delete all building requirements for a planet.

        Args:
            planet: Planet
        """
        statement = select(PlanetBuildingRequirement).where(
            PlanetBuildingRequirement.planet_natural_id == planet.natural_id
        )
        requirements = self.session.exec(statement).all()
        for requirement in requirements:
            self.session.delete(requirement)

    def delete_planet_production_fees(self, planet: Planet) -> None:
        """Delete all production fees for a planet.

        Args:
            planet: Planet
        """
        statement = select(PlanetProductionFee).where(PlanetProductionFee.planet_natural_id == planet.natural_id)
        fees = self.session.exec(statement).all()
        for fee in fees:
            self.session.delete(fee)

    def delete_planet_cogc_programs(self, planet: Planet) -> None:
        """Delete all COGC programs for a planet.

        Args:
            planet: Planet
        """
        statement = select(COGCProgram).where(COGCProgram.planet_natural_id == planet.natural_id)
        programs = self.session.exec(statement).all()
        for program in programs:
            self.session.delete(program)

    def delete_planet_cogc_votes(self, planet: Planet) -> None:
        """Delete all COGC votes for a planet.

        Args:
            planet: Planet
        """
        statement = select(COGCVote).where(COGCVote.planet_natural_id == planet.natural_id)
        votes = self.session.exec(statement).all()
        for vote in votes:
            self.session.delete(vote)

    def create_planet_resource(self, resource: PlanetResource) -> PlanetResource:
        """Create a new planet resource.

        Args:
            resource: Planet resource to create

        Returns:
            Created planet resource
        """
        self.session.add(resource)
        return resource

    def create_planet_building_requirement(self, requirement: PlanetBuildingRequirement) -> PlanetBuildingRequirement:
        """Create a new planet building requirement.

        Args:
            requirement: Planet building requirement to create

        Returns:
            Created planet building requirement
        """
        self.session.add(requirement)
        return requirement

    def create_planet_production_fee(self, fee: PlanetProductionFee) -> PlanetProductionFee:
        """Create a new planet production fee.

        Args:
            fee: Planet production fee to create

        Returns:
            Created planet production fee
        """
        self.session.add(fee)
        return fee

    def create_cogc_program(self, program: COGCProgram) -> COGCProgram:
        """Create a new COGC program.

        Args:
            program: COGC program to create

        Returns:
            Created COGC program
        """
        self.session.add(program)
        return program

    def create_cogc_vote(self, vote: COGCVote) -> COGCVote:
        """Create a new COGC vote.

        Args:
            vote: COGC vote to create

        Returns:
            Created COGC vote
        """
        self.session.add(vote)
        return vote

    def get_cogc_program(self, natural_id: str) -> COGCProgram | None:
        """Get COGC programs for a planet by natural ID.

        Args:
            natural_id: Planet natural ID

        Returns:
            Latest COGCProgram by start epoch if found, None otherwise
        """
        statement = (
            select(COGCProgram)
            .where(COGCProgram.planet_natural_id == natural_id)
            .order_by(COGCProgram.start_epoch_ms.desc())
        )
        return self.session.exec(statement).first()


class WarehouseRepository(BaseRepository):
    """Repository for warehouse-related operations."""

    def get_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        """Get a warehouse by ID.

        Args:
            warehouse_id: Warehouse ID

        Returns:
            Warehouse if found, None otherwise
        """
        return self.session.get(Warehouse, warehouse_id)

    def create_warehouse(self, warehouse: Warehouse) -> Warehouse:
        """Create a new warehouse.

        Args:
            warehouse: Warehouse

        Returns:
            Created warehouse
        """
        self.session.add(warehouse)
        return warehouse

    def delete_warehouses(self) -> None:
        """Delete all warehouses."""
        statement = select(Warehouse)
        warehouses = self.session.exec(statement).all()
        for warehouse in warehouses:
            self.session.delete(warehouse)

    def get_all_warehouses(self) -> Sequence[Warehouse]:
        """Get all warehouses.

        Returns:
            List of all warehouses
        """
        statement = select(Warehouse)
        return self.session.exec(statement).all()


class WorkforceRepository(BaseRepository):
    """Repository for workforce-related operations."""

    def get_workforce_needs(self, workforce_type: Optional[str] = None) -> Sequence[WorkforceNeed]:
        """Get workforce needs, optionally filtered by workforce type.

        Args:
            workforce_type: Optional workforce type to filter by

        Returns:
            List of workforce needs
        """
        statement = select(WorkforceNeed)
        if workforce_type:
            statement = statement.where(WorkforceNeed.workforce_type == workforce_type)
        return self.session.exec(statement).all()

    def create_workforce_need(self, workforce_need: WorkforceNeed) -> WorkforceNeed:
        """Create a new workforce need.

        Args:
            workforce_need: Workforce need

        Returns:
            Created workforce need
        """
        self.session.add(workforce_need)
        return workforce_need

    def delete_workforce_needs(self, workforce_type: str | None = None) -> None:
        """Delete workforce needs, optionally filtered by workforce type.

        Args:
            workforce_type: Optional workforce type to filter by
        """
        statement = select(WorkforceNeed)
        if workforce_type:
            statement = statement.where(WorkforceNeed.workforce_type == workforce_type)
        needs = self.session.exec(statement).all()
        for need in needs:
            self.session.delete(need)


class CompanyRepository(BaseRepository):
    """Repository for company-related operations."""

    def get_company_by_name_and_user(self, company_name: str, user_name: str) -> Optional[Company]:
        """Get a company by name and user.

        Args:
            company_name: Company name
            user_name: User name

        Returns:
            Company if found, None otherwise
        """
        statement = select(Company).where(Company.name == company_name, Company.user_name == user_name)
        return self.session.exec(statement).first()

    def create_company(self, company: Company) -> Company:
        """Create a new company.

        Args:
            company: Company to create

        Returns:
            Created company
        """
        self.session.add(company)
        self.session.commit()
        self.session.refresh(company)
        return company

    def update_company(self, company: Company) -> Company:
        """Update an existing company.

        Args:
            company: Company to update

        Returns:
            Updated company
        """
        # Get the existing company from the database
        db_company = self.session.get(Company, company.id)
        if not db_company:
            raise ValueError(f"Company with ID {company.id} not found")

        # Update fields - manually update fields that need updating
        if hasattr(company, "name"):
            db_company.name = company.name
        if hasattr(company, "user_name"):
            db_company.user_name = company.user_name
        if hasattr(company, "stock_link"):
            db_company.stock_link = company.stock_link

        self.session.commit()
        self.session.refresh(db_company)
        return db_company


class InternalOfferRepository(BaseRepository):
    """Repository for internal offer-related operations."""

    def get_offers_by_item(self, item_symbol: str) -> list[InternalOffer]:
        """Get all internal offers for a given item symbol.

        Args:
            item_symbol: Item symbol

        Returns:
            List of internal offers
        """
        statement = select(InternalOffer).where(InternalOffer.item_symbol == item_symbol)
        return self.session.exec(statement).all()

    def get_offer_by_item_and_user(self, item_symbol: str, user_name: str) -> Optional[InternalOffer]:
        """Get an internal offer by item symbol and user name.

        Args:
            item_symbol: Item symbol
            user_name: User name

        Returns:
            InternalOffer if found, None otherwise
        """
        statement = (
            select(InternalOffer)
            .join(Company)
            .where(
                InternalOffer.item_symbol == item_symbol,
                Company.user_name == user_name,
            )
        )
        return self.session.exec(statement).first()

    def create_offer(self, offer: InternalOffer) -> InternalOffer:
        """Create a new internal offer.

        Args:
            offer: Internal offer to create

        Returns:
            Created internal offer
        """
        self.session.add(offer)
        self.session.commit()
        self.session.refresh(offer)
        return offer

    def update_offer(self, offer: InternalOffer) -> InternalOffer:
        """Update an existing internal offer.

        Args:
            offer: Internal offer to update

        Returns:
            Updated internal offer
        """
        # Get the existing offer from the database
        db_offer = self.session.get(InternalOffer, offer.id)
        if not db_offer:
            raise ValueError(f"Offer with ID {offer.id} not found")

        # Update fields - manually update fields that need updating
        if hasattr(offer, "item_symbol"):
            db_offer.item_symbol = offer.item_symbol
        if hasattr(offer, "price"):
            db_offer.price = offer.price
        if hasattr(offer, "user_name"):
            db_offer.user_name = offer.user_name
        if hasattr(offer, "company_id"):
            db_offer.company_id = offer.company_id

        self.session.commit()
        self.session.refresh(db_offer)
        return db_offer


class LocalMarketAdRepository(BaseRepository):
    """Repository for local market ads."""

    def get_ads_by_planet(self, planet_natural_id: str) -> list[LocalMarketAd]:
        statement = select(LocalMarketAd).where(LocalMarketAd.planet_natural_id == planet_natural_id)
        return list(self.session.exec(statement).all())

    def delete_ads_by_planet(self, planet_natural_id: str) -> None:
        statement = select(LocalMarketAd).where(LocalMarketAd.planet_natural_id == planet_natural_id)
        for ad in self.session.exec(statement):
            self.session.delete(ad)

    def upsert_ads(self, ads: list[LocalMarketAd]) -> None:
        for ad in ads:
            existing = self.session.exec(
                select(LocalMarketAd).where(
                    (LocalMarketAd.contract_natural_id == ad.contract_natural_id)
                    & (LocalMarketAd.ad_type == ad.ad_type)
                )
            ).first()
            if existing:
                for field, value in ad.dict(exclude_unset=True).items():
                    setattr(existing, field, value)
            else:
                self.session.add(ad)
