from datetime import datetime

import pytest
import requests
from unittest.mock import patch, MagicMock

from fio.client import FIOClient
from fio.models import (
    FIOPrice,
    FIORecipe,
    FIOBuildingCost,
    FIOBuildingRecipeDetail,
    FIOBuildingRecipeInputOutput,
    FIOSystem,
    FIOSystemConnection,
)


@pytest.fixture
def headers():
    return "Ticker,MMBuy,MMSell,AI1-Average,AI1-AskAmt,AI1-AskPrice,AI1-AskAvail,AI1-BidAmt,AI1-BidPrice,AI1-BidAvail,CI1-Average,CI1-AskAmt,CI1-AskPrice,CI1-AskAvail,CI1-BidAmt,CI1-BidPrice,CI1-BidAvail,CI2-Average,CI2-AskAmt,CI2-AskPrice,CI2-AskAvail,CI2-BidAmt,CI2-BidPrice,CI2-BidAvail,NC1-Average,NC1-AskAmt,NC1-AskPrice,NC1-AskAvail,NC1-BidAmt,NC1-BidPrice,NC1-BidAvail,NC2-Average,NC2-AskAmt,NC2-AskPrice,NC2-AskAvail,NC2-BidAmt,NC2-BidPrice,NC2-BidAvail,IC1-Average,IC1-AskAmt,IC1-AskPrice,IC1-AskAvail,IC1-BidAmt,IC1-BidPrice,IC1-BidAvail"


@pytest.fixture
def example_price_data():
    return [
        {
            "MaterialTicker": "AAR",
            "ExchangeCode": "AI1",
            "MMBuy": None,
            "MMSell": None,
            "PriceAverage": 15100,
            "AskCount": 58,
            "Ask": 15000,
            "Supply": 178,
            "BidCount": None,
            "Bid": None,
            "Demand": 0,
        },
        {
            "MaterialTicker": "AAR",
            "ExchangeCode": "CI1",
            "MMBuy": None,
            "MMSell": None,
            "PriceAverage": 14900,
            "AskCount": 217,
            "Ask": 14900,
            "Supply": 513,
            "BidCount": None,
            "Bid": None,
            "Demand": 0,
        },
        {
            "MaterialTicker": "ABH",
            "ExchangeCode": "AI1",
            "MMBuy": None,
            "MMSell": None,
            "PriceAverage": 47830.12109375,
            "AskCount": 84,
            "Ask": 50900,
            "Supply": 781,
            "BidCount": 79,
            "Bid": 45200,
            "Demand": 387,
        },
        {
            "MaterialTicker": "ADR",
            "ExchangeCode": "AI1",
            "MMBuy": 58000,
            "MMSell": None,
            "PriceAverage": 60000,
            "AskCount": 32,
            "Ask": 69000,
            "Supply": 72,
            "BidCount": 1,
            "Bid": 58100,
            "Demand": 101,
        },
    ]


@pytest.fixture
def mock_csv_response(headers, example_price_data):
    return headers + "\n" + "\n".join(example_price_data)


@pytest.fixture
def example_recipe_data():
    return [
        {
            "RecipeName": "1xBMF-1xSNM=>1xNV2",
            "StandardRecipeName": "AAF:1xBMF-1xSNM=>1xNV2",
            "BuildingTicker": "AAF",
            "TimeMs": 172800000,
            "Inputs": [
                {"Ticker": "BMF", "Amount": "1"},
                {"Ticker": "SNM", "Amount": "1"},
            ],
            "Outputs": [{"Ticker": "NV2", "Amount": "1"}],
        },
        {
            "RecipeName": "10xH2O-5xOVE=>2xRAT",
            "StandardRecipeName": "FFP:10xH2O-5xOVE=>2xRAT",
            "BuildingTicker": "FFP",
            "TimeMs": 3600000,
            "Inputs": [
                {"Ticker": "H2O", "Amount": "10"},
                {"Ticker": "OVE", "Amount": "5"},
            ],
            "Outputs": [{"Ticker": "RAT", "Amount": "2"}],
        },
    ]


@pytest.fixture
def example_material_data():
    return [
        {
            "MaterialId": "9788890100fd2191fb065cb0d5e624cb",
            "Ticker": "AAR",
            "Name": "antennaArray",
            "CategoryName": "electronic devices",
            "Weight": "0.78",
            "Volume": "0.5",
        },
        {
            "MaterialId": "820d081096fd3e8fbd98b4344f6250ad",
            "Ticker": "H2O",
            "Name": "Water",
            "CategoryName": "Resources",
            "Weight": "1.0",
            "Volume": "1.0",
        },
    ]


