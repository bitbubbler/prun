from typing import List

from prun.models import Recipe


class MultipleRecipesError(ValueError):
    """Raised when multiple recipes are found for an item and no specific recipe was chosen."""

    def __init__(self, item_symbol: str, available_recipes: List[Recipe]):
        super().__init__(
            f"Multiple recipes found for item {item_symbol}. Please specify a recipe."
        )
        self.available_recipes = available_recipes
