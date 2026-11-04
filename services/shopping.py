# OWNER: ______
"""Combine ingredients from many recipes into one scaled shopping list."""
from utils.parsing import parse_measure, clean_ingredient_name  # noqa: F401

BASE_SERVINGS = 4  # assume each TheMealDB recipe serves about 4 people


def scale_quantity(qty, target_servings: int, base_servings: int = BASE_SERVINGS):
    """Scale a quantity for a different number of people.

    scale_quantity(200, 8)    -> 400.0
    scale_quantity(200, 2)    -> 100.0
    scale_quantity(None, 8)   -> None   # unknown quantities are not scaled
    """
    raise NotImplementedError("TODO")


class ShoppingListGenerator:
    def generate(self, recipes: list, servings: int) -> list:
        """Merge ingredients of all recipes into one list of dicts:
        [{"name": "onion", "quantity": 3.0, "unit": "", "note": ""}, ...]

        Rules:
        - Clean names with clean_ingredient_name so "Onion" and "onions" merge.
        - Add quantities only when the unit is the same; different units = separate lines.
        - If quantity is None (e.g. "pinch", "to taste"), keep one line with the original text in "note".
        - Scale every quantity for `servings`.
        - Return sorted by name.
        """
        raise NotImplementedError("TODO")
