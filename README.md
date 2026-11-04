# Smart Meal Planner

Search meals (TheMealDB), simplify recipes with Gemini, plan several days,
get one combined, scaled shopping list, and save everything to a local file.

## Setup
```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your Gemini key in .env
streamlit run app.py
pytest                           # run tests; a function is DONE when its tests pass
```

## Team workflow
1. Work ONLY on your own branch: `git checkout -b yourname-task`
2. Fill in the `TODO` functions in your file(s). Do not rename functions or change their inputs/outputs.
3. Run `pytest tests/test_yourfile.py` until it passes.
4. Push your branch and tell the team lead. Do not push to `main`.

## Task board
| File | Owner | Level |
|---|---|---|
| models/recipe.py | Team lead | done |
| services/ai_helper.py | Team lead | 
| services/mealdb_client.py | ______ | |
| services/shopping.py | ______ |  |
| services/planner.py | ______ |  |
| utils/parsing.py (parse_measure) | ______ 
| utils/parsing.py (parse_servings, clean_ingredient_name) | ______ 
| services/storage.py | ______ | 
| app.py (Streamlit UI) | ______ |
| tests + README polish | ______ | 

## Key facts about TheMealDB
- Base URL: https://www.themealdb.com/api/json/v1/1
- `search.php?s=name` returns FULL meals. `filter.php?i=` and `filter.php?c=` return only id/name/thumb,
  so call `lookup.php?i=<id>` for the full recipe.
- When nothing is found the API returns `{"meals": null}`.
- Ingredients are `strIngredient1..20` and `strMeasure1..20`; many are empty strings.
