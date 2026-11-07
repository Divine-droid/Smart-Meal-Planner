"""Tests for AIHelper. uses a FAKE Gemini client, so no internet or API key is needed."""
# pyright: reportMissingImports=false
import json

import pytest

from exceptions import APIRequestError
from models.recipe import Recipe
from services import ai_helper
from services.ai_helper import AIHelper

GOOD = json.dumps({
    "steps": ["1. Chop the onions.", "Step 2: Fry them in oil."],
    "difficulty": "easy",
    "substitutes": [
        {"ingredient": "Basmati rice", "substitute": "Local rice", "reason": "Cheaper"},
        {"ingredient": "", "substitute": "ignored", "reason": "missing ingredient name"},
    ],
})


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return FakeResponse(reply)


class FakeClient:
    def __init__(self, replies):
        self.models = FakeModels(replies)


def make_helper(tmp_path, replies):
    client = FakeClient(replies)
    return AIHelper(client=client, cache_path=str(tmp_path / "cache.json")), client


def recipe():
    return Recipe.from_api({"idMeal": "42", "strMeal": "Jollof Rice", "strInstructions": "Cook it.",
                            "strIngredient1": "Rice", "strMeasure1": "2 cups"})


def test_normal_reply_is_cleaned(tmp_path):
    helper, _ = make_helper(tmp_path, [GOOD])
    out = helper.enhance_recipe(recipe())
    assert out["steps"] == ["Chop the onions.", "Fry them in oil."]   # numbering removed
    assert out["difficulty"] == "Easy"                                # capitalised
    assert out["substitutes"] == [{"ingredient": "Basmati rice", "substitute": "Local rice", "reason": "Cheaper"}]


def test_json_in_code_fence_is_accepted(tmp_path):
    helper, _ = make_helper(tmp_path, ["```json\n" + GOOD + "\n```"])
    assert helper.enhance_recipe(recipe())["difficulty"] == "Easy"


def test_unknown_difficulty_defaults_to_medium(tmp_path):
    reply = json.dumps({"steps": ["Cook."], "difficulty": "Impossible", "substitutes": []})
    helper, _ = make_helper(tmp_path, [reply])
    assert helper.enhance_recipe(recipe())["difficulty"] == "Medium"


def test_second_call_uses_cache(tmp_path):
    helper, client = make_helper(tmp_path, [GOOD])
    first = helper.enhance_recipe(recipe())
    second = helper.enhance_recipe(recipe())   # would crash if it called Gemini again
    assert first == second
    assert client.models.calls == 1


def test_retries_once_on_bad_json(tmp_path):
    helper, client = make_helper(tmp_path, ["not json at all", GOOD])
    assert helper.enhance_recipe(recipe())["steps"]
    assert client.models.calls == 2


def test_gives_up_after_two_bad_replies(tmp_path):
    helper, _ = make_helper(tmp_path, ["nope", "still nope"])
    with pytest.raises(APIRequestError):
        helper.enhance_recipe(recipe())


def test_sdk_error_becomes_api_request_error(tmp_path):
    helper, _ = make_helper(tmp_path, [RuntimeError("503 service unavailable")])
    with pytest.raises(APIRequestError):
        helper.enhance_recipe(recipe())


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(ai_helper, "load_dotenv", None)   # don't read a real .env during the test
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(APIRequestError):
        AIHelper()