from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from prun.database import Building, WorkforceNeed, ExchangePrice
from prun.interface import RepositoryInterface


class TestRepository(RepositoryInterface):
    """Simple in-memory repository for testing."""

    def __init__(self):
        self.workforce_needs: List[WorkforceNeed] = []
        self.exchange_prices: List[ExchangePrice] = []

    def get_workforce_needs(
        self, workforce_type: Optional[str] = None
    ) -> List[WorkforceNeed]:
        if workforce_type:
            return [
                n for n in self.workforce_needs if n.workforce_type == workforce_type
            ]
        return self.workforce_needs

    def get_latest_price(
        self, item_symbol: str, exchange_code: str = "AI1"
    ) -> Optional[ExchangePrice]:
        prices = [
            p
            for p in self.exchange_prices
            if p.item_symbol == item_symbol and p.exchange_code == exchange_code
        ]
        return max(prices, key=lambda p: p.timestamp) if prices else None

    # Implement other required methods with empty implementations for now
    def get_recipe(self, symbol: str) -> Optional[Any]:
        return None

    def get_item(self, symbol: str) -> Optional[Any]:
        return None

    def get_building(self, symbol: str) -> Optional[Any]:
        return None

    def get_system(self, system_id: str) -> Optional[Any]:
        return None

    def get_system_by_natural_id(self, natural_id: str) -> Optional[Any]:
        return None

    def get_planet(self, natural_id: str) -> Optional[Any]:
        return None

    def get_site(self, site_id: str) -> Optional[Any]:
        return None

    def get_site_building(self, site_building_id: str) -> Optional[Any]:
        return None

    def get_storage(self, storage_id: str) -> Optional[Any]:
        return None

    def get_warehouse(self, warehouse_id: str) -> Optional[Any]:
        return None

    def get_all_warehouses(self) -> List[Any]:
        return []

    def get_storage_items_with_prices(self) -> List[tuple[Any, ExchangePrice]]:
        return []

    def get_recipe_with_prices(
        self, symbol: str
    ) -> tuple[Any, List[tuple[Any, ExchangePrice]]]:
        return None, []

    def get_all_recipes_with_info(self) -> List[Dict[str, Any]]:
        return []

    def create_recipe(self, **kwargs) -> None:
        pass

    def create_exchange_price(self, **kwargs) -> None:
        pass

    def create_item(self, **kwargs) -> None:
        pass

    def create_building(self, **kwargs) -> None:
        pass

    def create_system(self, **kwargs) -> None:
        pass

    def create_planet(self, **kwargs) -> None:
        pass

    def create_site(self, **kwargs) -> None:
        pass

    def create_site_building(self, **kwargs) -> None:
        pass

    def create_site_building_material(self, **kwargs) -> None:
        pass

    def create_storage(self, **kwargs) -> None:
        pass

    def create_storage_item(self, **kwargs) -> None:
        pass

    def create_warehouse(self, **kwargs) -> None:
        pass

    def create_workforce_need(self, **kwargs) -> None:
        pass

    def delete_workforce_needs(self) -> None:
        pass

    def delete_comex_exchanges(self) -> None:
        pass

    def delete_sites(self) -> None:
        pass

    def delete_site_building_materials(self, site_building_id: str) -> None:
        pass

    def delete_storage_items(self, storage_id: str) -> None:
        pass
