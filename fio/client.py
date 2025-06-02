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
    FIOPlanetFull,
    FIOSystem,
    FIOWorkforceNeeds,
    FIOComexExchange,
    FIOSimulation,
    FIOAuthLoginRequest,
    FIOAuthLoginResponse,
    FIOSite,
    FIOStorage,
    FIOWarehouse,
    FIOLocalMarketAds,
    FIOAd,
    FIOShippingAd,
)
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
        self._useapitoken = False

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._auth_token is not None

    def authenticate(
        self,
        username: str | None = None,
        password: str | None = None,
        apikey: str | None = None,
    ) -> str:
        """Authenticate with the FIO API.

        Args:
            username: FIO username
            password: FIO password

        Returns:
            Authentication token

        Raises:
            requests.RequestException: If the login request fails
        """
        if apikey:
            self._auth_token = apikey
            self.headers["Authorization"] = self._auth_token
            self._useapitoken = True
        elif password:
            if not username:
                raise ValueError("Username is required to authenticate with password")
            self._auth_token = self._get_auth_token(username, password)
            self.headers["Authorization"] = f"Bearer {self._auth_token}"
        elif not self._auth_token:
            raise ValueError("No authentication token provided")
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

    def _map_csv_to_model(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map CSV column names to model field names.

        Args:
            data: CSV data as dict
            mapping: Mapping from CSV column names to model field names

        Returns:
            Dict with model field names as keys
        """
        result = {model_field: data[csv_field] for csv_field, model_field in mapping.items()}
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

        headers: Dict[str, str] = self.headers.copy()
        if authenticated and self._useapitoken and self._auth_token:
            headers["Authorization"] = self._auth_token
        elif authenticated and self._auth_token:
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
        if authenticated and self._useapitoken and self._auth_token:
            headers["Authorization"] = self._auth_token
        elif authenticated and self._auth_token:
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

    def get_prices(self, material_ticker: Optional[str] = None, exchange: Optional[str] = None) -> List[FIOPrice]:
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

    def get_planets_full(self) -> List[FIOPlanetFull]:
        """Get full information for all planets from the FIO API.

        Returns:
            List of planets with full information
        """
        data = self._get_json("planet/allplanets/full")
        return [FIOPlanetFull(**planet) for planet in data]

    def get_planet_by_id(self, planet_id: str) -> Optional[FIOPlanetFull]:
        """Get a single planet by its natural ID.

        Args:
            planet_id: Planet natural ID (e.g., 'PG-241h')

        Returns:
            Planet details or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        try:
            # First get all planets to find the one we want
            planets = self.get_planets_full()
            for planet in planets:
                if planet.planet_natural_id == planet_id:
                    return planet
            logger.warning(f"Planet with ID {planet_id} not found")
            return None
        except requests.RequestException as e:
            logger.error(f"Error fetching planet {planet_id}: {str(e)}")
            raise

    def get_exchange_by_ticker(self, exchange_ticker: str) -> Optional[Dict[str, Any]]:
        """Get data for a single exchange by its ticker.

        Args:
            exchange_ticker: Exchange ticker (e.g., 'IC1', 'NC1')

        Returns:
            Exchange data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/exchange/{exchange_ticker}"
        logger.debug(f"Fetching exchange data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching exchange {exchange_ticker}: {str(e)}")
            raise

    def get_company_by_code(self, company_code: str) -> Optional[Dict[str, Any]]:
        """Get data for a single company by its code.

        Args:
            company_code: Company code (e.g., 'AI', 'ACC')

        Returns:
            Company data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/company/code/{company_code}"
        logger.debug(f"Fetching company data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching company {company_code}: {str(e)}")
            raise

    def get_company_by_name(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a single company by its name.

        Args:
            company_name: Company name (e.g., 'Antares Initiative')

        Returns:
            Company data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/company/name/{company_name}"
        logger.debug(f"Fetching company data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching company {company_name}: {str(e)}")
            raise

    def get_localmarket_by_planet(self, planet: str, market_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get local market data for a specific planet.

        Args:
            planet: Planet natural ID (e.g., 'PG-241h')
            market_type: Optional market type filter

        Returns:
            Local market data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/localmarket/planet/{planet}"
        if market_type:
            url = f"{url}/{market_type}"

        logger.debug(f"Fetching local market data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching local market for planet {planet}: {str(e)}")
            raise

    def get_infrastructure_by_planet(self, planet_id: str) -> Optional[Dict[str, Any]]:
        """Get infrastructure data for a specific planet.

        Args:
            planet_id: Planet natural ID or infrastructure ID

        Returns:
            Infrastructure data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/infrastructure/{planet_id}"
        logger.debug(f"Fetching infrastructure data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching infrastructure for planet {planet_id}: {str(e)}")
            raise

    def get_material_by_ticker(self, ticker: str) -> Optional[FIOMaterial]:
        """Get a single material by its ticker.

        Args:
            ticker: Material ticker (e.g., 'H2O', 'RAT')

        Returns:
            Material details or None if not found
        """
        try:
            materials = self.get_all_materials()
            for material in materials:
                if material.ticker.lower() == ticker.lower():
                    return material
            logger.warning(f"Material with ticker {ticker} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching material {ticker}: {str(e)}")
            raise

    def get_building_by_ticker(self, ticker: str) -> Optional[FIOBuilding]:
        """Get a single building by its ticker.

        Args:
            ticker: Building ticker (e.g., 'SMP', 'TNP')

        Returns:
            Building details or None if not found
        """
        try:
            buildings = self.get_buildings()
            for building in buildings:
                if building.ticker.lower() == ticker.lower():
                    return building
            logger.warning(f"Building with ticker {ticker} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching building {ticker}: {str(e)}")
            raise

    def get_workforce_by_planet(self, username: str, planet: str) -> Optional[Dict[str, Any]]:
        """Get workforce data for a specific user on a specific planet.

        Args:
            username: FIO username
            planet: Planet natural ID

        Returns:
            Workforce data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/workforce/{username}/{planet}"
        logger.debug(f"Fetching workforce data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        if self._auth_token:
            if self._useapitoken:
                headers["Authorization"] = self._auth_token
            else:
                headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching workforce for user {username} on planet {planet}: {str(e)}")
            raise

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information.

        Args:
            username: FIO username

        Returns:
            User data or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.base_url}/user/{username}"
        logger.debug(f"Fetching user data from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        if self._auth_token:
            if self._useapitoken:
                headers["Authorization"] = self._auth_token
            else:
                headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching user info for {username}: {str(e)}")
            raise

    def get_contracts(self, username: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get contracts for a user.

        Args:
            username: Optional username, defaults to authenticated user if None

        Returns:
            List of contracts or None if not found

        Raises:
            requests.RequestException: If the request fails
        """
        if not username and not self._auth_token:
            raise ValueError("Either username or authentication is required for get_contracts")

        url = f"{self.base_url}/contract/allcontracts"
        if username:
            url = f"{url}/{username}"

        logger.debug(f"Fetching contracts from {url}")

        headers = self.headers.copy()
        headers["Accept"] = "application/json"

        if self._auth_token:
            if self._useapitoken:
                headers["Authorization"] = self._auth_token
            else:
                headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching contracts: {str(e)}")
            raise

    def get_system_by_id(self, system_id: str) -> Optional[FIOSystem]:
        """Get a single system by its natural ID.

        Args:
            system_id: System natural ID

        Returns:
            System details or None if not found
        """
        try:
            systems = self.get_systems()
            for system in systems:
                if system.natural_id == system_id:
                    return system
            logger.warning(f"System with ID {system_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching system {system_id}: {str(e)}")
            raise

    def get_localmarket_ads(self, planet: str) -> FIOLocalMarketAds:
        """Get local market ads for a specific planet from the FIO API."""
        data = self.get_localmarket_by_planet(planet)
        return FIOLocalMarketAds(
            BuyingAds=[FIOAd(**ad) for ad in data.get("BuyingAds", [])],
            SellingAds=[FIOAd(**ad) for ad in data.get("SellingAds", [])],
            ShippingAds=[FIOShippingAd(**ad) for ad in data.get("ShippingAds", [])],
        )
