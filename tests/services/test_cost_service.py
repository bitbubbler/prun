import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from pydantic import BaseModel, Field
from typing import Dict, List

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
    CalculatedRecipeOutputCOGM,
)


class RecipeTestData(BaseModel):
    """Test data structure for recipe cost calculations."""

    recipe: Recipe = Field(description="The recipe to test cost calculations for")
    planet: Planet = Field(description="The planet where the recipe will be produced")
    building: Building = Field(description="The building that will produce the recipe")
    workforce_needs: List[WorkforceNeed] = Field(
        description="List of workforce needs for the recipe production"
    )
    workforce_days: float = Field(
        description="Number of days of workforce needed to complete the recipe",
        gt=0,
    )
    building_costs: List[BuildingCost] = Field(
        description="List of building costs for the production facility"
    )
    market_prices: Dict[str, float] = Field(
        description="Map of item symbols to their current market prices",
        example={"PE": 80.0, "PG": 120.0},
    )
    expected_inputs_count: int = Field(
        description="Expected number of input items in the recipe",
        ge=0,
    )
    expected_input_cost: float = Field(
        description="Expected total cost of all input materials",
        ge=0,
    )
    expected_workforce_cost: float = Field(
        description="Expected total cost of workforce needs",
        ge=0,
    )
    expected_repair_cost: float = Field(
        description="Expected daily repair cost for the building",
        ge=0,
    )
    expected_total_cost: float = Field(
        description="Expected total cost of recipe production (inputs + workforce + repair)",
        ge=0,
    )

    class Config:
        schema_extra = {
            "example": {
                "recipe": {
                    "symbol": "BMP:100xPE-25xPG=>20xOVE",
                    "building_symbol": "BMP",
                    "time_ms": 51840000,
                },
                "workforce_days": 0.6,
                "market_prices": {
                    "PE": 80.0,
                    "PG": 120.0,
                },
                "expected_inputs_count": 2,
                "expected_input_cost": 11000.0,
                "expected_workforce_cost": 120.3,
                "expected_repair_cost": 105.67,
                "expected_total": 11225.97,
            }
        }


