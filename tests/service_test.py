import pytest
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from unittest.mock import MagicMock

from prun.models import (
    Building,
    WorkforceNeed,
    ExchangePrice,
    Recipe,
    RecipeInput,
    RecipeOutput,
)
from prun.services.cost_service import CostService, CalculatedCOGM
from prun.services.building_service import BuildingService
from prun.services.exchange_service import ExchangeService
from prun.services.recipe_service import RecipeService
from prun.services.workforce_service import WorkforceService


@pytest.fixture
def mock_building_service():
    building = Building(
        symbol="TEST_BUILDING",
        name="Test Building",
        pioneers=2,
        settlers=1,
        technicians=0,
        engineers=0,
        scientists=0,
        area_cost=100,
    )
    service = MagicMock(spec=BuildingService)
    service.get_building.return_value = building
    return service


@pytest.fixture
def mock_exchange_service():
    service = MagicMock(spec=ExchangeService)
    # Mock get_buy_price to return 100.0 for any item
    service.get_buy_price = MagicMock(return_value=100.0)
    return service


@pytest.fixture
def mock_recipe_service():
    recipe = Recipe(
        symbol="TEST_RECIPE",
        building_symbol="TEST_BUILDING",
        time_ms=3600000,  # 1 hour
        inputs=[RecipeInput(item_symbol="TEST_INPUT", quantity=10)],
        outputs=[RecipeOutput(item_symbol="TEST_OUTPUT", quantity=1)],
    )
    service = MagicMock(spec=RecipeService)
    service.find_recipe.return_value = recipe
    service.get_recipe_with_prices.return_value = (
        recipe,
        [
            (
                RecipeInput(item_symbol="TEST_INPUT", quantity=10),
                ExchangePrice(
                    item_symbol="TEST_INPUT",
                    exchange_code="AI1",
                    timestamp=datetime.now(timezone.utc),
                    ask_price=100.0,
                    bid_price=90.0,
                    average_price=95.0,
                ),
            )
        ],
    )
    return service


@pytest.fixture
def mock_workforce_service():
    service = MagicMock(spec=WorkforceService)
    service.get_workforce_needs.return_value = [
        WorkforceNeed(workforce_type="PIONEER", item_symbol="FOOD", amount=24),
        WorkforceNeed(workforce_type="SETTLER", item_symbol="FOOD", amount=12),
    ]
    service.workforce_days.return_value = 22.5  # 20 A$ + 2.5 A$
    return service


@pytest.fixture
def cost_service(
    mock_building_service,
    mock_exchange_service,
    mock_recipe_service,
    mock_workforce_service,
):
    return CostService(
        building_service=mock_building_service,
        exchange_service=mock_exchange_service,
        recipe_service=mock_recipe_service,
        workforce_service=mock_workforce_service,
    )


def test_calculate_cogm_basic(cost_service):
    """Test COGM calculation for a basic recipe."""
    cogm = cost_service.calculate_cogm("TEST_OUTPUT")

    # Expected costs:
    # Input costs: 10 units * 100 A$/unit = 1000 A$
    # Labor costs: 22.5 A$ (mocked)

    assert isinstance(cogm, CalculatedCOGM)
    assert cogm.recipe == "TEST_RECIPE"
    assert cogm.building == "TEST_BUILDING"
    assert cogm.time_ms == 3600000
    assert len(cogm.input_costs) == 1
    assert cogm.input_costs[0].total == 1000.0  # 10 units * 100 A$
    assert cogm.workforce_cost == 22.5
    assert cogm.total_cost == 1022.5  # 1000 A$ + 22.5 A$
    assert len(cogm.recipe_outputs) == 1
    assert cogm.recipe_outputs[0].item == "TEST_OUTPUT"
    assert cogm.recipe_outputs[0].quantity == 1


def test_calculate_cogm_multiple_batches(cost_service):
    """Test COGM calculation for multiple batches."""
    cogm = cost_service.calculate_cogm("TEST_OUTPUT", item_quantity=2)

    assert isinstance(cogm, CalculatedCOGM)
    assert cogm.quantity == 2
    assert cogm.recipe_runs_needed == 2.0
    assert cogm.input_costs[0].total == 2000.0  # 2 * 10 units * 100 A$
    assert cogm.workforce_cost == 45.0  # 2 * 22.5 A$
    assert cogm.total_cost == 2045.0  # 2000 A$ + 45 A$


def test_calculate_cogm_missing_recipe(cost_service, mock_recipe_service):
    """Test COGM calculation with a non-existent recipe."""
    mock_recipe_service.find_recipe.side_effect = ValueError(
        "Recipe NONEXISTENT not found"
    )

    with pytest.raises(ValueError, match="Recipe NONEXISTENT not found"):
        cost_service.calculate_cogm("NONEXISTENT")
