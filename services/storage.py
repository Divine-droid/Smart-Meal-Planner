# OWNER: ______
"""
WHAT THIS FILE DOES
-------------------
All FILE HANDLING lives here: saving and loading the meal plan, favourite recipes and
shopping lists in the data/ folder.
  * JSON  - for the meal plan and favourites (keeps nested data)
  * CSV   - for the shopping list (opens in Excel)

ERROR HANDLING RULE: reading a file that does not exist (or is damaged) must NOT crash
the app. It should return a default value instead.
"""

"""Save and load files in the data/ folder."""
import json  # noqa: F401
import csv   # noqa: F401
import os    # noqa: F401

DATA_DIR = "data"


def save_json(filename: str, data) -> str:
    """Write data to data/<filename> as pretty JSON. Create the folder if missing.
    Return the file path. Raise OSError subclasses unchanged."""
    raise NotImplementedError("TODO")


def load_json(filename: str, default=None):
    """Read data/<filename>. If the file is missing or the JSON is broken, return `default`."""
    raise NotImplementedError("TODO")


def save_shopping_csv(filename: str, items: list[dict[str, object]]) -> str:
    """Write the shopping list (list of dicts from ShoppingListGenerator) to a CSV
    with columns: name, quantity, unit, note. Return the file path."""
    raise NotImplementedError("TODO")
