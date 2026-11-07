# OWNER: Team lead
"""
WHAT THIS FILE DOES
-------------------
Talks to the internet. MealDBClient sends HTTP requests to TheMealDB and turns the
answers into Recipe objects. Nothing else in the app calls the API directly.

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

ERRORS (see exceptions.py)
--------------------------
  APIRequestError   - no internet, timeout, server error, or unreadable reply
  MealNotFoundError - the request worked but nothing matched
  ValueError        - bad input from the caller (empty search, unknown mode)
"""

import json
import importlib
from typing import Any
from urllib import parse as urlparse
from urllib import request as urlrequest

try:
    requests = importlib.import_module("requests")
except ModuleNotFoundError:
    class _FallbackResponse:
        def __init__(self, payload: bytes, status_code: int):
            self._payload = payload
            self.status_code = status_code
            self.text = payload.decode("utf-8", errors="replace")

        def raise_for_status(self):
            if self.status_code >= 400:
                raise _FallbackRequests.RequestException(f"HTTP {self.status_code}")

        def json(self):
            return json.loads(self.text)

    class _FallbackRequests:
        class RequestException(Exception):
            pass

        @staticmethod
        def get(url: str, params=None, timeout: int | None = None):
            if params:
                query = urlparse.urlencode(params)
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}{query}"
            try:
                with urlrequest.urlopen(url, timeout=timeout) as response:
                    payload = response.read()
                    status_code = getattr(response, "status", response.getcode())
                    return _FallbackResponse(payload, status_code)
            except Exception as exc:  # pragma: no cover - fallback only when requests is absent
                raise _FallbackRequests.RequestException(str(exc)) from exc

    requests = _FallbackRequests()

from exceptions import APIRequestError, MealNotFoundError
from models.recipe import Recipe

TIMEOUT = 10        # seconds to wait before giving up on a request
MAX_RESULTS = 6     # how many full recipes to fetch for ingredient/category searches


class MealDBClient:
    BASE = "https://www.themealdb.com/api/json/v1/1"

    # ------------------------------------------------------------ low level

    def _get(self, endpoint: str, **params) -> list[Any]:
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
        recipes = []
        for meal in short_meals[:MAX_RESULTS]:
            try:
                recipes.append(self.lookup(meal["idMeal"]))
            except MealNotFoundError:
                continue   # one broken entry should not ruin the whole search
        return recipes

    # ------------------------------------------------------------ searches

    def search_by_name(self, name: str) -> list[Recipe]:
        """search.php?s=<name> -> list of full Recipe objects."""
        name = self._require(name, "meal name")
        meals = self._get("search.php", s=name)
        if not meals:
            raise MealNotFoundError(
                f"No meals found with the name '{name}'. TheMealDB's free database is limited, so try "
                "another spelling, or search by ingredient or category instead."
            )
        return [Recipe.from_api(m) for m in meals]

    def search_by_ingredient(self, ingredient: str) -> list[Recipe]:
        """filter.php?i=<ingredient> -> full Recipes that use this main ingredient."""
        ingredient = self._require(ingredient, "ingredient")
        # The site writes multi-word ingredients with underscores: "chicken_breast"
        api_name = ingredient.lower().replace(" ", "_")
        short_meals = self._get("filter.php", i=api_name)
        recipes = self._recipes_from_short_list(short_meals)
        if not recipes:
            raise MealNotFoundError(f"No meals found with the ingredient '{ingredient}'.")
        return recipes

    def search_by_category(self, category: str) -> list[Recipe]:
        """filter.php?c=<category> -> full Recipes in this category (e.g. Seafood)."""
        category = self._require(category, "category")
        short_meals = self._get("filter.php", c=category.capitalize())
        recipes = self._recipes_from_short_list(short_meals)
        if not recipes:
            raise MealNotFoundError(f"No meals found in the category '{category}'.")
        return recipes

    def lookup(self, meal_id: str) -> Recipe:
        """lookup.php?i=<id> -> one full Recipe."""
        meals = self._get("lookup.php", i=meal_id)
        if not meals:
            raise MealNotFoundError(f"No meal found with id '{meal_id}'.")
        return Recipe.from_api(meals[0])

    def list_categories(self) -> list[str]:
        """All category names, e.g. ["Beef", "Chicken", ...]. Handy for a dropdown in the UI."""
        meals = self._get("list.php", c="list")
        return [m["strCategory"] for m in meals if m.get("strCategory")]

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