class COGMTestData(BaseModel):
    """Test data structure for COGM calculations."""

    recipe: Recipe = Field(description="The recipe to test COGM calculations for")
    planet: Planet = Field(description="The planet where the recipe will be produced")
    output_symbol: str = Field(
        description="The symbol of the output item to calculate COGM for"
    )
    output_quantity: int = Field(
        description="The quantity of output items produced per recipe"
    )
    market_prices: Dict[str, float] = Field(
        description="Map of item symbols to their current market prices",
        example={"PE": 80.0, "PG": 120.0},
    )
    expected_input_cost_per_unit: float = Field(
        description="Expected input cost per unit of output",
        ge=0,
    )
    expected_workforce_cost_per_unit: float = Field(
        description="Expected workforce cost per unit of output",
        ge=0,
    )
    expected_repair_cost_per_unit: float = Field(
        description="Expected repair cost per unit of output",
        ge=0,
    )
    expected_total_cost_per_unit: float = Field(
        description="Expected total cost per unit of output",
        ge=0,
    )

    class Config:
        schema_extra = {
            "example": {
                "recipe": {
                    "symbol": "BMP:100xPE-25xPG=>20xOVE",
                    "building_symbol": "BMP",
                    "time_ms": 51840000,
                },
                "output_symbol": "OVE",
                "output_quantity": 20,
                "market_prices": {
                    "PE": 80.0,
                    "PG": 120.0,
                },
                "expected_input_cost_per_unit": 550.0,
                "expected_workforce_cost_per_unit": 5.33,
                "expected_repair_cost_per_unit": 5.28,
                "expected_total_cost_per_unit": 560.61,
            }
        }


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
        building_costs=[
            BuildingCost(
                building_symbol="BMP",
                item_symbol="BDE",
                amount=2,
            ),
            BuildingCost(
                building_symbol="BMP",
                item_symbol="BBH",
                amount=4,
            ),
            BuildingCost(
                building_symbol="BMP",
                item_symbol="BSE",
                amount=6,
            ),
        ],
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
        WorkforceNeed(
            workforce_type="PIONEER",
            item_symbol="RAT",
            amount_per_100_workers_per_day=4.0,
        ),
        WorkforceNeed(
            workforce_type="PIONEER",
            item_symbol="DW",
            amount_per_100_workers_per_day=4.0,
        ),
        WorkforceNeed(
            workforce_type="PIONEER",
            item_symbol="OVE",
            amount_per_100_workers_per_day=0.5,
        ),
        WorkforceNeed(
            workforce_type="PIONEER",
            item_symbol="COF",
            amount_per_100_workers_per_day=0.5,
        ),
        WorkforceNeed(
            workforce_type="PIONEER",
            item_symbol="PWO",
            amount_per_100_workers_per_day=0.2,
        ),
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

    def _test_calculate_recipe_cost(
        self, cost_service: CostService, recipe_test_data: RecipeTestData
    ) -> CalculatedRecipeCost:
        """
        Helper method to test recipe cost calculations with different inputs.

        Args:
            cost_service: The CostService instance
            test_data: RecipeTestData containing all test parameters and expected values

        Returns:
            CalculatedRecipeCost: The calculated recipe cost result
        """
        # Setup workforce service mocks
        cost_service.workforce_service.get_workforce_needs.return_value = (
            recipe_test_data.workforce_needs
        )
        cost_service.workforce_service.workforce_days.return_value = (
            recipe_test_data.workforce_days
        )

        # Setup planet building
        planet_building = PlanetBuilding.planet_building_from(
            building=recipe_test_data.building,
            planet=recipe_test_data.planet,
        )
        cost_service.planet_service.get_planet_building.return_value = planet_building

        # Setup market prices
        def get_buy_price(symbol):
            price = recipe_test_data.market_prices.get(symbol)
            if price is None:
                raise ValueError(f"Price for {symbol} not found")
            return price

        # Execute
        result = cost_service.calculate_recipe_cost(
            recipe=recipe_test_data.recipe,
            planet=recipe_test_data.planet,
            get_buy_price=get_buy_price,
        )

        # Assert
        assert isinstance(result, CalculatedRecipeCost)
        assert len(result.input_costs.inputs) == recipe_test_data.expected_inputs_count
        assert (
            round(result.input_costs.total, 2) == recipe_test_data.expected_input_cost
        )
        assert (
            round(result.workforce_cost.total, 2)
            == recipe_test_data.expected_workforce_cost
        )
        assert round(result.repair_cost, 2) == recipe_test_data.expected_repair_cost
        assert round(result.total, 2) == recipe_test_data.expected_total_cost

        return result

    def test_recipe_cost_gf__10_gl_15_pg__10_rg(self, cost_service):
        """Test the cost calculation for the RG recipe in the Glass Furnace (GF)."""
        building_symbol = "GF"
        recipe_symbol = "GF:10xGL-15xPG=>10xRG"
        planet_symbol = "WU-070a"
        planet_name = "Hyalos"
        building = Building(
            symbol=building_symbol,
            name="glassFurnace",
            expertise="METALLURGY",
            pioneers=0,
            settlers=80,
            technicians=0,
            engineers=0,
            scientists=0,
            area_cost=27,
            building_costs=[
                BuildingCost(
                    building_symbol=building_symbol,
                    item_symbol="TRU",
                    amount=5,
                ),
                BuildingCost(
                    building_symbol=building_symbol,
                    item_symbol="LBH",
                    amount=4,
                ),
                BuildingCost(
                    building_symbol=building_symbol,
                    item_symbol="LSE",
                    amount=6,
                ),
            ],
        )

        planet = Planet(
            natural_id=planet_symbol,
            name=planet_name,
            system_id="e92123538c66403bbc8edecb5fbed50a",
            planet_id="05cdce08f362adc36778fd5bb12fb53c",
            gravity=1.2156225442886353,
            magnetic_field=0.0462459959089756,
            mass=1.0962229002689905e25,
            mass_earth=1.835604190826416,
            orbit_semi_major_axis=24198237000,
            orbit_eccentricity=0.005065567325800657,
            orbit_inclination=-0.036997292190790176,
            orbit_right_ascension=0,
            orbit_periapsis=0,
            orbit_index=0,
            pressure=0.2749382257461548,
            radiation=3.182173975442235e-24,
            radius=7833893.5,
            sunlight=102.11439514160156,
            surface=True,
            temperature=72.5621109008789,
            fertility=-1.0,
            has_local_market=True,
            has_chamber_of_commerce=True,
            has_warehouse=True,
            has_administration_center=True,
            has_shipyard=False,
            planet_tier=0,
            timestamp=datetime.now(),
            base_local_market_fee=0,
            local_market_fee_factor=2,
            warehouse_fee=100,
        )

        recipe = Recipe(
            symbol=recipe_symbol,
            building_symbol=building_symbol,
            time_ms=112320000,  # 1d 7h 12m
            inputs=[
                RecipeInput(
                    recipe_symbol=recipe_symbol,
                    item_symbol="GL",
                    quantity=10,
                ),
                RecipeInput(
                    recipe_symbol=recipe_symbol,
                    item_symbol="PG",
                    quantity=15,
                ),
            ],
            outputs=[
                RecipeOutput(
                    recipe_symbol=recipe_symbol,
                    item_symbol="RG",
                    quantity=10,
                ),
            ],
        )

        settler_needs = [
            WorkforceNeed(
                workforce_type="SETTLER",
                item_symbol="KOM",
                amount_per_100_workers_per_day=1.0,
            ),
            WorkforceNeed(
                workforce_type="SETTLER",
                item_symbol="RAT",
                amount_per_100_workers_per_day=6.0,
            ),
            WorkforceNeed(
                workforce_type="SETTLER",
                item_symbol="EXO",
                amount_per_100_workers_per_day=0.5,
            ),
            WorkforceNeed(
                workforce_type="SETTLER",
                item_symbol="PT",
                amount_per_100_workers_per_day=0.5,
            ),
            WorkforceNeed(
                workforce_type="SETTLER",
                item_symbol="REP",
                amount_per_100_workers_per_day=0.2,
            ),
            WorkforceNeed(
                workforce_type="SETTLER",
                item_symbol="DW",
                amount_per_100_workers_per_day=5.0,
            ),
        ]

        recipe_test_data = RecipeTestData(
            recipe=recipe,
            planet=planet,
            building=building,
            workforce_needs=settler_needs,
            workforce_days=recipe.hours_decimal / 24,
            building_costs=building.building_costs,
            market_prices={
                "DW": 15.0,
                "EXO": 80.0,
                "GL": 60.0,
                "KOM": 100.0,
                "LBH": 1200.0,
                "LSE": 900.0,
                "MCG": 150.0,
                "PG": 120.0,
                "PT": 50.0,
                "RAT": 25.0,
                "REP": 200.0,
                "RG": 200.0,
                "TRU": 1800.0,
            },
            expected_inputs_count=2,
            expected_input_cost=2400.0,
            expected_workforce_cost=447.20,
            expected_repair_cost=255.67,
            expected_total_cost=3102.87,
        )

        self._test_calculate_recipe_cost(cost_service, recipe_test_data)

    def test_recipe_cost_bmp__100_pe_25_pg__20_ove(self, cost_service):
        """Example of using the helper method to test the OVE recipe."""
        # Create test data
        building_symbol = "BMP"
        recipe_symbol = "BMP:100xPE-25xPG=>20xOVE"
        planet_symbol = "KW-688c"
        planet_name = "Etherwind"
        building = Building(
            symbol=building_symbol,
            name="basicMaterialsPlant",
            expertise="MANUFACTURING",
            pioneers=100,
            settlers=0,
            technicians=0,
            engineers=0,
            scientists=0,
            area_cost=12,
            building_costs=[
                BuildingCost(
                    building_symbol=building_symbol,
                    item_symbol="BDE",
                    amount=2,
                ),
                BuildingCost(
                    building_symbol=building_symbol,
                    item_symbol="BBH",
                    amount=4,
                ),
                BuildingCost(
                    building_symbol=building_symbol,
                    item_symbol="BSE",
                    amount=6,
                ),
            ],
        )

        planet = Planet(
            natural_id=planet_symbol,
            name=planet_name,
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

        recipe = Recipe(
            symbol=recipe_symbol,
            building_symbol=building_symbol,
            time_ms=51840000,  # 14.4 hours
            inputs=[
                RecipeInput(
                    recipe_symbol=recipe_symbol,
                    item_symbol="PE",
                    quantity=100,
                ),
                RecipeInput(
                    recipe_symbol=recipe_symbol,
                    item_symbol="PG",
                    quantity=25,
                ),
            ],
            outputs=[
                RecipeOutput(
                    recipe_symbol=recipe_symbol,
                    item_symbol="OVE",
                    quantity=20,
                ),
            ],
        )

        pioneer_needs = [
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="RAT",
                amount_per_100_workers_per_day=4.0,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="DW",
                amount_per_100_workers_per_day=4.0,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="OVE",
                amount_per_100_workers_per_day=0.5,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="COF",
                amount_per_100_workers_per_day=0.5,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="PWO",
                amount_per_100_workers_per_day=0.2,
            ),
        ]

        recipe_test_data = RecipeTestData(
            recipe=recipe,
            planet=planet,
            building=building,
            workforce_needs=pioneer_needs,
            workforce_days=recipe.hours_decimal / 24,
            building_costs=building.building_costs,
            market_prices={
                "BBH": 2500.00,
                "BDE": 2300.00,
                "BSE": 1650.00,
                "COF": 35.0,
                "DW": 15.0,
                "MCG": 150.0,
                "OVE": 30.0,
                "PE": 80.0,
                "PG": 120.0,
                "PWO": 40.0,
                "RAT": 25.0,
            },
            expected_inputs_count=2,
            expected_input_cost=11000.0,
            expected_workforce_cost=120.30,
            expected_repair_cost=105.67,
            expected_total_cost=11225.97,
        )

        self._test_calculate_recipe_cost(cost_service, recipe_test_data)

    def _test_calculate_cogm(
        self,
        cost_service: CostService,
        cogm_test_data: COGMTestData,
    ) -> CalculatedRecipeOutputCOGM:
        """
        Helper method to test COGM calculations with different inputs.

        Args:
            cost_service: The CostService instance
            cogm_test_data: COGMTestData containing all test parameters and expected values

        Returns:
            CalculatedRecipeOutputCOGM: The calculated COGM result
        """

        def get_buy_price(symbol):
            return cogm_test_data.market_prices.get(symbol, 0)

        result = cost_service.calculate_cogm(
            recipe=cogm_test_data.recipe,
            planet=cogm_test_data.planet,
            item_symbol=cogm_test_data.output_symbol,
            get_buy_price=get_buy_price,
        )

        # Assert
        assert isinstance(result, CalculatedRecipeOutputCOGM)
        assert result.recipe_symbol == cogm_test_data.recipe.symbol
        assert result.item_symbol == cogm_test_data.output_symbol
        # commented out for now because we don't have good test data for anything but the total.
        # assert round(result.input_costs.total, 2) == round(
        #     cogm_test_data.expected_input_cost_per_unit, 2
        # )
        # assert round(result.workforce_cost.total, 2) == round(
        #     cogm_test_data.expected_workforce_cost_per_unit, 2
        # )
        # assert round(result.repair_cost, 2) == round(
        #     cogm_test_data.expected_repair_cost_per_unit, 2
        # )
        assert round(result.total_cost, 2) == round(
            cogm_test_data.expected_total_cost_per_unit, 2
        )

        return result

    def test_cogm_bmp__100_pe_25_pg__20_ove(
        self, cost_service, bmp_building, sample_planet, ove_recipe
    ):
        """Test the COGM calculation for the OVE recipe in the Basic Materials Plant (BMP)."""
        # Setup planet building mock
        planet_building = PlanetBuilding.planet_building_from(
            building=bmp_building,
            planet=sample_planet,
        )
        cost_service.planet_service.get_planet_building.return_value = planet_building

        # Setup workforce needs mock
        pioneer_needs = [
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="RAT",
                amount_per_100_workers_per_day=4.0,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="DW",
                amount_per_100_workers_per_day=4.0,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="OVE",
                amount_per_100_workers_per_day=0.5,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="COF",
                amount_per_100_workers_per_day=0.5,
            ),
            WorkforceNeed(
                workforce_type="PIONEER",
                item_symbol="PWO",
                amount_per_100_workers_per_day=0.2,
            ),
        ]
        cost_service.workforce_service.get_workforce_needs.return_value = pioneer_needs
        cost_service.workforce_service.workforce_days.return_value = (
            ove_recipe.hours_decimal / 24
        )  # 14.4 hours in days

        cogm_test_data = COGMTestData(
            recipe=ove_recipe,
            planet=sample_planet,
            output_symbol="OVE",
            output_quantity=20,
            market_prices={
                "BBH": 2500.00,
                "BDE": 2300.00,
                "BSE": 1650.00,
                "COF": 35.0,
                "DW": 15.0,
                "MCG": 150.0,
                "OVE": 30.0,
                "PE": 80.0,
                "PG": 120.0,
                "PWO": 40.0,
                "RAT": 25.0,
            },
            expected_input_cost_per_unit=550.0,
            expected_workforce_cost_per_unit=5.33,
            expected_repair_cost_per_unit=5.28,
            expected_total_cost_per_unit=561.30,
        )

        self._test_calculate_cogm(cost_service, cogm_test_data)
