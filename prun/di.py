from contextlib import contextmanager
from typing import Generator

from dependency_injector import containers, providers
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, Session, SQLModel

from prun import repository
from prun.services import (
    building_service,
    cost_service,
    exchange_service,
    item_service,
    planet_service,
    recipe_service,
    site_service,
    storage_service,
    system_service,
    workforce_service,
    warehouse_service,
)
from fio import FIOClient


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
    building_repository = providers.Factory(
        repository.BuildingRepository, session=session
    )
    exchange_repository = providers.Factory(
        repository.ExchangeRepository, session=session
    )
    item_repository = providers.Factory(repository.ItemRepository, session=session)
    recipe_repository = providers.Factory(repository.RecipeRepository, session=session)
    site_repository = providers.Factory(repository.SiteRepository, session=session)
    storage_repository = providers.Factory(
        repository.StorageRepository, session=session
    )
    system_repository = providers.Factory(repository.SystemRepository, session=session)
    warehouse_repository = providers.Factory(
        repository.WarehouseRepository, session=session
    )
    workforce_repository = providers.Factory(
        repository.WorkforceRepository, session=session
    )

    # Services with no other service dependencies
    building_service = providers.Factory(
        building_service.BuildingService,
        fio_client=fio_client,
        building_repository=building_repository,
    )
    exchange_service = providers.Factory(
        exchange_service.ExchangeService,
        fio_client=fio_client,
        exchange_repository=exchange_repository,
    )
    item_service = providers.Factory(
        item_service.ItemService,
        fio_client=fio_client,
        item_repository=item_repository,
    )
    planet_service = providers.Factory(
        planet_service.PlanetService,
        fio_client=fio_client,
        system_repository=system_repository,
    )
    recipe_service = providers.Factory(
        recipe_service.RecipeService,
        fio_client=fio_client,
        recipe_repository=recipe_repository,
    )
    site_service = providers.Factory(
        site_service.SiteService,
        fio_client=fio_client,
        site_repository=site_repository,
    )
    storage_service = providers.Factory(
        storage_service.StorageService,
        fio_client=fio_client,
        storage_repository=storage_repository,
    )
    system_service = providers.Factory(
        system_service.SystemService,
        fio_client=fio_client,
        system_repository=system_repository,
    )
    warehouse_service = providers.Factory(
        warehouse_service.WarehouseService,
        fio_client=fio_client,
        warehouse_repository=warehouse_repository,
    )
    workforce_service = providers.Factory(
        workforce_service.WorkforceService,
        fio_client=fio_client,
        workforce_repository=workforce_repository,
    )
    # Services with other service dependencies
    cost_service = providers.Factory(
        cost_service.CostService,
        building_service=building_service,
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
