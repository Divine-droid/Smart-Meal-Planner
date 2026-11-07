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

from typing import Any

from utils.parsing import parse_measure, clean_ingredient_name

BASE_SERVINGS = 4


def scale_quantity(qty, target_servings: int,
                   base_servings: int = BASE_SERVINGS):
    """Scale a quantity for a different number of people."""

    if qty is None:
        return None
      
    return qty * (target_servings / base_servings)


class ShoppingListGenerator:

    def generate(self, recipes: list[Any], servings: int) -> list[dict[str, Any]]:
        """Combine ingredients from multiple recipes."""

        if servings <= 0:
            raise ValueError("Servings must be greater than zero.")

        shopping_list = {}

        for recipe in recipes:

            # Get ingredients from each recipe
            ingredients = recipe.ingredients

            for ingredient in ingredients:

                # Get ingredient name and measurement
                raw_name = ingredient.get("name", "")
                raw_measure = ingredient.get("measure", "")

                if not raw_name.strip():
                    continue

                # Clean ingredient name
                name = clean_ingredient_name(raw_name)

                # Ignore empty names
                if not name:
                    continue

                # Parse the measurement
                parsed = parse_measure(raw_measure)

                # Expected parser result:
                # quantity, unit, note
                if isinstance(parsed, dict):
                    quantity = parsed.get("quantity")
                    unit = parsed.get("unit", "")
                    note = parsed.get("note", "")
                else:
                    quantity, unit, note = (
                        list(parsed) + ["", ""]
                    )[:3]

                unit = unit or ""
                note = note or ""

                # Scale known quantities
                if quantity is not None:
                    quantity = scale_quantity(quantity, servings)

                # Create a unique key for each ingredient and unit
                key = (name, unit)

                if key not in shopping_list:
                    shopping_list[key] = {
                        "name": name,
                        "quantity": 0,
                        "unit": unit,
                        "note": ""
                    }

                item = shopping_list[key]

                # Add quantities when units are the same
                if quantity is not None:
                    item["quantity"] += quantity

                else:
                    # Keep original measurement as a note
                    original_note = str(raw_measure).strip()

                    if original_note:
                        existing_notes = item["note"].split("; ")

                        if original_note not in existing_notes:
                            if item["note"]:
                                item["note"] += "; " + original_note
                            else:
                                item["note"] = original_note

        # Convert dictionary into a list
        result = list(shopping_list.values())

        # Remove zero quantities for unknown measurements
        for item in result:
            if item["quantity"] == 0:
                item["quantity"] = None

        # Sort alphabetically by ingredient name
        result.sort(key=lambda item: item["name"])

        return result
