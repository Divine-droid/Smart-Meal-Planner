# OWNER: ______
"""
WHAT THIS FILE DOES

Talks to the internet. MealDBClient sends HTTP requests to TheMealDB and turns the
answers into Recipe objects. Nothing else in the app calls the API directly.

THE API (free test key is "1", already in BASE)

  search by name        BASE/search.php?s=Arrabiata        -> FULL meals
  filter by ingredient  BASE/filter.php?i=chicken_breast   -> only id, name, thumbnail
  filter by category    BASE/filter.php?c=Seafood          -> only id, name, thumbnail
  lookup by id          BASE/lookup.php?i=52772            -> ONE full meal
Every answer looks like {"meals": [ {...}, {...} ]}, and {"meals": null} means no results.

KEY IDEA
filter.php gives a SHORT list, so for each result we call lookup() to get the full
recipe (ingredients + instructions). Limit this to ~6 meals so the app stays fast.

TRY IT QUICKLY in a Python shell:
    from services.mealdb_client import MealDBClient
    print(MealDBClient().search_by_name("Arrabiata"))
"""
"""Client for TheMealDB (free test key = 1)."""
import requests  # noqa: F401

from exceptions import APIRequestError, MealNotFoundError 
from models.recipe import Recipe


class MealDBClient:
    BASE = "https://www.themealdb.com/api/json/v1/1"

    def _get(self, endpoint: str, **params) -> list:
        """GET BASE/endpoint and return the list under the "meals" key.

        - Use a timeout (e.g. 10 seconds).
        - If the API returns {"meals": null}, return [].
        - On any requests exception, raise APIRequestError.
        """
        raise NotImplementedError("TODO")

    def search_by_name(self, name: str) -> list:
        """search.php?s=<name> -> list of full Recipe objects. Raise MealNotFoundError if empty."""
        raise NotImplementedError("TODO")

    def search_by_ingredient(self, ingredient: str) -> list:
        """filter.php?i=<ingredient> -> list of short dicts (id, name, thumb).
        Then call lookup() for each to get full Recipes (limit to first 5-10).
        Raise MealNotFoundError if empty."""
        raise NotImplementedError("TODO")

    def search_by_category(self, category: str) -> list:
        """filter.php?c=<category> -> same idea as search_by_ingredient."""
        raise NotImplementedError("TODO")

    def lookup(self, meal_id: str) -> Recipe:
        """lookup.php?i=<id> -> one full Recipe. Raise MealNotFoundError if not found."""
        raise NotImplementedError("TODO")

    def search(self, query: str, mode: str) -> list:
        """mode is one of "name", "ingredient", "category". Dispatch to the methods above.
        Raise ValueError for an unknown mode or empty query."""
        raise NotImplementedError("TODO")
