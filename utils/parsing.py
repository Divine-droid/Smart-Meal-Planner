# OWNER: ______
"""Regex helpers. Use the `re` module."""
import re  # noqa: F401  (you will need it)

from exceptions import InvalidServingsError  # noqa: F401


def parse_measure(text: str):
    """Extract (quantity, unit) from a measure string.

    Examples:
        "2 tbsp"    -> (2.0, "tbsp")
        "500g"      -> (500.0, "g")
        "1 1/2 cups"-> (1.5, "cups")
        "1/4 tsp"   -> (0.25, "tsp")
        "pinch"     -> (None, "pinch")   # no number found
        ""          -> (None, "")
    Hint: use re.match with groups, and fractions.Fraction for "1/2".
    """
    raise NotImplementedError("TODO")


def parse_servings(raw: str) -> int:
    """Validate serving-size input and return it as an int.

    Examples:
        "4"   -> 4
        " 2 " -> 2
        "0", "-3", "abc", "2.5", "" -> raise InvalidServingsError
    Rule: whole number from 1 to 99.
    """
    raise NotImplementedError("TODO")


def clean_ingredient_name(name: str) -> str:
    """Normalise an ingredient name so duplicates can be merged.

    Examples:
        "  Chicken Breasts "  -> "chicken breast"
        "Tomato (chopped)"    -> "tomato"
        "Olive  Oil"          -> "olive oil"
    Steps: lowercase, strip, remove text in brackets, collapse spaces,
    remove a trailing plural 's' (simple version is fine).
    """
    raise NotImplementedError("TODO")
