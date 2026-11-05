# OWNER: ______
"""
WHAT THIS FILE DOES
-------------------
MealPlanner stores which recipes are planned for which day, plus the number of
servings. The UI keeps ONE MealPlanner object and adds/removes meals on it.

HOW THE DATA LOOKS
------------------
    self.plan = {
        "Monday":  [Recipe(...), Recipe(...)],
        "Tuesday": [Recipe(...)],
    }

SAVING: json can't store Recipe objects, so to_dict() converts everything to plain
dictionaries (using recipe.to_dict()) and from_dict() rebuilds the objects
(using Recipe.from_dict()). storage.py then writes/reads that dictionary as JSON.
"""
    
"""Multi-day meal plan."""
from models.recipe import Recipe  # noqa: F401


class MealPlanner:
    def __init__(self, servings: int = 4):
        self.servings = servings
        self.plan = {}  # {"Monday": [Recipe, ...], ...}

    def add_meal(self, day: str, recipe: Recipe) -> None:
        """Add a recipe to a day (create the day if needed)."""
        raise NotImplementedError("TODO")

    def remove_meal(self, day: str, recipe_id: str) -> None:
        """Remove a recipe from a day. Do nothing if it is not there."""
        raise NotImplementedError("TODO")

    def all_recipes(self) -> list:
        """Flat list of every recipe in the plan (duplicates kept)."""
        raise NotImplementedError("TODO")

    def to_dict(self) -> dict:
        """{"servings": 4, "plan": {"Monday": [recipe.to_dict(), ...]}}"""
        raise NotImplementedError("TODO")

    @classmethod
    def from_dict(cls, data: dict) -> "MealPlanner":
        """Reverse of to_dict()."""
        raise NotImplementedError("TODO")
