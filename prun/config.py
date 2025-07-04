from typing import Dict, List, Optional
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, RootModel, ValidationError
from pydantic.config import ConfigDict

from prun.models import Experts


class YAMLConfigBase(BaseModel):
    """Base class for YAML configurations with strict validation."""

    model_config = ConfigDict(extra="forbid")  # Forbid extra attributes

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "YAMLConfigBase":
        """Load configuration from a YAML file with strict validation.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            The loaded configuration

        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration is invalid, with details about the error
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        try:
            with open(yaml_path, "r") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML syntax in {yaml_path}: {str(e)}")

        try:
            return cls(**config_data)
        except ValidationError as e:
            # Convert Pydantic validation error to more readable format
            error_messages = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_messages.append(f"- {location}: {message}")

            raise ValueError(
                f"Invalid configuration in {yaml_path}:\n" + "\n".join(error_messages)
            )


class ProductionMaterialPriceIn(YAMLConfigBase):
    """Production configuration for material prices."""

    item_symbol: str = Field(..., description="The symbol of the item")
    price: float = Field(..., description="The price of the item")


class EmpireProductionRecipeIn(YAMLConfigBase):
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


class EmpirePlanetIn(YAMLConfigBase):
    """A single planet configuration."""

    name: str = Field(
        ...,
        description="The name of the planet (can be a natural ID, passed to find_planet)",
    )
    recipes: List[EmpireProductionRecipeIn] = Field(
        ..., description="List of production recipes in order"
    )
    experts: EmpireExpertsIn


class EmpireIn(YAMLConfigBase):
    """A complete empire configuration."""

    name: str = Field(..., description="Name of the empire")
    planets: List[EmpirePlanetIn] = Field(
        ..., description="List of planets in the empire"
    )
    material_buy_prices: Optional[Dict[str, float]] = Field(
        default=None, description="Optional material buy prices"
    )


class InternalOfferIn(YAMLConfigBase):
    """Configuration for an individual internal offer."""

    item_symbol: str = Field(..., description="The symbol of the item")
    price: float = Field(..., description="The price of the item")


class CompanyIn(YAMLConfigBase):
    """Configuration for a company offering items."""

    name: str = Field(..., description="Name of the company")
    user_name: str = Field(..., description="Username of the company representative")
    stock_link: Optional[str] = Field(
        default=None, description="Optional stock link for the company"
    )
    offers: List[InternalOfferIn] = Field(
        ..., description="List of offers from this company"
    )


class InternalOfferConfig(YAMLConfigBase):
    """Configuration for loading internal offers."""

    name: str = Field(..., description="Name of the offer collection")
    description: Optional[str] = Field(
        default=None, description="Description of the offer collection"
    )
    companies: List[CompanyIn] = Field(
        ..., description="List of companies with internal offers"
    )


class BuyListItemsIn(RootModel[Dict[str, int]]):
    """A dictionary of items and their amounts."""

    root: Dict[str, int]


class BuyListPlanetIn(YAMLConfigBase):
    """Configuration for a planet in a buy list."""

    name: str = Field(
        ..., description="The planet name or natural id where the items are needed"
    )
    items: BuyListItemsIn = Field(..., description="The items to buy and their amounts")


class BuyListConfig(YAMLConfigBase):
    """Configuration for a buy list."""

    name: str = Field(..., description="Name of the buy list")
    exchange_code: str = Field(..., description="Exchange code for pricing")
    planets: List[BuyListPlanetIn] = Field(
        ..., description="List of planets to buy items from"
    )
