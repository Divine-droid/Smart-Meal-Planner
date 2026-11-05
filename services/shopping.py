# OWNER: ______
"""
WHAT THIS FILE DOES
-------------------
Builds ONE combined shopping list from all the recipes in the meal plan, and scales
the amounts for the number of people.

THE ALGORITHM (think of it as a dictionary of totals)
-----------------------------------------------------
  totals = {}      # key: (clean_name, unit)   value: running quantity
  for each recipe:
      for each ingredient:
          qty, unit = parse_measure(ingredient.measure)
          name = clean_ingredient_name(ingredient.name)
          if qty is None:     -> remember it as a note line (e.g. "pinch")
          else:               -> totals[(name, unit)] += qty
  then scale every total, turn the dict into a list of dicts, and sort by name.

WHY THE KEY IS (name, unit): "200g rice" and "1 cup rice" must NOT be added together,
because we don't convert units. Same name + same unit = add; otherwise separate lines.

SCALING: TheMealDB recipes serve about 4 people (BASE_SERVINGS). For 8 people the
factor is 8 / 4 = 2, so 200g becomes 400g.
"""
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