@pytest.fixture
def example_building_data():
    return [
        {
            "BuildingCosts": [
                {
                    "CommodityName": "basicStructuralElements",
                    "CommodityTicker": "BSE",
                    "Weight": 0.30000001192092896,
                    "Volume": 0.5,
                    "Amount": 12,
                }
            ],
            "Recipes": [
                {
                    "Inputs": [],
                    "Outputs": [],
                    "BuildingRecipeId": "@RIG=>",
                    "DurationMs": 17280000,
                    "RecipeName": "=>",
                    "StandardRecipeName": "RIG:=>",
                }
            ],
            "BuildingId": "00e3d3d9ac2fc9ba7cac62519915dc43",
            "Name": "rig",
            "Ticker": "RIG",
            "Expertise": "RESOURCE_EXTRACTION",
            "Pioneers": 30,
            "Settlers": 0,
            "Technicians": 0,
            "Engineers": 0,
            "Scientists": 0,
            "AreaCost": 10,
            "UserNameSubmitted": "SAGANAKI",
            "Timestamp": "2024-11-18T21:45:44.271567",
        },
        {
            "BuildingCosts": [
                {
                    "CommodityName": "lightweightBulkhead",
                    "CommodityTicker": "LBH",
                    "Weight": 0.20000000298023224,
                    "Volume": 0.6000000238418579,
                    "Amount": 6,
                },
                {
                    "CommodityName": "truss",
                    "CommodityTicker": "TRU",
                    "Weight": 0.10000000149011612,
                    "Volume": 1.5,
                    "Amount": 8,
                },
            ],
            "Recipes": [
                {
                    "Inputs": [
                        {
                            "CommodityName": "chemicalReagents",
                            "CommodityTicker": "REA",
                            "Weight": 0.05000000074505806,
                            "Volume": 0.05000000074505806,
                            "Amount": 4,
                        }
                    ],
                    "Outputs": [
                        {
                            "CommodityName": "enrichedTechnetium",
                            "CommodityTicker": "ETC",
                            "Weight": 4.099999904632568,
                            "Volume": 1,
                            "Amount": 1,
                        }
                    ],
                    "BuildingRecipeId": "1xTC 4xREA 4xFLX@TNP=>1xETC",
                    "DurationMs": 69120000,
                    "RecipeName": "1xTC 4xREA 4xFLX=>1xETC",
                    "StandardRecipeName": "TNP:4xFLX-4xREA-1xTC=>1xETC",
                }
            ],
            "BuildingId": "0473a002be6c4feb92433cc819e10b5d",
            "Name": "technetiumProcessing",
            "Ticker": "TNP",
            "Expertise": None,  # Test optional expertise
            "Pioneers": 0,
            "Settlers": 0,
            "Technicians": 80,
            "Engineers": 0,
            "Scientists": 0,
            "AreaCost": 30,
            "UserNameSubmitted": "SAGANAKI",
            "Timestamp": "2025-01-23T00:14:03.667814",
        },
    ]


@pytest.fixture
def example_planet_data():
    return [
        {"PlanetNaturalId": "PG-241h", "PlanetName": "PG-241h"},
        {"PlanetNaturalId": "NL-534a", "PlanetName": "NL-534a"},
        {"PlanetNaturalId": "NL-044b", "PlanetName": "NL-044b"},
    ]


@pytest.fixture
def example_system_data():
    return [
        {
            "Connections": [
                {
                    "SystemConnectionId": "014421a50088da622befe22fe1b12e7e-1ef59a64aa3e127f820a71be9b4d6716",
                    "ConnectingId": "1ef59a64aa3e127f820a71be9b4d6716",
                },
                {
                    "SystemConnectionId": "014421a50088da622befe22fe1b12e7e-58352be19029146f3fde30b40fb550eb",
                    "ConnectingId": "58352be19029146f3fde30b40fb550eb",
                },
            ],
            "SystemId": "014421a50088da622befe22fe1b12e7e",
            "Name": "YK-024",
            "NaturalId": "YK-024",
            "Type": "K",
            "PositionX": 409.50921630859375,
            "PositionY": -16.564367294311523,
            "PositionZ": 92.88360595703125,
            "SectorId": "sector-46",
            "SubSectorId": "subsector-46-9",
            "UserNameSubmitted": "SAGANAKI",
            "Timestamp": "2025-04-23T21:26:33.113509",
        },
        {
            "Connections": [
                {
                    "SystemConnectionId": "01616c4dc3d9d62eeb16bb863ccb3e0e-0b6bd15be768750c4e030edbcb402e87",
                    "ConnectingId": "0b6bd15be768750c4e030edbcb402e87",
                }
            ],
            "SystemId": "01616c4dc3d9d62eeb16bb863ccb3e0e",
            "Name": "XU-753",
            "NaturalId": "XU-753",
            "Type": "G",
            "PositionX": -808.9539794921875,
            "PositionY": -183.02001953125,
            "PositionZ": 141.99322509765625,
            "SectorId": "sector-97",
            "SubSectorId": "subsector-97-22",
            "UserNameSubmitted": "SAGANAKI",
            "Timestamp": "2025-04-23T21:26:33.113509",
        },
    ]


@pytest.fixture
def example_workforce_needs_data():
    return [
        {
            "Needs": [
                {
                    "MaterialId": "9788890100fd2191fb065cb0d5e624cb",
                    "MaterialName": "pioneerClothing",
                    "MaterialTicker": "OVE",
                    "MaterialCategory": "3f047ec3043bdd795fd7272d6be98799",
                    "Amount": 0.5,
                },
                {
                    "MaterialId": "820d081096fd3e8fbd98b4344f6250ad",
                    "MaterialName": "pioneerLuxuryClothing",
                    "MaterialTicker": "PWO",
                    "MaterialCategory": "8a0bd8b6a329c3d632da9da63c818b3d",
                    "Amount": 0.20000000298023224,
                },
            ],
            "WorkforceType": "PIONEER",
        },
        {
            "Needs": [
                {
                    "MaterialId": "a1d1d61f8085de53455dd4e8a7813788",
                    "MaterialName": "settlerLuxuryDrink",
                    "MaterialTicker": "KOM",
                    "MaterialCategory": "8a0bd8b6a329c3d632da9da63c818b3d",
                    "Amount": 1,
                },
                {
                    "MaterialId": "83dd61885cf6879ff49fe1419f068f10",
                    "MaterialName": "rations",
                    "MaterialTicker": "RAT",
                    "MaterialCategory": "3f047ec3043bdd795fd7272d6be98799",
                    "Amount": 6,
                },
            ],
            "WorkforceType": "SETTLER",
        },
    ]


