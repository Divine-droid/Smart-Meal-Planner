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
import json
import csv
import os

DATA_DIR = "data"


def save_json(filename: str, data) -> str:
    """Write data to data/<filename> as pretty JSON. Create the folder if missing.
    Return the file path. Raise OSError subclasses unchanged."""
    # Create the data directory if it does not already exist.
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)

    # Write UTF-8 JSON with indentation so the file is easy to read and edit.
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")

    # Return the path so callers can refer to the saved file.
    return path


def load_json(filename: str, default=None):
    """Read data/<filename>. If the file is missing or the JSON is broken, return `default`."""
    path = os.path.join(DATA_DIR, filename)

    try:
        # Parse the JSON file and return its value as a Python object.
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        # If the file is missing, unreadable, or invalid JSON, use the caller's fallback.
        return default


def save_shopping_csv(filename: str, items: list[dict[str, object]]) -> str:
    """Write the shopping list (list of dicts from ShoppingListGenerator) to a CSV
    with columns: name, quantity, unit, note. Return the file path."""
    # Make sure the output directory exists before opening the CSV file.
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)

    # Use a fixed set and order of columns for a consistent shopping-list export.
    fieldnames = ["name", "quantity", "unit", "note"]

    # newline="" lets the CSV module handle line endings correctly across platforms.
    # Ignore any extra keys that a shopping-list item may contain.
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()  # Write the column names as the first row.
        writer.writerows(items)  # Write each shopping-list item as a row.

    # Return the path of the exported CSV file.
    return path
