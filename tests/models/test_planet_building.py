import unittest
from prun.models import PlanetBuilding, Building, Planet, BuildingCost


class TestBuildingFrom(unittest.TestCase):
    def setUp(self):
        # Mock a building
        self.building = Building(
            symbol="TEST_BUILDING",
            name="Test Building",
            area_cost=100,
            building_costs=[],
            recipes=[],
        )

    def test_surface_true(self):
        planet = Planet(surface=True, pressure=1.0, gravity=1.0, temperature=25)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(
            BuildingCost(item_symbol="MCG", amount=400), result.building_costs
        )

    def test_surface_false(self):
        planet = Planet(surface=False, pressure=1.0, gravity=1.0, temperature=25)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(
            BuildingCost(item_symbol="AEF", amount=33.33), result.building_costs
        )

    def test_low_pressure(self):
        planet = Planet(surface=True, pressure=0.2, gravity=1.0, temperature=25)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(
            BuildingCost(item_symbol="SEA", amount=100), result.building_costs
        )

    def test_high_pressure(self):
        planet = Planet(surface=True, pressure=3.0, gravity=1.0, temperature=25)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(BuildingCost(item_symbol="HSE", amount=1), result.building_costs)

    def test_low_gravity(self):
        planet = Planet(surface=True, pressure=1.0, gravity=0.2, temperature=25)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(BuildingCost(item_symbol="MGC", amount=1), result.building_costs)

    def test_high_gravity(self):
        planet = Planet(surface=True, pressure=1.0, gravity=3.0, temperature=25)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(BuildingCost(item_symbol="BL", amount=1), result.building_costs)

    def test_low_temperature(self):
        planet = Planet(surface=True, pressure=1.0, gravity=1.0, temperature=-30)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(
            BuildingCost(item_symbol="INS", amount=1000), result.building_costs
        )

    def test_high_temperature(self):
        planet = Planet(surface=True, pressure=1.0, gravity=1.0, temperature=80)
        result = PlanetBuilding.planet_building_from(self.building, planet)
        self.assertIn(BuildingCost(item_symbol="TSH", amount=1), result.building_costs)


if __name__ == "__main__":
    unittest.main()
