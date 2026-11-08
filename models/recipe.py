# OWNER: Team lead (DONE - do not edit without telling the lead)
"""
WHAT THIS FILE DOES
-------------------
Defines the two data containers the WHOLE app uses:
  * Ingredient - one ingredient line, e.g. name="Rice", measure="2 cups"
  * Recipe     - one meal with its ingredients and instructions

Every other file (client, planner, shopping list, UI) passes Recipe objects around,
so the field names here must not change.

OOP CONCEPTS USED
-----------------
  * @dataclass       - Python writes __init__, __repr__ and __eq__ for us.
  * @classmethod     - a method that builds an object (Recipe.from_api(...)) instead of
                       needing an existing one.
"""
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Ingredient:
    name: str      # e.g. "Chicken Breast"
    measure: str   # RAW text from the API, e.g. "1 1/2 cups" (parsed later in utils/parsing.py)

    # An Ingredient is an OBJECT (use ingredient.name), but some code is written as if it were
    # a dictionary (ingredient["name"] or ingredient.get("name", "")). These two methods make
    # BOTH styles work, so nobody's code breaks.
    def get(self, key, default=None):
        return getattr(self, key, default) if key in ("name", "measure") else default

    def __getitem__(self, key):
        if key in ("name", "measure"):
            return getattr(self, key)
        raise KeyError(key)


@dataclass
class Recipe:
    id: str
    name: str
    category: str = ""      # fields with "= ..." are optional (they have defaults)
    cuisine: str = ""
    instructions: str = ""
    thumbnail: str = ""
    # A list can't be a plain default value in a dataclass, so we use default_factory
    # which creates a NEW empty list for every Recipe.
    ingredients: list[Ingredient] = field(default_factory=list)  # list of Ingredient

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Recipe":
        """Turn one meal dictionary from TheMealDB into a Recipe object."""
        ingredients = []
        # TheMealDB stores ingredients as strIngredient1 ... strIngredient20
        # and measures as strMeasure1 ... strMeasure20. Unused slots are "" or None.
        for i in range(1, 21):
            # `or ""` turns None into "" so .strip() never crashes.
            name = (data.get(f"strIngredient{i}") or "").strip()
            measure = (data.get(f"strMeasure{i}") or "").strip()
            if name:  # skip empty slots
                ingredients.append(Ingredient(name=name, measure=measure))
        return cls(
            id=data.get("idMeal", ""),
            name=data.get("strMeal", ""),
            category=data.get("strCategory") or "",
            cuisine=data.get("strArea") or "",
            instructions=data.get("strInstructions") or "",
            thumbnail=data.get("strMealThumb") or "",
            ingredients=ingredients,
        )

    def to_dict(self) -> dict[str, Any]:
        """Recipe -> plain dictionary. Needed because json.dump can't save custom objects."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Recipe":
        """Plain dictionary (loaded from a JSON file) -> Recipe. Reverse of to_dict()."""
        d = dict(d)  # copy so we don't change the caller's data
        d["ingredients"] = [Ingredient(**i) for i in d.get("ingredients", [])]
        return cls(**d)