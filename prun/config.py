from typing import Dict, List, Optional
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


# Liquidity configuration
LIQUIDITY_CONFIG = {
    "safety_buffer_percent": 0.1,  # 10% of balance
    "min_safety_buffer": 1000,  # Minimum 1000 A$
    "variance_tolerance": 0.05,  # 5% variance allowed
    "workforce_rates": {
        "pioneer": 30,  # A$/hour
        "settler": 40,  # A$/hour
        "technician": 50,  # A$/hour
        "engineer": 60,  # A$/hour
        "scientist": 70,  # A$/hour
    },
    "power_rate": 5,  # A$/kWh
    "power_usage": 0.5,  # kW per building
    "wear_rate": 0.1,  # A$/tick
}


class ProductionMaterialPrice(BaseModel):
    """Production configuration for material prices."""

    item_symbol: str = Field(..., description="The symbol of the item")
    price: float = Field(..., description="The price of the item")


class ProductionRecipe(BaseModel):
    """A single step in a production chain."""

    recipe_symbol: str = Field(..., description="The symbol of the recipe to use")
    item_symbol: Optional[str] = Field(
        default=None,
        description="The symbol of the item to produce. Required for resource extraction recipes. Ignored for all other recipes",
    )
    planet_natural_id: Optional[str] = Field(
        default=None, description="The planet where this recipe will be executed"
    )


class ProductionChain(BaseModel):
    """A complete production chain configuration."""

    name: str = Field(..., description="Name of the production chain")
    recipes: List[ProductionRecipe] = Field(
        ..., description="List of production recipes in order"
    )
    material_buy_prices: dict[str, float] = Field(
        default=None, description="Optional material buy prices"
    )

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "ProductionChain":
        """Load a production chain configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file

        Returns:
            ProductionChain: The loaded production chain configuration

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
