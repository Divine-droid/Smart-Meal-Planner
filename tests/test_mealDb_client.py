"""Tests for MealDBClient. requests.get is replaced by a fake, so no internet is needed."""
from importlib import import_module

pytest = import_module("pytest")
requests = import_module("requests")

from exceptions import APIRequestError, MealNotFoundError
from models.recipe import Recipe
from services import mealdb_client
from services.mealdb_client import MealDBClient, MAX_RESULTS


class FakeResponse:
    def __init__(self, data=None, status=200, bad_json=False):
        self.data, self.status, self.bad_json = data, status, bad_json

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status} error")

    def json(self):
        if self.bad_json:
            raise ValueError("not json")
        return self.data


def full_meal(meal_id, name="Test Meal"):
    return {"idMeal": meal_id, "strMeal": name, "strCategory": "Seafood",
            "strIngredient1": "Fish", "strMeasure1": "200g"}


def install_fake(monkeypatch, handler):
    """handler(endpoint, params) -> FakeResponse. Returns the list of calls made."""
    calls = []

    def fake_get(url, params=None, timeout=None):
        endpoint = url.rsplit("/", 1)[-1]
        calls.append((endpoint, dict(params or {})))
        return handler(endpoint, params or {})

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def test_search_by_name_returns_recipes(monkeypatch):
    calls = install_fake(monkeypatch, lambda e, p: FakeResponse({"meals": [full_meal("1", "Fish Pie")]}))
    result = MealDBClient().search_by_name("fish")
    assert isinstance(result[0], Recipe) and result[0].name == "Fish Pie"
    assert calls == [("search.php", {"s": "fish"})]


def test_null_meals_raises_not_found(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse({"meals": None}))
    with pytest.raises(MealNotFoundError):
        MealDBClient().search_by_name("zzzz")


def test_ingredient_search_uses_underscores_and_lookups(monkeypatch):
    def handler(endpoint, params):
        if endpoint == "filter.php":
            return FakeResponse({"meals": [{"idMeal": "10"}, {"idMeal": "11"}]})
        return FakeResponse({"meals": [full_meal(params["i"])]})   # lookup.php

    calls = install_fake(monkeypatch, handler)
    result = MealDBClient().search_by_ingredient("Chicken Breast")
    assert [r.id for r in result] == ["10", "11"]
    assert calls[0] == ("filter.php", {"i": "chicken_breast"})


def test_ingredient_search_is_limited(monkeypatch):
    many = [{"idMeal": str(i)} for i in range(50)]

    def handler(endpoint, params):
        if endpoint == "filter.php":
            return FakeResponse({"meals": many})
        return FakeResponse({"meals": [full_meal(params["i"])]})

    install_fake(monkeypatch, handler)
    assert len(MealDBClient().search_by_ingredient("rice")) == MAX_RESULTS


def test_category_search(monkeypatch):
    def handler(endpoint, params):
        if endpoint == "filter.php":
            return FakeResponse({"meals": [{"idMeal": "7"}]})
        return FakeResponse({"meals": [full_meal("7")]})

    calls = install_fake(monkeypatch, handler)
    assert MealDBClient().search_by_category("seafood")[0].id == "7"
    assert calls[0] == ("filter.php", {"c": "Seafood"})


def test_filter_with_no_results_raises_not_found(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse({"meals": None}))
    with pytest.raises(MealNotFoundError):
        MealDBClient().search_by_ingredient("unobtainium")


def test_lookup_not_found(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse({"meals": None}))
    with pytest.raises(MealNotFoundError):
        MealDBClient().lookup("999")


def test_network_failure_becomes_api_request_error(monkeypatch):
    def boom(endpoint, params):
        raise requests.ConnectionError("no internet")
    install_fake(monkeypatch, boom)
    with pytest.raises(APIRequestError):
        MealDBClient().search_by_name("fish")


def test_http_error_becomes_api_request_error(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse(status=500))
    with pytest.raises(APIRequestError):
        MealDBClient().search_by_name("fish")


def test_unreadable_json_becomes_api_request_error(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse(bad_json=True))
    with pytest.raises(APIRequestError):
        MealDBClient().search_by_name("fish")


def test_search_dispatches_by_mode(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse({"meals": [full_meal("1")]}))
    assert MealDBClient().search("fish", "name")[0].id == "1"


@pytest.mark.parametrize("query,mode", [("", "name"), ("   ", "name"), ("fish", "colour")])
def test_search_rejects_bad_input(query, mode):
    with pytest.raises(ValueError):
        MealDBClient().search(query, mode)


def test_list_categories(monkeypatch):
    install_fake(monkeypatch, lambda e, p: FakeResponse({"meals": [{"strCategory": "Beef"}, {"strCategory": "Dessert"}]}))
    assert MealDBClient().list_categories() == ["Beef", "Dessert"]