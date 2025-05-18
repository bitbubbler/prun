from typing import Dict, List, Optional
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, RootModel

from fly.models import Experts


class ProductionMaterialPriceIn(BaseModel):
    """Production configuration for material prices."""

    item_symbol: str = Field(..., description="The symbol of the item")
    price: float = Field(..., description="The price of the item")


class EmpireProductionRecipeIn(BaseModel):
    """A single step in a production chain."""

    building_symbol: str = Field(..., description="The symbol of the building to use")
    recipe_symbol: str = Field(..., description="The symbol of the recipe to use")
    item_symbol: Optional[str] = Field(
        default=None,
        description="The symbol of the item to produce. Required for resource extraction recipes. Ignored for all other recipes",
    )


class EmpireExpertsIn(Experts):
    """Experts for an empire."""

    pass


class EmpirePlanetIn(BaseModel):
    """A single planet configuration."""

    natural_id: str = Field(..., description="The natural ID of the planet")
    recipes: List[EmpireProductionRecipeIn] = Field(..., description="List of production recipes in order")
    experts: EmpireExpertsIn


class EmpireIn(BaseModel):
    """A complete empire configuration."""

    name: str = Field(..., description="Name of the empire")
    planets: List[EmpirePlanetIn] = Field(..., description="List of planets in the empire")
    material_buy_prices: Optional[Dict[str, float]] = Field(default=None, description="Optional material buy prices")

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "EmpireIn":
        """Load a empire configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            Empire: The loaded empire configuration

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration is invalid
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


class InternalOfferIn(BaseModel):
    """Configuration for an individual internal offer."""

    item_symbol: str = Field(..., description="The symbol of the item")
    price: float = Field(..., description="The price of the item")


class CompanyIn(BaseModel):
    """Configuration for a company offering items."""

    name: str = Field(..., description="Name of the company")
    user_name: str = Field(..., description="Username of the company representative")
    stock_link: Optional[str] = Field(default=None, description="Optional stock link for the company")
    offers: List[InternalOfferIn] = Field(..., description="List of offers from this company")


class InternalOfferConfig(BaseModel):
    """Configuration for loading internal offers."""

    name: str = Field(..., description="Name of the offer collection")
    description: Optional[str] = Field(default=None, description="Description of the offer collection")
    companies: List[CompanyIn] = Field(..., description="List of companies with internal offers")

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "InternalOfferConfig":
        """Load an internal offer configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            InternalOfferConfig: The loaded offer configuration

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration is invalid
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


class BuyListItemsIn(RootModel[Dict[str, int]]):
    """A dictionary of items and their amounts."""

    root: Dict[str, int]


class BuyListPlanetIn(BaseModel):
    """Configuration for a planet in a buy list."""

    name: str = Field(..., description="The planet name or natural id where the items are needed")
    items: BuyListItemsIn = Field(..., description="The items to buy and their amounts")


class BuyListConfig(BaseModel):
    """Configuration for a buy list."""

    name: str = Field(..., description="Name of the buy list")
    exchange_code: str = Field(..., description="Exchange code for pricing")
    planets: List[BuyListPlanetIn] = Field(..., description="List of planets to buy items from")

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "BuyListConfig":
        """Load a buy list configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            BuyListConfig: The loaded buy list configuration

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration is invalid
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)
