# OWNER: Team lead
"""Gemini integration: simplify steps, rate difficulty, suggest substitutes."""
import os  # noqa: F401
import json  # noqa: F401

from models.recipe import Recipe


class AIHelper:
    def __init__(self, api_key: str = None):
        """Read GEMINI_API_KEY from env if api_key is None."""
        raise NotImplementedError("TODO")

    def enhance_recipe(self, recipe: Recipe) -> dict:
        """Return {"steps": [str], "difficulty": "Easy|Medium|Hard",
        "substitutes": [{"ingredient": str, "substitute": str, "reason": str}]}.

        Ask Gemini for JSON only, strip ``` fences, json.loads it,
        cache results in data/ai_cache.json by recipe.id, and raise
        APIRequestError on failure.
        """
        raise NotImplementedError("TODO")
