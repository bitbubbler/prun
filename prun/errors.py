from typing import List, Optional

from prun.models import Recipe, PlanetResource


class MultipleRecipesError(ValueError):
    """Raised when multiple recipes are found for an item and no specific recipe was chosen."""

    def __init__(self, item_symbol: str, available_recipes: List[Recipe]):
        super().__init__(
            f"Multiple recipes found for item {item_symbol}. Please specify a recipe."
        )
        self.available_recipes = available_recipes


class RecipeNotFoundError(ValueError):
    """Raised when a recipe is not found."""

    def __init__(self, recipe_symbol: str, item_symbol: Optional[str] = None):
        message = f"Recipe {recipe_symbol} not found"
        if item_symbol:
            message += f" for item {item_symbol}"
        super().__init__(message)


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