@pytest.fixture
def example_comex_exchange_data():
    return [
        {
            "ComexExchangeId": "428b9f5cf86d62bbb29f9485f10a88d3",
            "ExchangeName": "Hortus Station Commodity Exchange",
            "ExchangeCode": "IC1",
            "ExchangeOperatorId": None,
            "ExchangeOperatorCode": None,
            "ExchangeOperatorName": None,
            "CurrencyNumericCode": 5,
            "CurrencyCode": "ICA",
            "CurrencyName": "Austral",
            "CurrencyDecimals": 2,
            "LocationId": "0deca369a92788b8079e7ac245be66f7",
            "LocationName": "Hortus Station",
            "LocationNaturalId": "HRT",
        },
        {
            "ComexExchangeId": "076fa603217bd9f5e6d0e1338cdfd9c5",
            "ExchangeName": "Moria Station Commodity Exchange",
            "ExchangeCode": "NC1",
            "ExchangeOperatorId": None,
            "ExchangeOperatorCode": None,
            "ExchangeOperatorName": None,
            "CurrencyNumericCode": 4,
            "CurrencyCode": "NCC",
            "CurrencyName": "NCE Coupons",
            "CurrencyDecimals": 2,
            "LocationId": "299e4c9b1d2d9fc0f45340cf7e54e005",
            "LocationName": "Moria Station",
            "LocationNaturalId": "MOR",
        },
    ]


@pytest.fixture
def mock_http_error_session():
    """Fixture that creates a mock session that raises HTTP errors."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    return mock_session


def test_parse_price_data(example_price_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_price_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()

        # Test AAR data
        prices = client.get_prices(material_ticker="AAR")
        assert len(prices) == 2  # Should have AI1 and CI1 entries

        # Find AI1 exchange data
        ai1_price = next(p for p in prices if p.exchange == "AI1")
        assert ai1_price.material_ticker == "AAR"
        assert ai1_price.average_price == 15100
        assert ai1_price.ask_amount == 58
        assert ai1_price.ask_price == 15000
        assert ai1_price.ask_available == 178
        assert ai1_price.bid_amount is None
        assert ai1_price.bid_price is None
        assert ai1_price.bid_available == 0

        # Test ABH data
        prices = client.get_prices(material_ticker="ABH")
        assert len(prices) == 1

        # Find AI1 exchange data
        ai1_price = next(p for p in prices if p.exchange == "AI1")
        assert ai1_price.material_ticker == "ABH"
        assert ai1_price.average_price == 47830.12109375
        assert ai1_price.ask_amount == 84
        assert ai1_price.ask_price == 50900
        assert ai1_price.ask_available == 781
        assert ai1_price.bid_amount == 79
        assert ai1_price.bid_price == 45200
        assert ai1_price.bid_available == 387

        # Test ADR data with MM prices
        prices = client.get_prices(material_ticker="ADR")
        assert len(prices) == 1

        # Find AI1 exchange data
        ai1_price = next(p for p in prices if p.exchange == "AI1")
        assert ai1_price.material_ticker == "ADR"
        assert ai1_price.mm_buy == 58000
        assert ai1_price.mm_sell is None
        assert ai1_price.average_price == 60000
        assert ai1_price.ask_amount == 32
        assert ai1_price.ask_price == 69000
        assert ai1_price.ask_available == 72
        assert ai1_price.bid_amount == 1
        assert ai1_price.bid_price == 58100
        assert ai1_price.bid_available == 101


def test_filter_by_exchange(example_price_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_price_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()

        # Test filtering by exchange
        prices = client.get_prices(exchange="CI1")
        assert len(prices) == 1

        # All prices should be from CI1 exchange
        assert all(p.exchange == "CI1" for p in prices)

        # Test specific CI1 data for AAR
        aar_ci1 = next(p for p in prices if p.material_ticker == "AAR")
        assert aar_ci1.average_price == 14900
        assert aar_ci1.ask_amount == 217
        assert aar_ci1.ask_price == 14900
        assert aar_ci1.ask_available == 513
        assert aar_ci1.bid_amount is None
        assert aar_ci1.bid_price is None
        assert aar_ci1.bid_available == 0


def test_get_recipes_success(example_recipe_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_recipe_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        recipes = client.get_recipes()

        assert len(recipes) == 2

        # Test first recipe
        recipe1 = recipes[0]
        assert recipe1.recipe_name == "1xBMF-1xSNM=>1xNV2"
        assert recipe1.building_ticker == "AAF"
        assert recipe1.time_ms == 172800000
        assert len(recipe1.inputs) == 2
        assert recipe1.inputs[0].ticker == "BMF"
        assert recipe1.inputs[0].amount == 1
        assert recipe1.inputs[1].ticker == "SNM"
        assert recipe1.inputs[1].amount == 1
        assert len(recipe1.outputs) == 1
        assert recipe1.outputs[0].ticker == "NV2"
        assert recipe1.outputs[0].amount == 1

        # Test second recipe
        recipe2 = recipes[1]
        assert recipe2.recipe_name == "10xH2O-5xOVE=>2xRAT"
        assert recipe2.building_ticker == "FFP"
        assert recipe2.time_ms == 3600000
        assert len(recipe2.inputs) == 2
        assert recipe2.inputs[0].ticker == "H2O"
        assert recipe2.inputs[0].amount == 10
        assert recipe2.inputs[1].ticker == "OVE"
        assert recipe2.inputs[1].amount == 5
        assert len(recipe2.outputs) == 1
        assert recipe2.outputs[0].ticker == "RAT"
        assert recipe2.outputs[0].amount == 2


def test_get_recipes_http_error(mock_http_error_session):
    """Test that get_recipes properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_recipes()
        assert "404 Not Found" in str(exc_info.value)


