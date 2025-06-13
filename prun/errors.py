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

    def __init__(self, item_symbol: str, recipe_symbol: Optional[str] = None) -> None:
        message = f"Item {item_symbol} recipe {recipe_symbol} not found"
        super().__init__(message)


class RecipeNotFoundError(ValueError):
    """Raised when a recipe is not found."""

    def __init__(self, recipe_symbol: str) -> None:
        super().__init__(f"Recipe {recipe_symbol} not found")


class PlanetResourceNotFoundError(ValueError):
    """Raised when a planet resource is not found."""

    def __init__(self, item_symbol: str, planet_natural_id: str) -> None:
        super().__init__(
            f"Planet resource {item_symbol} not found on planet {planet_natural_id}"
        )


class BuildingNotFoundError(ValueError):
    """Raised when a building is not found."""

    def __init__(self, building_symbol: str) -> None:
        super().__init__(f"Building {building_symbol} not found")


class PlanetNotFoundError(ValueError):
    """Raised when a planet is not found."""

    def __init__(self, name_or_natural_id: str) -> None:
        super().__init__(f"Planet {name_or_natural_id} not found")


class PlanetResourceRequiredError(ValueError):
    """Raised when a planet resource is required."""

    def __init__(self) -> None:
        super().__init__("A planet resource is required to calculate the COGM")


class PlanetRequiredError(ValueError):
    """Raised when a planet is required."""

    def __init__(self) -> None:
        super().__init__("A planet is required to calculate the COGM")


class RecipeSymbolRequiredError(ValueError):
    """Raised when a recipe symbol is required."""

    def __init__(self) -> None:
        super().__init__("A recipe symbol is required to find an extraction recipe")
