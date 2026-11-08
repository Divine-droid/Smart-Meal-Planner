# OWNER: Team lead (written as a fallback so the project could be finished on time)
r"""
WHAT THIS FILE DOES
-------------------
Small helper functions that read and clean TEXT using regular expressions (regex).
  * parse_measure          - "1 1/2 cups"       -> (1.5, "cup")
  * parse_servings         - "4"                -> 4   (or an error for bad input)
  * clean_ingredient_name  - "  Onions (diced)" -> "onion"

WHERE THEY ARE USED
-------------------
  * shopping.py calls parse_measure and clean_ingredient_name to merge ingredients.
  * app.py calls parse_servings to check the "Number of people" box.

WHY UNITS ARE NORMALISED
------------------------
Recipes write the same unit many ways ("cup", "cups", "tbs", "tablespoon"). If we kept
them as written, the shopping list would show "1 cup oil" and "2 cups oil" on separate
lines. parse_measure therefore returns ONE standard form of each unit ("cup", "tbsp"...).

REGEX CHEAT SHEET (the `re` module)
-----------------------------------
  \d  a digit    \s  a space    [a-zA-Z]  a letter    +  one or more    *  zero or more
  ?   optional   (...)  a group    (?P<name>...)  a NAMED group -> m.group("name")
Test patterns at https://regex101.com (choose Python).
"""
import re
from fractions import Fraction

from exceptions import InvalidServingsError

# Unicode fraction characters that sometimes appear in recipe data.
_UNICODE_FRACTIONS = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3", "⅛": "1/8"}

# Unit spellings -> one standard form.
_UNIT_ALIASES = {
    "tbs": "tbsp", "tbsp": "tbsp", "tbl": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp",
    "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "cup": "cup", "cups": "cup",
    "g": "g", "gr": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
    "ml": "ml", "millilitre": "ml", "milliliter": "ml", "millilitres": "ml", "milliliters": "ml",
    "l": "l", "litre": "l", "liter": "l", "litres": "l", "liters": "l",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
    "leaves": "leaf", "dashes": "dash", "pinches": "pinch", "bunches": "bunch", "slices": "slice",
}

# A measure starts with an optional number ("1 1/2", "1/4", "2.5", "500") followed by an
# optional unit word ("cups", "g"). Anything after that is ignored.
_MEASURE_RE = re.compile(
    r"^\s*(?P<qty>\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)?\s*(?P<unit>[a-zA-Z]+)?"
)


def _normalise_unit(unit: str) -> str:
    """'Cups' -> 'cup',  'tablespoons' -> 'tbsp'.  Unknown words just lose a plural 's'."""
    unit = unit.lower()
    if unit in _UNIT_ALIASES:
        return _UNIT_ALIASES[unit]
    if len(unit) > 3 and unit.endswith("s") and not unit.endswith("ss"):
        return unit[:-1]   # cloves -> clove, tins -> tin
    return unit


def parse_measure(text: str):
    """Extract (quantity, unit) from a measure string.

    Examples:
        "2 tbsp"     -> (2.0, "tbsp")
        "500g"       -> (500.0, "g")
        "1 1/2 cups" -> (1.5, "cup")
        "1/4 tsp"    -> (0.25, "tsp")
        "3"          -> (3.0, "")
        "pinch"      -> (None, "pinch")   # no number found: quantity is None
        ""           -> (None, "")
    """
    text = (text or "").strip()
    for char, replacement in _UNICODE_FRACTIONS.items():   # "1½" -> "1 1/2"
        text = text.replace(char, f" {replacement}")
    text = text.strip()

    match = _MEASURE_RE.match(text)
    if not match or not match.group("qty"):
        return None, text                                  # nothing to scale ("pinch", "to taste")

    # "1 1/2" -> parts ["1", "1/2"] -> 1 + 1/2 = 1.5.  Fraction("1/2") parses safely.
    quantity = float(sum(Fraction(part) for part in match.group("qty").split()))
    return quantity, _normalise_unit(match.group("unit") or "")


def parse_servings(raw: str) -> int:
    """Validate serving-size input and return it as an int.

    Examples:
        "4"   -> 4
        " 2 " -> 2
        "0", "-3", "abc", "2.5", "" -> raise InvalidServingsError
    Rule: a whole number from 1 to 99.
    """
    cleaned = (raw or "").strip()
    if not re.fullmatch(r"\d{1,2}", cleaned):     # 1-2 digits only: rejects "-3", "abc", "2.5", ""
        raise InvalidServingsError("Number of people must be a whole number from 1 to 99.")
    servings = int(cleaned)
    if servings < 1:                               # rejects "0" and "00"
        raise InvalidServingsError("Number of people must be at least 1.")
    return servings


def clean_ingredient_name(name: str) -> str:
    """Normalise an ingredient name so duplicates can be merged.

    Examples:
        "  Chicken Breasts "  -> "chicken breast"
        "Tomato (chopped)"    -> "tomato"
        "Tomatoes"            -> "tomato"
        "Olive  Oil"          -> "olive oil"
    """
    text = (name or "").lower().strip()
    text = re.sub(r"\(.*?\)", "", text)    # remove anything in brackets
    text = re.sub(r"\s+", " ", text).strip()  # collapse repeated spaces
    if not text:
        return ""

    # Make the LAST word singular ("chicken breasts" -> "chicken breast").
    *front, last = text.split(" ")
    if len(last) > 3 and not last.endswith(("ss", "us", "is")):   # keep "hummus", "couscous", "watercress"
        if last.endswith("ies"):
            last = last[:-3] + "y"        # berries -> berry
        elif last.endswith("oes"):
            last = last[:-2]              # tomatoes -> tomato
        elif last.endswith("s"):
            last = last[:-1]              # onions -> onion
    return " ".join(front + [last])