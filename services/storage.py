# OWNER: ______
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


def save_shopping_csv(filename: str, items: list) -> str:
    """Write the shopping list (list of dicts from ShoppingListGenerator) to a CSV
    with columns: name, quantity, unit, note. Return the file path."""
    raise NotImplementedError("TODO")
