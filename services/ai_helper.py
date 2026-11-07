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
import importlib
import json
import os
import re
import time
from typing import Optional

from exceptions import APIRequestError
from models.recipe import Recipe

try:
    load_dotenv = importlib.import_module("dotenv").load_dotenv
except ModuleNotFoundError:  # python-dotenv is optional; env vars still work without it
    def load_dotenv() -> bool:
        return False

DEFAULT_MODEL = "gemini-3.8-flash"
CACHE_PATH = os.path.join("data", "ai_cache.json")
VALID_DIFFICULTIES = ("Easy", "Medium", "Hard")
MAX_INSTRUCTION_CHARS = 6000  # keep prompts small so requests stay fast and cheap
RETRY_DELAYS = (1, 3)         # seconds to wait before the 2nd and 3rd try when Gemini is busy


class AIHelper:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 cache_path: str = CACHE_PATH, client=None, retry_delays=RETRY_DELAYS):
        """Set up the Gemini client.

        api_key / model: optional overrides. Normally they come from the .env file.
        client: for tests only - pass a fake client so no real API call is made.
        retry_delays: seconds to wait between retries when Gemini is temporarily busy.
        """
        if load_dotenv:
            load_dotenv()  # copies values from .env into environment variables
        self.model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
        self.cache_path = cache_path
        self.retry_delays = retry_delays

        if client is not None:  # used by the tests
            self.client = client
            return

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise APIRequestError(
                "Missing GEMINI_API_KEY. Put it in your .env file "
                "(copy .env.example to .env and add your key)."
            )
        try:
            # Import the SDK lazily so the rest of the app still works without the package.
            genai = importlib.import_module("google.genai")
        except ImportError as e:
            raise APIRequestError(
                "The google-genai package is not installed. Run: pip install google-genai"
            ) from e
        self.client = genai.Client(api_key=key)

    # ------------------------------------------------------------------ public

    def enhance_recipe(self, recipe: Recipe, use_cache: bool = True) -> dict[str, object]:
        """Return {"steps": [...], "difficulty": "...", "substitutes": [...]} for a recipe.

        Raises APIRequestError if Gemini cannot be reached or returns unusable output.
        """
        # 1. Cache: if we already asked Gemini about this recipe, reuse the answer.
        cache: dict[str, dict[str, object]] = self._load_cache() if use_cache else {}
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
        """Send the prompt and return Gemini's raw text. Raises APIRequestError on failure.

        If Gemini says it is temporarily busy (503 and similar), we wait a moment and try
        again (see RETRY_DELAYS) before giving up. Other errors fail immediately.
        """
        response = None
        for attempt in range(len(self.retry_delays) + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.3},
                )
                break
            except Exception as e:  # the SDK can raise many kinds of errors
                msg = str(e)
                if self._is_temporary(msg) and attempt < len(self.retry_delays):
                    time.sleep(self.retry_delays[attempt])
                    continue
                raise APIRequestError(self._friendly_error(msg)) from e

        text = getattr(response, "text", None)
        if not text:
            raise APIRequestError("Gemini returned an empty response.")
        return text

    @staticmethod
    def _is_temporary(msg: str) -> bool:
        """True for errors that usually disappear if we simply try again."""
        return bool(re.search(r"\b(500|502|503|504)\b", msg)) or any(
            word in msg for word in ("UNAVAILABLE", "INTERNAL", "DEADLINE_EXCEEDED", "high demand")
        )

    def _friendly_error(self, msg: str) -> str:
        """Turn a raw SDK error into one short sentence the user can act on."""
        if "404" in msg or "NOT_FOUND" in msg:
            return (f"The Gemini model '{self.model}' is not available. Set GEMINI_MODEL in your "
                    ".env file to a current model name (see https://ai.google.dev/gemini-api/docs/models).")
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            return "You may have hit the free Gemini quota. Wait a minute and try again."
        if "401" in msg or "403" in msg or "API key" in msg or "PERMISSION_DENIED" in msg:
            return "Gemini rejected the request. Check that GEMINI_API_KEY in your .env is correct."
        if self._is_temporary(msg):
            return "Gemini is very busy right now (this is temporary). Wait a few seconds and press the button again."
        return f"Gemini request failed: {msg[:300]}"

    @staticmethod
    def _parse_json(text: str) -> dict[str, object]:
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
    def _normalize(data) -> dict[str, object]:
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

    def _load_cache(self) -> dict[str, dict[str, object]]:
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): v for k, v in data.items() if isinstance(v, dict)}
            return {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_cache(self, cache: dict[str, dict[str, object]]) -> None:
        try:
            folder = os.path.dirname(self.cache_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except OSError:
            pass