def test_get_recipes_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_recipes()


def test_get_all_materials_success(example_material_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_material_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        materials = client.get_all_materials()

        assert len(materials) == 2

        # Test first material
        material1 = materials[0]
        assert material1.ticker == "AAR"
        assert material1.name == "antennaArray"
        assert material1.category == "electronic devices"
        assert material1.weight == 0.78
        assert material1.volume == 0.5

        # Test second material
        material2 = materials[1]
        assert material2.ticker == "H2O"
        assert material2.name == "Water"
        assert material2.category == "Resources"
        assert material2.weight == 1.0
        assert material2.volume == 1.0


def test_get_all_materials_http_error(mock_http_error_session):
    """Test that get_all_materials properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_all_materials()
        assert "404 Not Found" in str(exc_info.value)


def test_get_all_materials_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_all_materials()


def test_get_building_details_success(example_building_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_building_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        buildings = client.get_buildings()

        assert len(buildings) == 2

        # Test first building (RIG)
        building1 = buildings[0]
        assert building1.building_id == "00e3d3d9ac2fc9ba7cac62519915dc43"
        assert building1.name == "rig"
        assert building1.ticker == "RIG"
        assert building1.expertise == "RESOURCE_EXTRACTION"
        assert building1.pioneers == 30
        assert building1.settlers == 0
        assert building1.technicians == 0
        assert building1.engineers == 0
        assert building1.scientists == 0
        assert building1.area_cost == 10
        assert building1.user_name_submitted == "SAGANAKI"
        assert building1.timestamp == datetime.fromisoformat(
            "2024-11-18T21:45:44.271567"
        )

        # Test building costs
        assert len(building1.building_costs) == 1
        cost = building1.building_costs[0]
        assert cost.commodity_name == "basicStructuralElements"
        assert cost.commodity_ticker == "BSE"
        assert cost.weight == 0.30000001192092896
        assert cost.volume == 0.5
        assert cost.amount == 12

        # Test recipes
        assert len(building1.recipes) == 1
        recipe = building1.recipes[0]
        assert recipe.building_recipe_id == "@RIG=>"
        assert recipe.duration_ms == 17280000
        assert recipe.recipe_name == "=>"
        assert recipe.standard_recipe_name == "RIG:=>"
        assert len(recipe.inputs) == 0
        assert len(recipe.outputs) == 0

        # Test second building (TNP)
        building2 = buildings[1]
        assert building2.building_id == "0473a002be6c4feb92433cc819e10b5d"
        assert building2.name == "technetiumProcessing"
        assert building2.ticker == "TNP"
        assert building2.expertise is None  # Test optional expertise
        assert building2.pioneers == 0
        assert building2.settlers == 0
        assert building2.technicians == 80
        assert building2.engineers == 0
        assert building2.scientists == 0
        assert building2.area_cost == 30
        assert building2.user_name_submitted == "SAGANAKI"
        assert building2.timestamp == datetime.fromisoformat(
            "2025-01-23T00:14:03.667814"
        )

        # Test building costs with multiple items
        assert len(building2.building_costs) == 2
        cost1 = building2.building_costs[0]
        assert cost1.commodity_name == "lightweightBulkhead"
        assert cost1.commodity_ticker == "LBH"
        assert cost1.weight == 0.20000000298023224
        assert cost1.volume == 0.6000000238418579
        assert cost1.amount == 6

        cost2 = building2.building_costs[1]
        assert cost2.commodity_name == "truss"
        assert cost2.commodity_ticker == "TRU"
        assert cost2.weight == 0.10000000149011612
        assert cost2.volume == 1.5
        assert cost2.amount == 8

        # Test recipes with inputs and outputs
        assert len(building2.recipes) == 1
        recipe = building2.recipes[0]
        assert recipe.building_recipe_id == "1xTC 4xREA 4xFLX@TNP=>1xETC"
        assert recipe.duration_ms == 69120000
        assert recipe.recipe_name == "1xTC 4xREA 4xFLX=>1xETC"
        assert recipe.standard_recipe_name == "TNP:4xFLX-4xREA-1xTC=>1xETC"

        # Test recipe inputs
        assert len(recipe.inputs) == 1
        input = recipe.inputs[0]
        assert input.commodity_name == "chemicalReagents"
        assert input.commodity_ticker == "REA"
        assert input.weight == 0.05000000074505806
        assert input.volume == 0.05000000074505806
        assert input.amount == 4

        # Test recipe outputs
        assert len(recipe.outputs) == 1
        output = recipe.outputs[0]
        assert output.commodity_name == "enrichedTechnetium"
        assert output.commodity_ticker == "ETC"
        assert output.weight == 4.099999904632568
        assert output.volume == 1
        assert output.amount == 1


def test_get_building_details_http_error(mock_http_error_session):
    """Test that get_building_details properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_buildings()
        assert "404 Not Found" in str(exc_info.value)


def test_get_building_details_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_buildings()


def test_get_planets_success(example_planet_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_planet_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        planets = client.get_planets()

        assert len(planets) == 3

        # Test first planet
        planet1 = planets[0]
        assert planet1.planet_natural_id == "PG-241h"
        assert planet1.planet_name == "PG-241h"

        # Test second planet
        planet2 = planets[1]
        assert planet2.planet_natural_id == "NL-534a"
        assert planet2.planet_name == "NL-534a"

        # Test third planet
        planet3 = planets[2]
        assert planet3.planet_natural_id == "NL-044b"
        assert planet3.planet_name == "NL-044b"


def test_get_planets_http_error(mock_http_error_session):
    """Test that get_planets properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_planets()
        assert "404 Not Found" in str(exc_info.value)


def test_get_planets_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_planets()


def test_get_systems_success(example_system_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_system_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        systems = client.get_systems()

        assert len(systems) == 2

        # Test first system
        system1 = systems[0]
        assert system1.system_id == "014421a50088da622befe22fe1b12e7e"
        assert system1.name == "YK-024"
        assert system1.natural_id == "YK-024"
        assert system1.type == "K"
        assert system1.position_x == 409.50921630859375
        assert system1.position_y == -16.564367294311523
        assert system1.position_z == 92.88360595703125
        assert system1.sector_id == "sector-46"
        assert system1.sub_sector_id == "subsector-46-9"
        assert system1.user_name_submitted == "SAGANAKI"
        assert system1.timestamp == datetime.fromisoformat("2025-04-23T21:26:33.113509")

        # Test system connections
        assert len(system1.connections) == 2
        conn1 = system1.connections[0]
        assert (
            conn1.system_connection_id
            == "014421a50088da622befe22fe1b12e7e-1ef59a64aa3e127f820a71be9b4d6716"
        )
        assert conn1.connecting_id == "1ef59a64aa3e127f820a71be9b4d6716"

        conn2 = system1.connections[1]
        assert (
            conn2.system_connection_id
            == "014421a50088da622befe22fe1b12e7e-58352be19029146f3fde30b40fb550eb"
        )
        assert conn2.connecting_id == "58352be19029146f3fde30b40fb550eb"

        # Test second system
        system2 = systems[1]
        assert system2.system_id == "01616c4dc3d9d62eeb16bb863ccb3e0e"
        assert system2.name == "XU-753"
        assert system2.natural_id == "XU-753"
        assert system2.type == "G"
        assert system2.position_x == -808.9539794921875
        assert system2.position_y == -183.02001953125
        assert system2.position_z == 141.99322509765625
        assert system2.sector_id == "sector-97"
        assert system2.sub_sector_id == "subsector-97-22"
        assert system2.user_name_submitted == "SAGANAKI"
        assert system2.timestamp == datetime.fromisoformat("2025-04-23T21:26:33.113509")

        # Test system connections
        assert len(system2.connections) == 1
        conn = system2.connections[0]
        assert (
            conn.system_connection_id
            == "01616c4dc3d9d62eeb16bb863ccb3e0e-0b6bd15be768750c4e030edbcb402e87"
        )
        assert conn.connecting_id == "0b6bd15be768750c4e030edbcb402e87"


def test_get_systems_http_error(mock_http_error_session):
    """Test that get_systems properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_systems()
        assert "404 Not Found" in str(exc_info.value)


def test_get_systems_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_systems()


def test_get_workforce_needs_success(example_workforce_needs_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_workforce_needs_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        needs = client.get_workforce_needs()

        assert len(needs) == 2

        # Test pioneer needs
        pioneer_needs = next(n for n in needs if n.workforce_type == "PIONEER")
        assert len(pioneer_needs.needs) == 2

        need1 = pioneer_needs.needs[0]
        assert need1.material_id == "9788890100fd2191fb065cb0d5e624cb"
        assert need1.material_name == "pioneerClothing"
        assert need1.material_ticker == "OVE"
        assert need1.material_category == "3f047ec3043bdd795fd7272d6be98799"
        assert need1.amount == 0.5

        need2 = pioneer_needs.needs[1]
        assert need2.material_id == "820d081096fd3e8fbd98b4344f6250ad"
        assert need2.material_name == "pioneerLuxuryClothing"
        assert need2.material_ticker == "PWO"
        assert need2.material_category == "8a0bd8b6a329c3d632da9da63c818b3d"
        assert need2.amount == 0.20000000298023224

        # Test settler needs
        settler_needs = next(n for n in needs if n.workforce_type == "SETTLER")
        assert len(settler_needs.needs) == 2

        need1 = settler_needs.needs[0]
        assert need1.material_id == "a1d1d61f8085de53455dd4e8a7813788"
        assert need1.material_name == "settlerLuxuryDrink"
        assert need1.material_ticker == "KOM"
        assert need1.material_category == "8a0bd8b6a329c3d632da9da63c818b3d"
        assert need1.amount == 1

        need2 = settler_needs.needs[1]
        assert need2.material_id == "83dd61885cf6879ff49fe1419f068f10"
        assert need2.material_name == "rations"
        assert need2.material_ticker == "RAT"
        assert need2.material_category == "3f047ec3043bdd795fd7272d6be98799"
        assert need2.amount == 6


def test_get_workforce_needs_http_error(mock_http_error_session):
    """Test that get_workforce_needs properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_workforce_needs()
        assert "404 Not Found" in str(exc_info.value)


def test_get_workforce_needs_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_workforce_needs()


def test_get_comex_exchanges_success(example_comex_exchange_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_comex_exchange_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        exchanges = client.get_comex_exchanges()

        assert len(exchanges) == 2

        # Test first exchange
        exchange1 = exchanges[0]
        assert exchange1.comex_exchange_id == "428b9f5cf86d62bbb29f9485f10a88d3"
        assert exchange1.exchange_name == "Hortus Station Commodity Exchange"
        assert exchange1.exchange_code == "IC1"
        assert exchange1.exchange_operator_id is None
        assert exchange1.exchange_operator_code is None
        assert exchange1.exchange_operator_name is None
        assert exchange1.currency_numeric_code == 5
        assert exchange1.currency_code == "ICA"
        assert exchange1.currency_name == "Austral"
        assert exchange1.currency_decimals == 2
        assert exchange1.location_id == "0deca369a92788b8079e7ac245be66f7"
        assert exchange1.location_name == "Hortus Station"
        assert exchange1.location_natural_id == "HRT"

        # Test second exchange
        exchange2 = exchanges[1]
        assert exchange2.comex_exchange_id == "076fa603217bd9f5e6d0e1338cdfd9c5"
        assert exchange2.exchange_name == "Moria Station Commodity Exchange"
        assert exchange2.exchange_code == "NC1"
        assert exchange2.exchange_operator_id is None
        assert exchange2.exchange_operator_code is None
        assert exchange2.exchange_operator_name is None
        assert exchange2.currency_numeric_code == 4
        assert exchange2.currency_code == "NCC"
        assert exchange2.currency_name == "NCE Coupons"
        assert exchange2.currency_decimals == 2
        assert exchange2.location_id == "299e4c9b1d2d9fc0f45340cf7e54e005"
        assert exchange2.location_name == "Moria Station"
        assert exchange2.location_natural_id == "MOR"


def test_get_comex_exchanges_http_error(mock_http_error_session):
    """Test that get_comex_exchanges properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_comex_exchanges()
        assert "404 Not Found" in str(exc_info.value)


def test_get_comex_exchanges_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_comex_exchanges()


def test_login_success():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"auth_token": "test-token-123"}
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        token = client.authenticate("test_user", "test_password")

        assert token == "test-token-123"
        assert client._auth_token == "test-token-123"
        assert client.headers["Authorization"] == "Bearer test-token-123"

        # Verify the request was made correctly
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args[1]
        assert call_args["json"] == {
            "username": "test_user",
            "password": "test_password",
        }


def test_login_http_error():
    """Test that authenticate properly handles HTTP errors with specific unauthorized error."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.authenticate("test_user", "test_password")
        assert "401 Unauthorized" in str(exc_info.value)


def test_login_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_session.post.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.authenticate("test_user", "test_password")


def test_get_json_http_error(mock_http_error_session):
    """Test that _get_json properly raises HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client._get_json("test/endpoint")
        assert "404 Not Found" in str(exc_info.value)


@pytest.fixture
def example_site_data():
    return [
        {
            "Buildings": [
                {
                    "ReclaimableMaterials": [
                        {
                            "MaterialId": "cc5fb1618f0506e80bfbcee9ae2605ab",
                            "MaterialName": "mineralConstructionGranulate",
                            "MaterialTicker": "MCG",
                            "MaterialAmount": 30,
                        },
                        {
                            "MaterialId": "6bbdf7d0503153753c8cb23653a4d22b",
                            "MaterialName": "basicStructuralElements",
                            "MaterialTicker": "BSE",
                            "MaterialAmount": 1,
                        },
                    ],
                    "RepairMaterials": [],
                    "SiteBuildingId": "b45fe358ce67b71114b25a95c969d20f-01d9bb37f1d803ea65a44d6f86f08379",
                    "BuildingId": "01d9bb37f1d803ea65a44d6f86f08379",
                    "BuildingCreated": 1741702023930,
                    "BuildingName": "habitationPioneer",
                    "BuildingTicker": "HB1",
                    "BuildingLastRepair": None,
                    "Condition": 0.9892963767051697,
                }
            ],
            "SiteId": "b45fe358ce67b71114b25a95c969d20f",
            "PlanetId": "9e328375bb2f8bdaf0b5e0d270120339",
            "PlanetIdentifier": "ZV-759c",
            "PlanetName": "Deimos",
            "PlanetFoundedEpochMs": 1741643185610,
            "InvestedPermits": 1,
            "MaximumPermits": 3,
            "UserNameSubmitted": "CORPORATEJESTER",
            "Timestamp": "2025-04-23T23:51:53.006653",
        }
    ]


def test_get_sites_success(example_site_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_site_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        sites = client.get_sites("CORPORATEJESTER")

        assert len(sites) == 1

        # Test site data
        site = sites[0]
        assert site.site_id == "b45fe358ce67b71114b25a95c969d20f"
        assert site.planet_id == "9e328375bb2f8bdaf0b5e0d270120339"
        assert site.planet_identifier == "ZV-759c"
        assert site.planet_name == "Deimos"
        assert site.planet_founded_epoch_ms == 1741643185610
        assert site.invested_permits == 1
        assert site.maximum_permits == 3
        assert site.user_name_submitted == "CORPORATEJESTER"
        assert site.timestamp == datetime.fromisoformat("2025-04-23T23:51:53.006653")

        # Test building data
        assert len(site.buildings) == 1
        building = site.buildings[0]
        assert (
            building.site_building_id
            == "b45fe358ce67b71114b25a95c969d20f-01d9bb37f1d803ea65a44d6f86f08379"
        )
        assert building.building_id == "01d9bb37f1d803ea65a44d6f86f08379"
        assert building.building_created == 1741702023930
        assert building.building_name == "habitationPioneer"
        assert building.building_ticker == "HB1"
        assert building.building_last_repair is None
        assert building.condition == 0.9892963767051697

        # Test reclaimable materials
        assert len(building.reclaimable_materials) == 2
        material1 = building.reclaimable_materials[0]
        assert material1.material_id == "cc5fb1618f0506e80bfbcee9ae2605ab"
        assert material1.material_name == "mineralConstructionGranulate"
        assert material1.material_ticker == "MCG"
        assert material1.material_amount == 30

        material2 = building.reclaimable_materials[1]
        assert material2.material_id == "6bbdf7d0503153753c8cb23653a4d22b"
        assert material2.material_name == "basicStructuralElements"
        assert material2.material_ticker == "BSE"
        assert material2.material_amount == 1

        # Test repair materials
        assert len(building.repair_materials) == 0


def test_get_sites_http_error(mock_http_error_session):
    """Test that get_sites properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_sites("CORPORATEJESTER")
        assert "404 Not Found" in str(exc_info.value)


def test_get_sites_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_sites("CORPORATEJESTER")


@pytest.fixture
def example_storage_data():
    return [
        {
            "StorageItems": [
                {
                    "MaterialId": "7756a0779efe67f0f293f41eda4944d4",
                    "MaterialName": "stlFuel",
                    "MaterialTicker": "SF",
                    "MaterialCategory": "ba98fa0cf77040a96cd8a608ad0d08e9",
                    "MaterialWeight": 0.05999999865889549,
                    "MaterialVolume": 0.05999999865889549,
                    "MaterialAmount": 2008,
                    "MaterialValue": 33397.32,
                    "MaterialValueCurrency": "AIC",
                    "Type": "INVENTORY",
                    "TotalWeight": 120.4800033569336,
                    "TotalVolume": 120.4800033569336,
                }
            ],
            "StorageId": "1fe42efc53038a12b02e6a822ac68fa9",
            "AddressableId": "328575592815e68bdc8a1c957da76b06",
            "Name": "2. Two",
            "WeightLoad": 120.4800033569336,
            "WeightCapacity": 210,
            "VolumeLoad": 120.4800033569336,
            "VolumeCapacity": 210,
            "FixedStore": False,
            "Type": "STL_FUEL_STORE",
            "UserNameSubmitted": "CORPORATEJESTER",
            "Timestamp": "2025-04-24T23:58:48.280423",
        },
        {
            "StorageItems": [],
            "StorageId": "2492f0abb50ac225cbfa5586568bcb07",
            "AddressableId": "f4b1b26152a82646387f1189cc293348",
            "Name": None,
            "WeightLoad": 0,
            "WeightCapacity": 3000,
            "VolumeLoad": 0,
            "VolumeCapacity": 3000,
            "FixedStore": True,
            "Type": "WAREHOUSE_STORE",
            "UserNameSubmitted": "CORPORATEJESTER",
            "Timestamp": "2025-04-24T23:58:48.280423",
        },
    ]


def test_get_storage_success(example_storage_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_storage_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        storage = client.get_storage("CORPORATEJESTER")

        assert len(storage) == 2

        # Test first storage (STL_FUEL_STORE)
        store1 = storage[0]
        assert store1.storage_id == "1fe42efc53038a12b02e6a822ac68fa9"
        assert store1.addressable_id == "328575592815e68bdc8a1c957da76b06"
        assert store1.name == "2. Two"
        assert store1.weight_load == 120.4800033569336
        assert store1.weight_capacity == 210
        assert store1.volume_load == 120.4800033569336
        assert store1.volume_capacity == 210
        assert store1.fixed_store is False
        assert store1.type == "STL_FUEL_STORE"
        assert store1.user_name_submitted == "CORPORATEJESTER"
        assert store1.timestamp == datetime.fromisoformat("2025-04-24T23:58:48.280423")

        # Test storage items
        assert len(store1.storage_items) == 1
        item = store1.storage_items[0]
        assert item.material_id == "7756a0779efe67f0f293f41eda4944d4"
        assert item.material_name == "stlFuel"
        assert item.material_ticker == "SF"
        assert item.material_category == "ba98fa0cf77040a96cd8a608ad0d08e9"
        assert item.material_weight == 0.05999999865889549
        assert item.material_volume == 0.05999999865889549
        assert item.material_amount == 2008
        assert item.material_value == 33397.32
        assert item.material_value_currency == "AIC"
        assert item.type == "INVENTORY"
        assert item.total_weight == 120.4800033569336
        assert item.total_volume == 120.4800033569336

        # Test second storage (WAREHOUSE_STORE)
        store2 = storage[1]
        assert store2.storage_id == "2492f0abb50ac225cbfa5586568bcb07"
        assert store2.addressable_id == "f4b1b26152a82646387f1189cc293348"
        assert store2.name is None
        assert store2.weight_load == 0
        assert store2.weight_capacity == 3000
        assert store2.volume_load == 0
        assert store2.volume_capacity == 3000
        assert store2.fixed_store is True
        assert store2.type == "WAREHOUSE_STORE"
        assert store2.user_name_submitted == "CORPORATEJESTER"
        assert store2.timestamp == datetime.fromisoformat("2025-04-24T23:58:48.280423")
        assert len(store2.storage_items) == 0


def test_get_storage_http_error(mock_http_error_session):
    """Test that get_storage properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_storage("CORPORATEJESTER")
        assert "404 Not Found" in str(exc_info.value)


def test_get_storage_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_storage("CORPORATEJESTER")


@pytest.fixture
def example_warehouse_data():
    return [
        {
            "WarehouseId": "4ff3a6e5bc6d6a5dac0ac6da6d60ccbe-f798a011ff80b47922677ce90253037a",
            "StoreId": "f798a011ff80b47922677ce90253037a",
            "Units": 3,
            "WeightCapacity": 1500,
            "VolumeCapacity": 1500,
            "NextPaymentTimestampEpochMs": 1746134266859,
            "FeeAmount": 450,
            "FeeCurrency": "AIC",
            "FeeCollectorId": None,
            "FeeCollectorName": None,
            "FeeCollectorCode": None,
            "LocationName": "Hephaestus",
            "LocationNaturalId": "ZV-307c",
            "UserNameSubmitted": "CORPORATEJESTER",
            "Timestamp": "2025-04-24T23:58:48.586578",
        },
        {
            "WarehouseId": "f4b1b26152a82646387f1189cc293348-2492f0abb50ac225cbfa5586568bcb07",
            "StoreId": "2492f0abb50ac225cbfa5586568bcb07",
            "Units": 6,
            "WeightCapacity": 3000,
            "VolumeCapacity": 3000,
            "NextPaymentTimestampEpochMs": 1746057468945,
            "FeeAmount": 450,
            "FeeCurrency": "AIC",
            "FeeCollectorId": None,
            "FeeCollectorName": None,
            "FeeCollectorCode": None,
            "LocationName": "Griffonstone",
            "LocationNaturalId": "LS-300c",
            "UserNameSubmitted": "CORPORATEJESTER",
            "Timestamp": "2025-04-24T23:58:48.586578",
        },
    ]


def test_get_warehouses_success(example_warehouse_data):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = example_warehouse_data
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        warehouses = client.get_warehouses("CORPORATEJESTER")

        assert len(warehouses) == 2

        # Test first warehouse
        warehouse1 = warehouses[0]
        assert (
            warehouse1.warehouse_id
            == "4ff3a6e5bc6d6a5dac0ac6da6d60ccbe-f798a011ff80b47922677ce90253037a"
        )
        assert warehouse1.store_id == "f798a011ff80b47922677ce90253037a"
        assert warehouse1.units == 3
        assert warehouse1.weight_capacity == 1500
        assert warehouse1.volume_capacity == 1500
        assert warehouse1.next_payment_timestamp_epoch_ms == 1746134266859
        assert warehouse1.fee_amount == 450
        assert warehouse1.fee_currency == "AIC"
        assert warehouse1.fee_collector_id is None
        assert warehouse1.fee_collector_name is None
        assert warehouse1.fee_collector_code is None
        assert warehouse1.location_name == "Hephaestus"
        assert warehouse1.location_natural_id == "ZV-307c"
        assert warehouse1.user_name_submitted == "CORPORATEJESTER"
        assert warehouse1.timestamp == datetime.fromisoformat(
            "2025-04-24T23:58:48.586578"
        )

        # Test second warehouse
        warehouse2 = warehouses[1]
        assert (
            warehouse2.warehouse_id
            == "f4b1b26152a82646387f1189cc293348-2492f0abb50ac225cbfa5586568bcb07"
        )
        assert warehouse2.store_id == "2492f0abb50ac225cbfa5586568bcb07"
        assert warehouse2.units == 6
        assert warehouse2.weight_capacity == 3000
        assert warehouse2.volume_capacity == 3000
        assert warehouse2.next_payment_timestamp_epoch_ms == 1746057468945
        assert warehouse2.fee_amount == 450
        assert warehouse2.fee_currency == "AIC"
        assert warehouse2.fee_collector_id is None
        assert warehouse2.fee_collector_name is None
        assert warehouse2.fee_collector_code is None
        assert warehouse2.location_name == "Griffonstone"
        assert warehouse2.location_natural_id == "LS-300c"
        assert warehouse2.user_name_submitted == "CORPORATEJESTER"
        assert warehouse2.timestamp == datetime.fromisoformat(
            "2025-04-24T23:58:48.586578"
        )


def test_get_warehouses_http_error(mock_http_error_session):
    """Test that get_warehouses properly handles HTTP errors."""
    with patch("requests.Session", return_value=mock_http_error_session):
        client = FIOClient()
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.get_warehouses("CORPORATEJESTER")
        assert "404 Not Found" in str(exc_info.value)


def test_get_warehouses_json_error():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.status_code = 200
    mock_session.get.return_value = mock_response

    with patch("requests.Session", return_value=mock_session):
        client = FIOClient()
        with pytest.raises(ValueError):
            client.get_warehouses("CORPORATEJESTER")
