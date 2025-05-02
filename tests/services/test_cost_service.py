import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from prun.models import (
    Building,
    BuildingCost,
    Item,
    Planet,
    PlanetBuilding,
    Recipe,
    RecipeInput,
    RecipeOutput,
    WorkforceNeed,
)
from prun.services.cost_service import (
    CostService,
    CalculatedInput,
    CalculatedInputCosts,
    CalculatedWorkforceInput,
    CalculatedWorkforceCosts,
    CalculatedRecipeCost,
    CalculatedCOGM,
)


@pytest.fixture
def mock_services():
    return {
        "building_service": Mock(),
        "exchange_service": Mock(),
        "planet_service": Mock(),
        "recipe_service": Mock(),
        "workforce_service": Mock(),
    }


@pytest.fixture
def cost_service(mock_services):
    return CostService(
        building_service=mock_services["building_service"],
        exchange_service=mock_services["exchange_service"],
        planet_service=mock_services["planet_service"],
        recipe_service=mock_services["recipe_service"],
        workforce_service=mock_services["workforce_service"],
    )


@pytest.fixture
def game_items():
    return {
        "RAT": Item(
            material_id="83dd61885cf6879ff49fe1419f068f10",
            symbol="RAT",
            name="rations",
            category="consumables (basic)",
            weight=0.21,
            volume=0.1,
        ),
        "H2O": Item(
            material_id="ec8dbb1d3f51d89c61b6f58fdd64a7f0",
            symbol="H2O",
            name="water",
            category="liquids",
            weight=0.2,
            volume=0.2,
        ),
        "MCG": Item(
            material_id="cc5fb1618f0506e80bfbcee9ae2605ab",
            symbol="MCG",
            name="mineralConstructionGranulate",
            category="construction materials",
            weight=0.24,
            volume=0.1,
        ),
        "AEF": Item(
            material_id="5fa39c2298568262540bf6579feb017e",
            symbol="AEF",
            name="aerostatFoundation",
            category="construction parts",
            weight=2.0,
            volume=5.0,
        ),
    }


@pytest.fixture
def bmp_building():
    return Building(
        symbol="BMP",
        name="basicMaterialsPlant",
        expertise="MANUFACTURING",
        pioneers=100,
        settlers=0,
        technicians=0,
        engineers=0,
        scientists=0,
        area_cost=12,
    )


@pytest.fixture
def sample_planet():
    return Planet(
        natural_id="KW-688c",
        name="Etherwind",
        system_id="239e36f2a61041e0952d9c9741c195c9",
        planet_id="8403b6809cda4c6adf1362a5c2801ad0",
        gravity=0.56,
        magnetic_field=0.19,
        mass=4.77e24,
        mass_earth=0.80,
        orbit_semi_major_axis=99094810000,
        orbit_eccentricity=0.016,
        orbit_inclination=-0.05,
        orbit_right_ascension=0,
        orbit_periapsis=0,
        orbit_index=2,
        pressure=0.40,
        radiation=2.37e-23,
        radius=7603592.5,
        sunlight=893.76,
        surface=True,
        temperature=31.40,
        fertility=-0.70,
        has_local_market=True,
        has_chamber_of_commerce=True,
        has_warehouse=True,
        has_administration_center=True,
        has_shipyard=True,
        planet_tier=0,
        timestamp=datetime.now(),
        base_local_market_fee=0,
        local_market_fee_factor=0,
        warehouse_fee=0,
    )


@pytest.fixture
def pioneer_needs():
    # Values from DB - amounts are per 100 workers per day
    return [
        WorkforceNeed(workforce_type="PIONEER", item_symbol="RAT", amount=4.0),
        WorkforceNeed(workforce_type="PIONEER", item_symbol="DW", amount=4.0),
        WorkforceNeed(workforce_type="PIONEER", item_symbol="OVE", amount=0.5),
        WorkforceNeed(workforce_type="PIONEER", item_symbol="COF", amount=0.5),
        WorkforceNeed(workforce_type="PIONEER", item_symbol="PWO", amount=0.2),
    ]


