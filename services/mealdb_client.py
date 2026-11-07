# OWNER: Team lead
"""
WHAT THIS FILE DOES
-------------------
Finds recipes. MealDBClient searches TWO places and combines the results:
  1. LOCAL dishes  - Nigerian meals we wrote ourselves in local_data/local_meals.json
  2. TheMealDB     - a free online recipe database (over the internet)
Local dishes are listed first. If the internet is down, local dishes still work.
Nothing else in the app talks to the API directly.

THE API (free test key is "1", already in BASE)
-----------------------------------------------
  search by name        BASE/search.php?s=Arrabiata        -> FULL meals
  filter by ingredient  BASE/filter.php?i=chicken_breast   -> only id, name, thumbnail
  filter by category    BASE/filter.php?c=Seafood          -> only id, name, thumbnail
  lookup by id          BASE/lookup.php?i=52772            -> ONE full meal
  list categories       BASE/list.php?c=list               -> category names
Every answer looks like {"meals": [ {...}, {...} ]}, and {"meals": null} means no results.

KEY IDEA
--------
filter.php gives a SHORT list (no ingredients or instructions), so for each result we
call lookup() to get the full recipe. We limit this to MAX_RESULTS meals so the app
stays fast (one extra request per meal).

ADDING A LOCAL DISH
-------------------
Open local_data/local_meals.json and copy an existing entry. Give it a unique "id"
starting with "local-", and write the ingredients as {"name": ..., "measure": ...}
using measures like "2 cups", "500g", "3 tbsp" or "1" (a count). Recipes should serve
about 4 people, because the shopping list scales from 4.

ERRORS (see exceptions.py)
--------------------------
  APIRequestError   - no internet, timeout, server error, or unreadable reply
  MealNotFoundError - the request worked but nothing matched
  ValueError        - bad input from the caller (empty search, unknown mode)

TRY IT QUICKLY in a Python shell:
    from services.mealdb_client import MealDBClient
    c = MealDBClient()
    print([r.name for r in c.search("jollof", "name")])
"""
import json
from pathlib import Path
from typing import Any, Callable

try:
    import importlib

    requests = importlib.import_module("requests")
except ModuleNotFoundError:
    class _MissingRequests:
        class RequestException(Exception):
            """Fallback exception used when the requests package is unavailable."""

        @staticmethod
        def get(*args, **kwargs):
            raise ModuleNotFoundError("The 'requests' package is required to use the MealDB client.")

    requests = _MissingRequests()

from exceptions import APIRequestError, MealNotFoundError
from models.recipe import Recipe

TIMEOUT = 10        # seconds to wait before giving up on a request
MAX_RESULTS = 6     # how many full recipes to fetch for ingredient/category searches
LOCAL_MEALS_PATH = Path(__file__).resolve().parent.parent / "local_data" / "local_meals.json"


