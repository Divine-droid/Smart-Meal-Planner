from models.recipe import Recipe
from importlib import import_module
from typing import Any

shopping_list: Any = import_module("shopping")
ShoppingListGenerator: Any = getattr(shopping_list, "ShoppingListGenerator")
scale_quantity: Any = getattr(shopping_list, "scale_quantity")


def make(id_, *pairs):
    d = {"idMeal": id_, "strMeal": id_}
    for i, (n, m) in enumerate(pairs, 1):
        d[f"strIngredient{i}"] = n
        d[f"strMeasure{i}"] = m
    return Recipe.from_api(d)


def test_scale():
    assert scale_quantity(200, 8) == 400
    assert scale_quantity(200, 2) == 100
    assert scale_quantity(None, 8) is None


def test_merge_same_unit():
    a = make("a", ("Onion", "1"), ("Rice", "200g"))
    b = make("b", ("onions", "2"), ("Rice", "100g"))
    items = {i["name"]: i for i in ShoppingListGenerator().generate([a, b], servings=4)}
    assert items["onion"]["quantity"] == 3
    assert items["rice"]["quantity"] == 300


def test_different_units_stay_separate():
    a = make("a", ("Milk", "1 cup"))
    b = make("b", ("Milk", "200ml"))
    items = ShoppingListGenerator().generate([a, b], servings=4)
    assert len([i for i in items if i["name"] == "milk"]) == 2


def test_unknown_quantity_kept():
    a = make("a", ("Salt", "pinch"))
    items = ShoppingListGenerator().generate([a], servings=4)
    assert items[0]["quantity"] is None and items[0]["note"] == "pinch"
