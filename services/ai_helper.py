# OWNER: Team lead
"""
WHAT THIS FILE DOES
-------------------
Sends a recipe to the Gemini AI and returns three things:
  1. the instructions rewritten as simple numbered steps
  2. a difficulty level: "Easy", "Medium" or "Hard"
  3. cheaper or locally available ingredient substitutes

THE FLOW
--------
  Recipe -> check cache -> build prompt -> call Gemini -> parse JSON -> clean up -> save to cache

WHAT THE APP RECEIVES (always this shape):
  {
    "steps": ["Chop the onions.", "Fry them in oil.", ...],
    "difficulty": "Easy",
    "substitutes": [{"ingredient": "Basmati rice", "substitute": "Local long-grain rice",
                     "reason": "Cheaper and easy to find in Nigerian markets"}]
  }

SETUP
-----
  * GEMINI_API_KEY in your local .env file (never commit it).
  * Optional: GEMINI_MODEL in .env if the default model name stops working. Check the
    current model names at https://ai.google.dev/gemini-api/docs
  * Answers are cached in data/ai_cache.json by recipe id, so the same recipe never
    uses your free quota twice.
"""
import json
import importlib
import os
import re
from typing import Any
from exceptions import APIRequestError
from models.recipe import Recipe

try:
    load_dotenv = importlib.import_module("dotenv").load_dotenv
except ImportError:  # python-dotenv is optional; env vars still work without it
    load_dotenv = None

DEFAULT_MODEL = "gemini-2.5-flash"
CACHE_PATH = os.path.join("data", "ai_cache.json")
VALID_DIFFICULTIES = ("Easy", "Medium", "Hard")
MAX_INSTRUCTION_CHARS = 6000  # keep prompts small so requests stay fast and cheap


