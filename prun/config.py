from typing import Dict, List, Optional
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProductionMaterialPrice(BaseModel):
    """Production configuration for material prices."""

    item_symbol: str = Field(..., description="The symbol of the item")
    price: float = Field(..., description="The price of the item")


class ProductionRecipe(BaseModel):
    """A single step in a production chain."""

    building_symbol: str = Field(..., description="The symbol of the building to use")
    recipe_symbol: str = Field(..., description="The symbol of the recipe to use")
    item_symbol: Optional[str] = Field(
        default=None,
        description="The symbol of the item to produce. Required for resource extraction recipes. Ignored for all other recipes",
    )


class Planet(BaseModel):
    """A single planet configuration."""

    natural_id: str = Field(..., description="The natural ID of the planet")
    recipes: List[ProductionRecipe] = Field(
        ..., description="List of production recipes in order"
    )


class Empire(BaseModel):
    """A complete empire configuration."""

    name: str = Field(..., description="Name of the empire")
    planets: List[Planet] = Field(..., description="List of planets in the empire")
    material_buy_prices: Optional[Dict[str, float]] = Field(
        default=None, description="Optional material buy prices"
    )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "Empire":
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