class MealDBClient:
    BASE = "https://www.themealdb.com/api/json/v1/1"

    def __init__(self, local_meals: list[Recipe] | None = None, local_path=LOCAL_MEALS_PATH):
        """local_meals: a list of Recipe objects to use instead of the file (used by tests)."""
        self._local = local_meals
        self._local_path = Path(local_path)

    # ------------------------------------------------------------ local dishes

    def local_meals(self) -> list[Recipe]:
        """Our own dishes as Recipe objects (read once from the JSON file)."""
        if self._local is None:
            self._local = self._read_local_file()
        return self._local

    def _read_local_file(self) -> list[Recipe]:
        """Read local_meals.json. If it is missing or damaged, return [] (the app still works)."""
        try:
            with open(self._local_path, "r", encoding="utf-8") as f:
                return [Recipe.from_dict(d) for d in json.load(f)]
        except (OSError, ValueError, KeyError, TypeError):
            return []

    @staticmethod
    def _merge(local: list[Recipe], api_call: Callable[[], list[Recipe]]) -> list[Recipe]:
        """Local matches first, then the API results (without duplicates).

        If the internet request fails but we already have local matches, we show those
        instead of an error. With no local matches the error is raised as normal.
        """
        try:
            remote = api_call()
        except APIRequestError:
            if not local:
                raise
            remote = []
        known = {r.id for r in local}
        return local + [r for r in remote if r.id not in known]

    # ------------------------------------------------------------ low level

    def _get(self, endpoint: str, **params: str) -> list[dict[str, Any]]:
        """The ONE place that makes HTTP requests. All other methods use it.

        Returns the list under the "meals" key, or [] when the API says null.
        Raises APIRequestError if anything goes wrong with the request or the reply.
        """
        url = f"{self.BASE}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()      # turns 404 / 500 into an exception
            data = response.json()
        except requests.RequestException as e:   # no internet, timeout, bad status...
            raise APIRequestError(f"Could not reach TheMealDB: {e}") from e
        except ValueError as e:                  # reply was not valid JSON
            raise APIRequestError("TheMealDB sent a reply we could not read.") from e

        if not isinstance(data, dict):
            raise APIRequestError("TheMealDB sent an unexpected reply.")
        return data.get("meals") or []           # null -> []

    @staticmethod
    def _require(text: str, what: str) -> str:
        """Strip the text and make sure something is left."""
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError(f"Please enter a {what}.")
        return cleaned

    def _recipes_from_short_list(self, short_meals: list[dict[str, Any]]) -> list[Recipe]:
        """filter.php only returns id/name/thumb. Fetch the full Recipe for each one."""
        recipes: list[Recipe] = []
        for meal in short_meals[:MAX_RESULTS]:
            try:
                recipes.append(self.lookup(meal["idMeal"]))
            except MealNotFoundError:
                continue   # one broken entry should not ruin the whole search
        return recipes

    # ------------------------------------------------------------ searches

    def search_by_name(self, name: str) -> list[Recipe]:
        """Local dishes whose name contains the text + TheMealDB's search.php?s=<name>."""
        name = self._require(name, "meal name")
        wanted = name.lower()
        local = [r for r in self.local_meals() if wanted in r.name.lower()]
        results = self._merge(
            local, lambda: [Recipe.from_api(m) for m in self._get("search.php", s=name)]
        )
        if not results:
            raise MealNotFoundError(
                f"No meals found with the name '{name}'. Try another spelling, "
                "or search by ingredient or category instead."
            )
        return results

    def search_by_ingredient(self, ingredient: str) -> list[Recipe]:
        """Local dishes that use the ingredient + TheMealDB's filter.php?i=<ingredient>."""
        ingredient = self._require(ingredient, "ingredient")
        wanted = ingredient.lower()
        local = [r for r in self.local_meals()
                 if any(wanted in i.name.lower() for i in r.ingredients)]
        # The site writes multi-word ingredients with underscores: "chicken_breast"
        api_name = wanted.replace(" ", "_")
        results = self._merge(
            local, lambda: self._recipes_from_short_list(self._get("filter.php", i=api_name))
        )
        if not results:
            raise MealNotFoundError(f"No meals found with the ingredient '{ingredient}'.")
        return results

    def search_by_category(self, category: str) -> list[Recipe]:
        """Local dishes in this category or cuisine (e.g. "Nigerian") + TheMealDB's filter.php?c=."""
        category = self._require(category, "category")
        wanted = category.lower()
        local = [r for r in self.local_meals() if wanted in (r.category.lower(), r.cuisine.lower())]
        results = self._merge(
            local,
            lambda: self._recipes_from_short_list(self._get("filter.php", c=category.capitalize())),
        )
        if not results:
            raise MealNotFoundError(f"No meals found in the category '{category}'.")
        return results

    def lookup(self, meal_id: str) -> Recipe:
        """One full Recipe by id. Local ids (they start with "local-") need no internet."""
        for recipe in self.local_meals():
            if recipe.id == meal_id:
                return recipe
        meals = self._get("lookup.php", i=meal_id)
        if not meals:
            raise MealNotFoundError(f"No meal found with id '{meal_id}'.")
        return Recipe.from_api(meals[0])

    def list_categories(self) -> list[str]:
        """Category names for the dropdown: TheMealDB's, plus our local cuisines (e.g. "Nigerian")."""
        meals = self._get("list.php", c="list")
        categories = [m["strCategory"] for m in meals if m.get("strCategory")]
        known = {c.lower() for c in categories}
        for cuisine in sorted({r.cuisine for r in self.local_meals() if r.cuisine}):
            if cuisine.lower() not in known:
                categories.append(cuisine)
        return categories

    # ------------------------------------------------------------ the one the UI calls

    def search(self, query: str, mode: str) -> list[Recipe]:
        """mode is "name", "ingredient" or "category". Returns a list of Recipe objects."""
        query = self._require(query, "search term")
        if mode == "name":
            return self.search_by_name(query)
        if mode == "ingredient":
            return self.search_by_ingredient(query)
        if mode == "category":
            return self.search_by_category(query)
        raise ValueError(f"Unknown search mode: {mode}")