@pytest.fixture
def ove_recipe():
    return Recipe(
        symbol="BMP:100xPE-25xPG=>20xOVE",
        building_symbol="BMP",
        time_ms=51840000,  # 14.4 hours
        inputs=[
            RecipeInput(
                recipe_symbol="BMP:100xPE-25xPG=>20xOVE",
                item_symbol="PE",
                quantity=100,
            ),
            RecipeInput(
                recipe_symbol="BMP:100xPE-25xPG=>20xOVE",
                item_symbol="PG",
                quantity=25,
            ),
        ],
        outputs=[
            RecipeOutput(
                recipe_symbol="BMP:100xPE-25xPG=>20xOVE",
                item_symbol="OVE",
                quantity=20,
            ),
        ],
    )


class TestCostService:
    def test_calculate_daily_building_repair_cost(
        self, cost_service, bmp_building, sample_planet
    ):
        # Setup
        building_cost = BuildingCost(
            building_symbol=bmp_building.symbol,
            item_symbol="MCG",
            amount=48,  # 12 area cost * 4 for surface planet
        )
        planet_building = PlanetBuilding(
            building=bmp_building,
            planet=sample_planet,
            building_costs=[building_cost],
        )
        days_since_repair = 30

        # Real market prices
        def get_buy_price(symbol):
            prices = {
                "MCG": 150.0,
            }
            return prices.get(symbol, 0)

        # Execute
        daily_cost = cost_service.calculate_daily_building_repair_cost(
            planet_building=planet_building,
            days_since_last_repair=days_since_repair,
            get_buy_price=get_buy_price,
        )

        # Expected calculation:
        # MCG amount = 48 (12 area cost * 4 for surface)
        # repair_amount = 48 * (30/180) = 8
        # daily_cost = (8 * 150) / 30 = 40.0
        expected_daily_cost = 40.0

        # Assert
        assert round(daily_cost, 2) == expected_daily_cost

    def test_calculate_recipe_cost(
        self, cost_service, bmp_building, sample_planet, ove_recipe, pioneer_needs
    ):
        # Setup
        cost_service.workforce_service.get_workforce_needs.return_value = pioneer_needs
        cost_service.workforce_service.workforce_days.return_value = (
            14.4 / 24
        )  # 14.4 hours in days

        # Mock planet building
        building_cost = BuildingCost(
            building_symbol=bmp_building.symbol,
            item_symbol="MCG",
            amount=48,
        )
        planet_building = PlanetBuilding(
            building=bmp_building,
            planet=sample_planet,
            building_costs=[building_cost],
        )
        cost_service.planet_service.get_planet_building.return_value = planet_building

        # Real market prices
        def get_buy_price(symbol):
            prices = {
                "PE": 80.0,
                "PG": 120.0,
                "MCG": 150.0,
                "RAT": 25.0,
                "OVE": 30.0,
                "PWO": 40.0,
                "COF": 35.0,
                "DW": 15.0,
            }
            return prices.get(symbol, 0)

        # Execute
        result = cost_service.calculate_recipe_cost(
            recipe=ove_recipe,
            planet=sample_planet,
            get_buy_price=get_buy_price,
        )

        # Expected calculations:
        # Input costs: (100 * 80.0) + (25 * 120.0) = 8000 + 3000 = 11000.0

        # Workforce costs for 14.4 hours (0.6 days):
        # DB values are per 100 workers per day, and we have 100 pioneers
        # - RAT: 4.0 * 0.6 = 2.4 units * 25.0 = 60.0
        # - DW:  4.0 * 0.6 = 2.4 units * 15.0 = 36.0
        # - OVE: 0.5 * 0.6 = 0.3 units * 30.0 = 9.0
        # - COF: 0.5 * 0.6 = 0.3 units * 35.0 = 10.5
        # - PWO: 0.2 * 0.6 = 0.12 units * 40.0 = 4.8
        # Total workforce = 120.3

        # Repair costs: (48 * (1/6) * 150.0) * (14.4/24) = 24.0
        expected_total = 11144.3  # 11000 + 120.3 + 24.0

        # Assert
        assert isinstance(result, CalculatedRecipeCost)
        assert len(result.input_costs.inputs) == 2
        assert round(result.input_costs.total, 2) == 11000.0
        assert round(result.workforce_cost.total, 2) == 120.3
        assert round(result.repair_cost, 2) == 24.0
        assert round(result.total, 2) == expected_total

    def test_calculate_cogm(
        self, cost_service, bmp_building, sample_planet, ove_recipe
    ):
        # Setup with real recipe that produces 20 OVE
        mock_recipe_cost = CalculatedRecipeCost(
            recipe_symbol=ove_recipe.symbol,
            building_symbol=bmp_building.symbol,
            time_ms=51840000,
            input_costs=CalculatedInputCosts(
                inputs=[
                    CalculatedInput(
                        item_symbol="PE",
                        quantity=100,
                        price=80.0,
                        total=8000.0,
                    ),
                    CalculatedInput(
                        item_symbol="PG",
                        quantity=25,
                        price=120.0,
                        total=3000.0,
                    ),
                ],
                total=11000.0,
            ),
            workforce_cost=CalculatedWorkforceCosts(
                inputs=[
                    CalculatedWorkforceInput(
                        workforce_type="PIONEER",
                        item_symbol="RAT",
                        quantity=2.4,  # 4.0 per day * 0.6 days
                        price=25.0,
                        total=60.0,
                    ),
                    CalculatedWorkforceInput(
                        workforce_type="PIONEER",
                        item_symbol="DW",
                        quantity=2.4,
                        price=15.0,
                        total=36.0,
                    ),
                    CalculatedWorkforceInput(
                        workforce_type="PIONEER",
                        item_symbol="OVE",
                        quantity=0.3,
                        price=30.0,
                        total=9.0,
                    ),
                    CalculatedWorkforceInput(
                        workforce_type="PIONEER",
                        item_symbol="COF",
                        quantity=0.3,
                        price=35.0,
                        total=10.5,
                    ),
                    CalculatedWorkforceInput(
                        workforce_type="PIONEER",
                        item_symbol="PWO",
                        quantity=0.12,
                        price=40.0,
                        total=4.8,
                    ),
                ],
                total=120.3,
            ),
            repair_cost=24.0,
            total=11144.3,
        )

        with patch.object(
            cost_service,
            "calculate_recipe_cost",
            return_value=mock_recipe_cost,
        ):
            # Execute
            def get_buy_price(symbol):
                prices = {
                    "PE": 80.0,
                    "PG": 120.0,
                    "MCG": 150.0,
                    "RAT": 25.0,
                    "OVE": 30.0,
                }
                return prices.get(symbol, 0)

            result = cost_service.calculate_cogm(
                recipe=ove_recipe,
                planet=sample_planet,
                item_symbol="OVE",
                get_buy_price=get_buy_price,
            )

        # Expected calculations for 20 OVE output:
        # Per unit costs:
        # Input costs per OVE: 11000.0 / 20 = 550.0
        # Workforce costs per OVE: 120.3 / 20 = 6.015
        # Repair costs per OVE: 24.0 / 20 = 1.2
        # Total per OVE: 11144.3 / 20 = 557.215 -> rounds to 557.21

        # Assert
        assert isinstance(result, CalculatedCOGM)
        assert result.recipe_symbol == ove_recipe.symbol
        assert result.item_symbol == "OVE"
        assert round(result.input_costs.total, 2) == 550.0
        assert round(result.workforce_cost.total, 2) == 6.01
        assert round(result.repair_cost, 2) == 1.20
        assert round(result.total_cost, 2) == 557.21
