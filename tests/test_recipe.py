from models.recipe import Recipe


def test_from_api_drops_blank_ingredients():
    data = {"idMeal": "1", "strMeal": "Test", "strIngredient1": "Rice", "strMeasure1": "2 cups",
            "strIngredient2": "", "strMeasure2": " "}
    r = Recipe.from_api(data)
    assert len(r.ingredients) == 1
    assert r.ingredients[0].name == "Rice"


def test_roundtrip():
    r = Recipe.from_api({"idMeal": "1", "strMeal": "T", "strIngredient1": "Salt", "strMeasure1": "1 tsp"})
    assert Recipe.from_dict(r.to_dict()) == r
