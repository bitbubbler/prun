import requests
import csv
import io
import logging
from typing import List, Optional, Dict, Any
from .models import (
    FIOMaterial,
    FIOBuilding,
    FIOBuildingRecipe,
    FIOPrice,
    FIORecipe,
    FIOBuildingRecipeDetail,
    FIOPlanet,
    FIOSystem,
    FIOWorkforceNeeds,
    FIOComexExchange,
    FIOSimulation,
    FIOAuthLoginRequest,
    FIOAuthLoginResponse,
    FIOSite,
    FIOStorage,
    FIOWarehouse,
)
from decimal import Decimal
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class FIOClient:
    """Client for interacting with the FIO API."""

    def __init__(self) -> None:
        """Initialize the FIO client."""
        self.base_url = "https://rest.fnar.net"
        self.headers = {"Accept": "text/csv"}
        self._auth_token: Optional[str] = None
        self._session = requests.Session()

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._auth_token is not None

    def authenticate(self, username: str, password: str) -> str:
        """Authenticate with the FIO API.

        Args:
            username: FIO username
            password: FIO password

        Returns:
            Authentication token

        Raises:
            requests.RequestException: If the login request fails
        """
        self._auth_token = self._get_auth_token(username, password)
        self.headers["Authorization"] = f"Bearer {self._auth_token}"
        return self._auth_token

    def _get_auth_token(self, username: str, password: str) -> str:
        """Get an authentication token from the FIO API.

        Args:
            username: FIO username
            password: FIO password

        Returns:
            Authentication token

        Raises:
            requests.RequestException: If the login request fails
        """
        url = f"{self.base_url}/auth/login"
        payload = FIOAuthLoginRequest(username=username, password=password)

        response = self._session.post(url, json=payload.model_dump())
        response.raise_for_status()
        data = response.json()
        return FIOAuthLoginResponse(**data).auth_token

    def _map_csv_to_model(
        self, data: Dict[str, Any], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Map CSV column names to model field names.

        Args:
            data: CSV data as dict
            mapping: Mapping from CSV column names to model field names

        Returns:
            Dict with model field names as keys
        """
        result = {
            model_field: data[csv_field] for csv_field, model_field in mapping.items()
        }
        return result

    def _get_csv(self, endpoint: str, authenticated: bool = False) -> List[dict]:
        """Get CSV data from an endpoint and parse it into a list of dicts.

        Args:
            endpoint: API endpoint to call
            is_authenticated: Whether to include auth token in request

        Returns:
            List of dicts containing the CSV data
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug("Fetching CSV from %s", url)

        headers = self.headers.copy()
        if authenticated and self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            text = response.text
            # Convert CSV to list of dicts
            reader = csv.DictReader(io.StringIO(text))
            return list(reader)
        except requests.RequestException as e:
            logger.error("Error fetching CSV from %s: %s", url, str(e))
            raise

    def _get_json(self, endpoint: str, authenticated: bool = False) -> Any:
        """Get JSON data from an endpoint and parse it into a list of dicts.

        Args:
            endpoint: API endpoint to call
            is_authenticated: Whether to include auth token in request

        Returns:
            List of dicts containing the JSON data

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug("Fetching JSON from %s", url)

        headers = self.headers.copy()
        if authenticated and self._auth_token:
            headers["Authorization"] = f"{self._auth_token}"

        response = self._session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_materials(self) -> List[FIOMaterial]:
        """Get all materials from the FIO API.

        Returns:
            List of materials
        """
        data = self._get_csv("csv/materials")
        mapping = {
            "Ticker": "ticker",
            "Name": "name",
            "Category": "category",
            "Weight": "weight",
            "Volume": "volume",
        }
        return [FIOMaterial(**self._map_csv_to_model(item, mapping)) for item in data]

    def get_all_materials(self) -> List[FIOMaterial]:
        """Get all materials from the FIO API using the JSON endpoint.

        Returns:
            List of materials
        """
        data = self._get_json("material/allmaterials")
        return [FIOMaterial(**item) for item in data]

    def get_recipes(self) -> List[FIORecipe]:
        """Get all recipes from the FIO API.

        Returns:
            List of recipes
        """
        data = self._get_json("recipes/allrecipes")
        return [FIORecipe(**recipe) for recipe in data]

    def get_prices(
        self, material_ticker: Optional[str] = None, exchange: Optional[str] = None
    ) -> List[FIOPrice]:
        """Get prices from the FIO API.

        Args:
            material_ticker: Optional material ticker to filter by
            exchange: Optional exchange to filter by (e.g. 'IC1', 'NC1', 'CI1', etc.)

        Returns:
            List of prices
        """
        data = self._get_json("exchange/full")
        prices = [FIOPrice(**price) for price in data]

        # Filter by material ticker if specified
        if material_ticker:
            prices = [p for p in prices if p.material_ticker == material_ticker]

        # Filter by exchange if specified
        if exchange:
            prices = [p for p in prices if p.exchange == exchange]

        return prices

    def get_buildings(self) -> List[FIOBuilding]:
        """Get all buildings from the FIO API.

        Returns:
            List of buildings
        """
        data = self._get_json("building/allbuildings")
        return [FIOBuilding(**building) for building in data]

    def get_planets(self) -> List[FIOPlanet]:
        """Get all planets from the FIO API.

        Returns:
            List of planets
        """
        data = self._get_json("planet/allplanets")
        return [FIOPlanet(**planet) for planet in data]

    def get_systems(self) -> List[FIOSystem]:
        """Get all systems from the FIO API.

        Returns:
            List of systems
        """
        data = self._get_json("systemstars")
        return [FIOSystem(**system) for system in data]

    def get_workforce_needs(self) -> List[FIOWorkforceNeeds]:
        """Get all workforce needs from the FIO API.

        Returns:
            List of workforce needs
        """
        data = self._get_json("global/workforceneeds")
        return [FIOWorkforceNeeds(**need) for need in data]

    def get_comex_exchanges(self) -> List[FIOComexExchange]:
        """Get all COMEX exchanges from the FIO API.

        Returns:
            List of COMEX exchanges
        """
        data = self._get_json("global/comexexchanges")
        return [FIOComexExchange(**exchange) for exchange in data]

    def get_simulation(self) -> FIOSimulation:
        """Get the current simulation state from the FIO API.

        Returns:
            Current simulation state
        """
        data = self._get_json("simulation/current")
        return FIOSimulation(**data)

    def get_sites(self, username: str) -> List[FIOSite]:
        """Get all sites for a user from the FIO API.

        Args:
            username: FIO username

        Returns:
            List of sites
        """
        data = self._get_json(f"sites/{username}", authenticated=True)
        return [FIOSite(**site) for site in data]

    def get_storage(self, username: str) -> List[FIOStorage]:
        """Get all storage for a user from the FIO API.

        Args:
            username: FIO username

        Returns:
            List of storage
        """
        data = self._get_json(f"storage/{username}", authenticated=True)
        return [FIOStorage(**storage) for storage in data]

    def get_warehouses(self, username: str) -> List[FIOWarehouse]:
        """Get all warehouses for a user from the FIO API.

        Args:
            username: FIO username

        Returns:
            List of warehouses
        """
        data = self._get_json(f"sites/warehouses/{username}", authenticated=True)
        return [FIOWarehouse(**warehouse) for warehouse in data]
