# OWNER: Team lead (written as a fallback so the project could be finished on time)
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
from models.recipe import Recipe


class MealPlanner:
    def __init__(self, servings: int = 4):
        self.servings = servings  # how many people we are cooking for
        self.plan = {}            # {"Monday": [Recipe, ...], ...}

    def add_meal(self, day: str, recipe: Recipe) -> None:
        """Add a recipe to a day (the day is created the first time it is used)."""
        self.plan.setdefault(day, []).append(recipe)

    def remove_meal(self, day: str, recipe_id: str) -> None:
        """Remove a recipe from a day. Does nothing if it is not there."""
        remaining = [r for r in self.plan.get(day, []) if r.id != recipe_id]
        if remaining:
            self.plan[day] = remaining
        else:
            self.plan.pop(day, None)   # don't keep an empty day around

    def all_recipes(self) -> list[Recipe]:
        """Flat list of every recipe in the plan (duplicates are kept on purpose:
        cooking the same dish twice means buying its ingredients twice)."""
        return [recipe for recipes in self.plan.values() for recipe in recipes]

    def to_dict(self) -> dict[str, object]:
        """{"servings": 4, "plan": {"Monday": [recipe.to_dict(), ...]}}"""
        return {
            "servings": self.servings,
            "plan": {day: [r.to_dict() for r in recipes] for day, recipes in self.plan.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "MealPlanner":
        """Reverse of to_dict(): rebuild a MealPlanner (and its Recipe objects)."""
        raw_servings = data.get("servings", 4)
        servings = int(raw_servings) if isinstance(raw_servings, (int, str)) else 4
        planner = cls(servings=servings)
        plan_data = data.get("plan", {})

        if not isinstance(plan_data, dict):
            return planner

        for day, recipes in plan_data.items():
            if not isinstance(day, str) or not isinstance(recipes, list):
                continue
            planner.plan[day] = [
                Recipe.from_dict(recipe)
                for recipe in recipes
                if isinstance(recipe, dict)
            ]
        return planner