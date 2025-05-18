from typing import Generator

from dependency_injector import containers, providers
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, Session, SQLModel

from fio import FIOClient
from fly.repository import (
    BuildingRepository,
    ExchangeRepository,
    ItemRepository,
    RecipeRepository,
    SiteRepository,
    StorageRepository,
    SystemRepository,
    WarehouseRepository,
    WorkforceRepository,
    InternalOfferRepository,
    CompanyRepository,
)
from fly.services.building_service import BuildingService
from fly.services.cost_service import CostService
from fly.services.efficiency_service import EfficiencyService
from fly.services.exchange_service import ExchangeService
from fly.services.item_service import ItemService
from fly.services.planet_service import PlanetService
from fly.services.recipe_service import RecipeService
from fly.services.site_service import SiteService
from fly.services.storage_service import StorageService
from fly.services.system_service import SystemService
from fly.services.warehouse_service import WarehouseService
from fly.services.workforce_service import WorkforceService
from fly.services.internal_offer_service import InternalOfferService


def session_resource_factory(engine: Engine) -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Container(containers.DeclarativeContainer):
    engine = providers.Singleton(create_engine, "sqlite:///prun.db")
    fio_client = providers.Singleton(FIOClient)

    session = providers.Resource(session_resource_factory, engine=engine)

    # Repositories
    building_repository = providers.Factory(BuildingRepository, session=session)
    company_repository = providers.Factory(CompanyRepository, session=session)
    exchange_repository = providers.Factory(ExchangeRepository, session=session)
    internal_offer_repository = providers.Factory(InternalOfferRepository, session=session)
    item_repository = providers.Factory(ItemRepository, session=session)
    recipe_repository = providers.Factory(RecipeRepository, session=session)
    site_repository = providers.Factory(SiteRepository, session=session)
    storage_repository = providers.Factory(StorageRepository, session=session)
    system_repository = providers.Factory(SystemRepository, session=session)
    warehouse_repository = providers.Factory(WarehouseRepository, session=session)
    workforce_repository = providers.Factory(WorkforceRepository, session=session)

    # Services with no other service dependencies
    building_service = providers.Factory(
        BuildingService,
        fio_client=fio_client,
        building_repository=building_repository,
    )
    efficiency_service = providers.Factory(EfficiencyService)
    exchange_service = providers.Factory(
        ExchangeService,
        fio_client=fio_client,
        exchange_repository=exchange_repository,
    )
    item_service = providers.Factory(
        ItemService,
        fio_client=fio_client,
        item_repository=item_repository,
    )
    planet_service = providers.Factory(
        PlanetService,
        fio_client=fio_client,
        system_repository=system_repository,
    )
    recipe_service = providers.Factory(
        RecipeService,
        fio_client=fio_client,
        efficiency_service=efficiency_service,
        recipe_repository=recipe_repository,
    )
    site_service = providers.Factory(
        SiteService,
        fio_client=fio_client,
        site_repository=site_repository,
    )
    storage_service = providers.Factory(
        StorageService,
        fio_client=fio_client,
        storage_repository=storage_repository,
    )
    system_service = providers.Factory(
        SystemService,
        fio_client=fio_client,
        system_repository=system_repository,
    )
    warehouse_service = providers.Factory(
        WarehouseService,
        fio_client=fio_client,
        warehouse_repository=warehouse_repository,
    )
    workforce_service = providers.Factory(
        WorkforceService,
        fio_client=fio_client,
        workforce_repository=workforce_repository,
    )
    internal_offer_service = providers.Factory(
        InternalOfferService,
        company_repository=company_repository,
        item_repository=item_repository,
        offer_repository=internal_offer_repository,
    )
    # Services with other service dependencies
    cost_service = providers.Factory(
        CostService,
        building_service=building_service,
        efficiency_service=efficiency_service,
        exchange_service=exchange_service,
        planet_service=planet_service,
        recipe_service=recipe_service,
        workforce_service=workforce_service,
    )


container = Container()
container.init_resources()  # Initialize resources before using them
SQLModel.metadata.create_all(container.engine())


def setup_database() -> None:
    """Set up the database connection."""
    engine = create_engine(
        "sqlite:///prun.db",
    )
    SQLModel.metadata.create_all(engine)
