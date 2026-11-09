# Smart Meal Planner

A Python web app that helps you find recipes, understand them, plan a week of meals and shop for them. It searches TheMealDB and our own collection of Nigerian dishes, uses Google's Gemini AI to rewrite recipes in simple steps, rate their difficulty and suggest cheaper or locally available ingredients, and builds one combined shopping list scaled for any number of people.

Built with Python, Streamlit, Requests and the Gemini API.

## Features

- *Search*: by meal name, main ingredient or category. International and Nigerian dishes (Arriabata, Apple pie, Honey Cookies, jollof rice, egusi soup, moi moi, suya and more) appear first, then results from TheMealDB.
- *Works offline for local dishes.*: If the internet is down, the Nigerian dishes still appear.(all 12 local dishes are stored in local data/local_meals.json)
- *AI helper (Gemini):* rewrites the instructions as simple numbered steps, rates the difficulty (Easy, Medium or Hard) and suggests cheaper or locally available substitutes. Answers are cached and temporary Gemini errors are retried automatically.
- *Weekly meal planner:* add meals to any day of the week.
- *Smart shopping list:* combines the ingredients of every planned meal into one list, adds up matching items, and scales all quantities for the number of people.
- *Save and load:* the meal plan, favourite recipes and shopping list are saved to local files (JSON and CSV).
- *Friendly error handling*: unknown meals, empty searches, invalid serving numbers and failed requests show clear messages instead of crashing.

## Quick start

You need Python 3.10 or newer and a free Gemini API key from [Google AI Studio](https://aistudio.google.com).

git clone https://github.com/Divine-droid/Smart-Meal-Planner.git
cd Smart-Meal-Planner
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env

1. Open `.env` and add your key:
    GEMINI_API_KEY=your key here


2.Then run the app:
    streamlit run app.py


It opens at http://localhost:8501. Everything except the "Simplify with AI" button works without a key.

"Never commit your `.env` file." It is already listed in `.gitignore`.

### Settings

Setting (in `.env`): Required   
`GEMINI_API_KEY` For the AI button  Your Gemini API key 
`GEMINI_MODEL : Gemini model name. The default is  'gemini-3.8-flash'. Set this if Google retires the model.

## How to use it

1. Search: a meal (for example "jollof" by name, "chicken" by ingredient, or the category "Nigerian").
2. Open a recipe card. Press "Simplify with AI" for simple steps, difficulty and substitutes.
3. Choose a day and press "Add to plan". Use "Save to favourites" for recipes you like.
4. Set "Number of people" in the sidebar.
5. Open the "Shopping list" tab to see the combined, scaled list. Save the plan and the list to files.

## Project structure

```
Smart-Meal-Planner/
 app.py                 Streamlit user interface
 exceptions.py          Custom errors
 requirements.txt       The necessary requirements to run the recipe planner
 .env.example           Template for your API key 
 models/
    recipe.py           Ingredient and Recipe data classes
 services/
    mealdb_client.py    MealDBClient: local dishes + TheMealDB search
    ai_helper.py        AIHelper: Gemini steps, difficulty, substitutes
    planner.py          MealPlanner: the weekly plan
    shopping.py         ShoppingListGenerator: combined, scaled list
    storage.py          Saving and loading JSON and CSV files
 utils/
    parsing.py          Regex helpers (measures, servings, ingredient names)
 local_data/
    local_meals.json    Our Nigerian dishes
    images/             Pictures for the local dishes (optional)
 data/                  Saved plans, favourites, shopping lists (created at run time)
 tests/                 pytest tests


## How it works

Search box : MealDBClient.search()  (local dishes first, then TheMealDB) -> Recipe objects
Recipe card : AIHelper.enhance_recipe()    simple steps, difficulty, substitutes
             MealPlanner.add_meal()       weekly plan
Shopping tab : ShoppingListGenerator.generate()   uses parse_measure() and clean_ingredient_name()
Save buttons : storage.save_json() / storage.save_shopping_csv()


## Python concepts used

Concept / Where it is used 
File handling : `storage.py` saves and loads JSON and CSV. `ai_helper.py` keeps a JSON cache. `mealdb_client.py` reads `local_meals.json`.
Exception handling: Custom exceptions in `exceptions.py`. `MealDBClient._get()` handles failed requests. `AIHelper` retries temporary Gemini errors. `guarded()` in `app.py` turns every error into a friendly message. 
Regular expressions: `parsing.py` extracts quantities and units from measures such as "2 tbsp", "500g" and "1 1/2 cups", validates the serving size, and cleans ingredient names. 
OOP : The `Ingredient` and `Recipe` data classes (with `from_api` and `from_dict` class methods), and the `MealDBClient`, `AIHelper`, `MealPlanner` and `ShoppingListGenerator` classes.

## Local (Nigerian) dishes
Created this file because MealDb API does not have Nigerian local dishes, it only has international dishes. The file contains a collection of 12 popular Nigerian dishes. 
The dishes live in `local_data/local_meals.json`. To add one, copy an existing entry and change it:

- `id` must be unique and start with `local-`, for example `local-pounded-yam`.
- Write each ingredient as `{"name": "Onion", "measure": "2"}`. Measures like `"2 cups"`, `"500g"`, `"3 tbsp"` or `"1"` (a count) are understood.
- Write recipes for about 4 people, because the shopping list scales from 4.
- Put one instruction step per line.
Note: The Nigerian Local dishes do not have images for now due to some licensing problems 

## Tests
pytest
The tests use a fake network and a fake Gemini client, so they need no internet connection and no API key.
Note: not all the tests are complete some may fail due to that reason. 

## Known limitations

- TheMealDB's free database is limited, and it contains few Nigerian dishes. That is why we added our own.
- Recipes are assumed to serve 4 people when scaling the shopping list.
- Units are not converted, so "1 cup of oil" and "50 ml of oil" appear as separate lines.
- AI answers can be imperfect. Check them before cooking.
- The free Gemini tier has usage limits and is sometimes busy. The app retries and caches answers to   reduce the impact.
- Saved files are stored on the local computer. There are no user accounts.

## Troubleshooting

- "The Gemini model ... is not available": set `GEMINI_MODEL` in `.env` to a current model name from Google AI Studio.
- "Gemini is very busy": this is temporary. Wait a few seconds and press the button again.
- "Missing GEMINI_API_KEY": create `.env` from `.env.example` and add your key.
- "No meals found": try another spelling, or search by ingredient or category.
- `ModuleNotFoundError`: run commands from the project folder and run `pip install -r requirements.txt` again.
- A change does not appear: stop Streamlit with Ctrl+C and run it again.

## Team

Name / Contribution 
Divine (team lead): Project setup, `Recipe` model, `MealDBClient`, `AIHelper`, Streamlit UI, local dishes 
Khalilinc - `storage.py` - Save buttons 
Jennifer - `shopping.py` - Creates a shopping list for the searched meal

## Credits

- Recipes: [TheMealDB](https://www.themealdb.com), a free recipe API.
- AI: Google Gemini API.
- Interface: [Streamlit](https://streamlit.io).
- The Nigerian dish recipes were written by CLAUDE.