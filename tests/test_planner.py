from models.recipe import Recipe
from services.planner import MealPlanner


def test_add_remove_and_roundtrip():
    p = MealPlanner(servings=3)
    r = Recipe(id="1", name="Soup")
    p.add_meal("Monday", r)
    p.add_meal("Tuesday", r)
    assert len(p.all_recipes()) == 2
    p.remove_meal("Monday", "1")
    assert len(p.all_recipes()) == 1
    p2 = MealPlanner.from_dict(p.to_dict())
    assert p2.servings == 3 and len(p2.all_recipes()) == 1
