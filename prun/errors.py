from typing import List, Optional

from prun.models import Recipe, PlanetResource


class MultipleRecipesError(ValueError):
    """Raised when multiple recipes are found for an item and no specific recipe was chosen."""

    def __init__(self, item_symbol: str, available_recipes: List[Recipe]):
        super().__init__(
            f"Multiple recipes found for item {item_symbol}. Please specify a recipe."
        )
        self.available_recipes = available_recipes


class ItemRecipeNotFoundError(ValueError):
    """Raised when an item recipe is not found."""

    def __init__(self, item_symbol: str, recipe_symbol: Optional[str] = None):
        message = f"Item {item_symbol} recipe {recipe_symbol} not found"
        super().__init__(message)


class RecipeNotFoundError(ValueError):
    """Raised when a recipe is not found."""

    def __init__(self, recipe_symbol: str):
        super().__init__(f"Recipe {recipe_symbol} not found")


class PlanetResourceNotFoundError(ValueError):
    """Raised when a planet resource is not found."""

    def __init__(self, item_symbol: str, planet_natural_id: str):
        super().__init__(
            f"Planet resource {item_symbol} not found on planet {planet_natural_id}"
        )


class PlanetResourceRequiredError(ValueError):
    """Raised when a planet resource is required for an extraction recipe."""

    def __init__(self, recipe_symbol: str, planet_resource: Optional[PlanetResource]):
        super().__init__(
            f"Planet resource required for recipe {recipe_symbol}. Planet resource: {planet_resource}"
        )


class BuildingNotFoundError(ValueError):
    """Raised when a building is not found."""

    def __init__(self, building_symbol: str):
        super().__init__(f"Building {building_symbol} not found")


class PlanetNotFoundError(ValueError):
    """Raised when a planet is not found."""

    def __init__(self, natural_id: str):
        super().__init__(f"Planet {natural_id} not found")


class PlanetResourceRequiredError(ValueError):
    """Raised when a planet resource is required."""

    def __init__(self):
        super().__init__("A planet resource is required to calculate the COGM")
