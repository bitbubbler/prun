import pytest
from unittest.mock import Mock, MagicMock

from prun.services.building_service import BuildingService
from prun.model import Building, BuildingCost, Recipe


@pytest.fixture
def mock_fio_client():
    return Mock()


@pytest.fixture
def mock_building_repository():
    return Mock()


@pytest.fixture
def mock_exchange_service():
    return Mock()


@pytest.fixture
def mock_recipe_service():
    return Mock()


@pytest.fixture
def building_service(
    mock_fio_client,
    mock_building_repository,
    mock_exchange_service,
    mock_recipe_service,
):
    return BuildingService(
        mock_fio_client,
        mock_building_repository,
        mock_exchange_service,
        mock_recipe_service,
    )


class TestBuildingService:
    def test_sync_buildings_creates_new_building(
        self,
        building_service,
        mock_fio_client,
        mock_building_repository,
        mock_recipe_service,
    ):
        # Arrange
        mock_recipe = Recipe(
            symbol="TEST_RECIPE",
            name="Test Recipe",
            time=60,
            produces=[],
            consumes=[],
            building_symbol="RIG",
        )
        mock_recipe_service.get_recipe_unsafe.return_value = mock_recipe

        # Update mock data with real building data from the database
        mock_fio_building = MagicMock()
        mock_fio_building.ticker = "RIG"
        mock_fio_building.name = "rig"
        mock_fio_building.expertise = "RESOURCE_EXTRACTION"
        mock_fio_building.pioneers = 30
        mock_fio_building.settlers = 0
        mock_fio_building.technicians = 0
        mock_fio_building.engineers = 0
        mock_fio_building.scientists = 0
        mock_fio_building.area_cost = 10

        mock_fio_recipe = MagicMock()
        mock_fio_recipe.standard_recipe_name = "TEST_RECIPE"
        mock_fio_building.recipes = [mock_fio_recipe]

        mock_building_cost = MagicMock()
        mock_building_cost.commodity_ticker = "TEST_ITEM"
        mock_building_cost.amount = 10
        mock_fio_building.building_costs = [mock_building_cost]

        mock_fio_client.get_buildings.return_value = [mock_fio_building]
        mock_building_repository.get_building.return_value = None

        # Act
        building_service.sync_buildings()

        # Assert
        mock_fio_client.get_buildings.assert_called_once()
        mock_building_repository.get_building.assert_called_once_with("RIG")
        mock_recipe_service.get_recipe_unsafe.assert_called_once_with("TEST_RECIPE")
        mock_building_repository.create_building.assert_called_once()

        # Verify the building creation call
        created_building = mock_building_repository.create_building.call_args[0][0]
        assert isinstance(created_building, Building)
        assert created_building.symbol == "RIG"
        assert created_building.name == "rig"
        assert created_building.expertise == "RESOURCE_EXTRACTION"
        assert created_building.pioneers == 30
        assert created_building.settlers == 0
        assert created_building.technicians == 0
        assert created_building.engineers == 0
        assert created_building.scientists == 0
        assert created_building.area_cost == 10
        assert len(created_building.recipes) == 1
        assert created_building.recipes[0].symbol == "TEST_RECIPE"
        assert len(created_building.building_costs) == 1
        assert isinstance(created_building.building_costs[0], BuildingCost)
        assert created_building.building_costs[0].item_symbol == "TEST_ITEM"
        assert created_building.building_costs[0].amount == 10

    def test_sync_buildings_skips_existing_building(
        self, building_service, mock_fio_client, mock_building_repository
    ):
        # Arrange
        mock_fio_building = MagicMock()
        mock_fio_building.ticker = "EXISTING_BUILDING"
        mock_fio_client.get_buildings.return_value = [mock_fio_building]
        mock_building_repository.get_building.return_value = Building(
            symbol="EXISTING_BUILDING",
            name="Existing Building",
            expertise="TEST",
            pioneers=0,
            settlers=0,
            technicians=0,
            engineers=0,
            scientists=0,
            area_cost=0,
            recipes=[],
        )

        # Act
        building_service.sync_buildings()

        # Assert
        mock_fio_client.get_buildings.assert_called_once()
        mock_building_repository.get_building.assert_called_once_with(
            "EXISTING_BUILDING"
        )
        mock_building_repository.create_building.assert_not_called()

    def test_sync_buildings_raises_error_when_recipe_not_found(
        self,
        building_service,
        mock_fio_client,
        mock_building_repository,
        mock_recipe_service,
    ):
        # Arrange
        mock_fio_building = MagicMock()
        mock_fio_building.ticker = "TEST_BUILDING"
        mock_fio_recipe = MagicMock()
        mock_fio_recipe.standard_recipe_name = "NONEXISTENT_RECIPE"
        mock_fio_building.recipes = [mock_fio_recipe]
        mock_fio_building.building_costs = []

        mock_fio_client.get_buildings.return_value = [mock_fio_building]
        mock_building_repository.get_building.return_value = None
        mock_recipe_service.get_recipe_unsafe.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Recipe NONEXISTENT_RECIPE not found"):
            building_service.sync_buildings()