class AIHelper:
    def __init__(self, api_key: str | None = None, model: str | None = None,
                 cache_path: str = CACHE_PATH, client=None):
        """Set up the Gemini client.

        api_key / model: optional overrides. Normally they come from the .env file.
        client: for tests only - pass a fake client so no real API call is made.
        """
        if load_dotenv:
            load_dotenv()  # copies values from .env into environment variables
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        self.cache_path = cache_path

        if client is not None:  # used by the tests
            self.client = client
            return

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise APIRequestError("Missing GEMINI_API_KEY. Put it in your .env file ""(copy .env.example to .env and add your key).")
        try:
            genai: Any = importlib.import_module("google.genai")
        except ImportError as e:
            raise APIRequestError(
                "The google-genai package is not installed. Run: pip install google-genai"
            ) from e
        self.client = genai.Client(api_key=key)

    # ------------------------------------------------------------------ public

    def enhance_recipe(self, recipe: Recipe, use_cache: bool = True) -> dict[str, Any]:
        """Return {"steps": [...], "difficulty": "...", "substitutes": [...]} for a recipe.

        Raises APIRequestError if Gemini cannot be reached or returns unusable output.
        """
        # 1. Cache: if we already asked Gemini about this recipe, reuse the answer.
        cache = self._load_cache() if use_cache else {}
        if use_cache and recipe.id and recipe.id in cache:
            return cache[recipe.id]

        # 2. Ask Gemini. Models sometimes return broken JSON, so we try twice.
        prompt = self._build_prompt(recipe)
        result, last_error = None, None
        for _attempt in range(2):
            text = self._call_gemini(prompt)
            try:
                result = self._normalize(self._parse_json(text))
                break
            except ValueError as e:
                last_error = e
        if result is None:
            raise APIRequestError(f"Gemini returned an answer we could not read: {last_error}")

        # 3. Save for next time.
        if use_cache and recipe.id:
            cache[recipe.id] = result
            self._save_cache(cache)
        return result

    # ----------------------------------------------------------------- helpers

    def _build_prompt(self, recipe: Recipe) -> str:
        """Turn a Recipe into the instruction text we send to Gemini."""
        ingredient_lines = "\n".join(
            f"- {i.measure} {i.name}".strip() for i in recipe.ingredients
        ) or "- (no ingredients listed)"
        instructions = (recipe.instructions or "(no instructions provided)")[:MAX_INSTRUCTION_CHARS]

        return f"""You are a friendly cooking assistant helping students in Nigeria.

Recipe: {recipe.name}
Category: {recipe.category or "unknown"}   Cuisine: {recipe.cuisine or "unknown"}

Ingredients:
{ingredient_lines}

Original instructions:
{instructions}

Do three things:
1. Rewrite the instructions as short, simple numbered steps a beginner can follow.
   Each step is one clear action, written without the number itself.
2. Rate the difficulty for a beginner cook: exactly "Easy", "Medium" or "Hard".
3. Suggest cheaper or more locally available substitutes (for example in Nigerian markets)
   for ingredients that may be expensive or hard to find. Skip ingredients that are
   already cheap and common. Return an empty list if none are needed.

Respond with ONLY a JSON object, no extra text, in exactly this shape:
{{"steps": ["..."], "difficulty": "Easy", "substitutes": [{{"ingredient": "...", "substitute": "...", "reason": "..."}}]}}"""

    def _call_gemini(self, prompt: str) -> str:
        """Send the prompt and return Gemini's raw text. Raises APIRequestError on failure."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.3},
            )
        except Exception as e:  # the SDK can raise many kinds of errors
            msg = str(e)
            hint = ""
            if "404" in msg or "NOT_FOUND" in msg:
                hint = (f" The model '{self.model}' may no longer exist. Set GEMINI_MODEL in "
                        "your .env to a current model name from Google AI Studio.")
            elif "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                hint = " You may have hit the free quota. Wait a minute and try again."
            elif "401" in msg or "403" in msg or "API key" in msg or "PERMISSION_DENIED" in msg:
                hint = " Check that GEMINI_API_KEY in your .env is correct."
            raise APIRequestError(f"Gemini request failed: {msg}{hint}") from e

        text = getattr(response, "text", None)
        if not text:
            raise APIRequestError("Gemini returned an empty response.")
        return text

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Turn Gemini's text into a dict. Handles ```json fences and extra words around it."""
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object found in the reply")
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid JSON: {e}") from e

    @staticmethod
    def _normalize(data: Any) -> dict[str, Any]:
        """Make sure the dict has exactly the shape the app expects, whatever Gemini sent."""
        if not isinstance(data, dict):
            raise ValueError("reply is not a JSON object")

        steps = data.get("steps") or []
        if isinstance(steps, str):
            steps = [steps]
        cleaned_steps = []
        for s in steps:
            # remove numbering like "1." or "Step 2:" because the UI adds its own numbers
            text = re.sub(r"^\s*(?:step\s*)?\d+\s*[.):\-]\s*", "", str(s), flags=re.IGNORECASE).strip()
            if text:
                cleaned_steps.append(text)
        if not cleaned_steps:
            raise ValueError("no steps in the reply")

        difficulty = str(data.get("difficulty", "")).strip().capitalize()
        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "Medium"  # safe default if Gemini says something unexpected

        substitutes = []
        for item in data.get("substitutes") or []:
            if isinstance(item, dict) and item.get("ingredient") and item.get("substitute"):
                substitutes.append({
                    "ingredient": str(item["ingredient"]).strip(),
                    "substitute": str(item["substitute"]).strip(),
                    "reason": str(item.get("reason", "")).strip(),
                })

        return {"steps": cleaned_steps, "difficulty": difficulty, "substitutes": substitutes}

    # ------------------------------------------------------------------- cache
    # The cache is "best effort": if it cannot be read or written, the app still works.

    def _load_cache(self) -> dict[str, Any]:
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            print(f"Warning: could not read cache from {self.cache_path}. Continuing without cache.")
            return {}

    def _save_cache(self, cache: dict[str, Any]) -> None:
        try:
            folder = os.path.dirname(self.cache_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except OSError:
            print(f"Warning: could not write cache to {self.cache_path}. Continuing without cache.")
            pass
