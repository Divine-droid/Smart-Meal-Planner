# OWNER: Team lead
"""
WHAT THIS FILE DOES
-------------------
The user interface (Streamlit). It only DISPLAYS things and calls the other files:

  MealDBClient          -> search for recipes             (services/mealdb_client.py)
  AIHelper              -> simple steps, difficulty, substitutes (services/ai_helper.py)
  MealPlanner           -> the weekly plan                (services/planner.py)
  ShoppingListGenerator -> combined, scaled shopping list (services/shopping.py)
  storage               -> save / load JSON and CSV files (services/storage.py)
  parse_servings        -> check the "number of people" box (utils/parsing.py)

HOW STREAMLIT WORKS (important!)
--------------------------------
Streamlit re-runs this whole file from top to bottom every time the user clicks a
button or types something. Normal variables are reset on every run, so anything that
must be remembered (the meal plan, search results, AI answers) lives in
st.session_state.

WHILE THE TEAM IS STILL WORKING
-------------------------------
Any function that is still a TODO raises NotImplementedError. The `guarded(...)` helper
below catches that and shows a yellow "not finished yet" message instead of crashing,
so the app runs even when only some parts are done. When a teammate finishes their
function, the matching feature starts working with no change to this file.

RUN IT:  streamlit run app.py
"""
from contextlib import contextmanager
from typing import Any

import streamlit as st  # pyright: ignore[reportMissingImports]

from exceptions import InvalidServingsError, MealNotFoundError, MealPlannerError
from models.recipe import Recipe
from services import storage
from services.ai_helper import AIHelper
from services.mealdb_client import MealDBClient
from services.planner import MealPlanner
from services.shopping import ShoppingListGenerator
from utils.parsing import parse_servings

st.set_page_config(page_title="Smart Meal Planner", page_icon="🍲", layout="wide")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PLAN_FILE = "meal_plan.json"
FAVOURITES_FILE = "favourites.json"
SHOPPING_FILE = "shopping_list.csv"


# ---------------------------------------------------------------- helpers

@contextmanager
def guarded(feature: str):
    """Run the code inside `with guarded("..."):` and show a friendly message on errors.

    This is our central ERROR HANDLING: no matter which part fails, the user sees a
    message instead of a crash.
    """
    try:
        yield
    except NotImplementedError:
        st.warning(f"{feature} isn't finished yet (a TODO function is still empty).")
    except MealNotFoundError as e:           # unknown meal / empty result
        st.warning(str(e))
    except MealPlannerError as e:            # failed API request, invalid servings, ...
        st.error(str(e))
    except ValueError as e:                  # empty search box, unknown search mode
        st.warning(str(e))
    except OSError as e:                     # could not read or write a file
        st.error(f"File problem ({feature.lower()}): {e}")


def init_state():
    """Create the things we want to remember between reruns (only the first time)."""
    if "planner" not in st.session_state:
        st.session_state.planner = MealPlanner()
    st.session_state.setdefault("results", [])        # recipes from the last search
    st.session_state.setdefault("ai", {})             # recipe id -> Gemini answer
    st.session_state.setdefault("servings_input", "4")


def get_ai() -> AIHelper:
    """Create the Gemini helper the first time it is needed (it needs the API key)."""
    if "ai_helper" not in st.session_state:
        st.session_state.ai_helper = AIHelper(model="gemini-3.8-flash")
    return st.session_state.ai_helper


@st.cache_data(show_spinner=False, ttl=3600)
def _fetch_categories() -> list[str]:
    return MealDBClient().list_categories()


def get_categories() -> list[str]:
    """Category names for the dropdown. If the request fails, return [] (we then show a text box)."""
    try:
        return _fetch_categories()
    except Exception:
        return []


def load_favourites() -> list[Recipe]:
    """Saved favourite recipes as Recipe objects ([] if none or the file can't be read)."""
    try:
        raw: list[dict[str, object]] = storage.load_json(FAVOURITES_FILE, default=[]) or []
        if not isinstance(raw, list):
            return []
        return [Recipe.from_dict(d) for d in raw if isinstance(d, dict)]
    except (NotImplementedError, KeyError, TypeError):
        return []


def load_plan_callback():
    """Runs when 'Load saved plan' is clicked. It runs BEFORE the page reruns, which is
    the only moment we are allowed to change the servings box. Messages are stored in
    st.session_state.flash and shown at the top of the next run."""
    try:
        data = storage.load_json(PLAN_FILE, default=None)
        if not data:
            st.session_state.flash = ("warning", "No saved meal plan found yet. Save one first.")
            return
        planner = MealPlanner.from_dict(data)
        st.session_state.planner = planner
        st.session_state.servings_input = str(planner.servings)
        st.session_state.flash = ("success", "Meal plan loaded.")
    except NotImplementedError:
        st.session_state.flash = ("warning", "Loading isn't finished yet (a TODO function is still empty).")
    except (MealPlannerError, ValueError, KeyError, TypeError) as e:
        st.session_state.flash = ("error", f"Could not load the saved plan: {e}")


def format_quantity(qty) -> str:
    """400.0 -> '400',  1.5 -> '1.5',  None -> ''"""
    return "" if qty is None else f"{round(qty, 2):g}"


# ---------------------------------------------------------------- recipe card

def show_ai_result(result: dict[str, Any]):
    """Display the Gemini answer: difficulty, simple steps, substitutes."""
    st.markdown(f"**Difficulty:** {result['difficulty']}")
    st.markdown("**Simple steps**")
    st.markdown("\n".join(f"{n}. {step}" for n, step in enumerate(result["steps"], start=1)))
    if result["substitutes"]:
        st.markdown("**Cheaper / locally available substitutes**")
        st.dataframe(
            [{"Ingredient": s["ingredient"], "Substitute": s["substitute"], "Why": s["reason"]}
             for s in result["substitutes"]],
            hide_index=True,
        )


def show_recipe(recipe: Recipe, ctx: str, planner: MealPlanner, fav_ids: set[str], expanded: bool = False):
    """One recipe as an expandable card with its buttons.

    ctx ("search" or "fav") keeps button keys unique when the same recipe is shown in
    two tabs. Streamlit needs every widget to have a unique key.
    """
    title = recipe.name + (f"  ·  {recipe.category}" if recipe.category else "")
    with st.expander(title, expanded=expanded):
        left, right = st.columns([1, 3])
        with left:
            if recipe.thumbnail:
                st.image(recipe.thumbnail)
        with right:
            st.markdown(f"**Category:** {recipe.category or '-'}   |   **Cuisine:** {recipe.cuisine or '-'}")
            st.markdown("**Ingredients**")
            st.markdown("\n".join(f"- {i.measure} {i.name}".replace("-  ", "- ") for i in recipe.ingredients))

        key = f"{ctx}_{recipe.id}"
        col_ai, col_plan, col_fav = st.columns(3)

        with col_ai:
            if st.button("Simplify with AI", key=f"{key}_ai"):
                with guarded("The AI helper"):
                    with st.spinner("Asking Gemini..."):
                        enhance_recipe = getattr(get_ai(), "enhance_recipe", None)
                        if not callable(enhance_recipe):
                            raise NotImplementedError
                        st.session_state.ai[recipe.id] = enhance_recipe(recipe)

        with col_plan:
            day = st.selectbox("Day", DAYS, key=f"{key}_day", label_visibility="collapsed")
            if st.button("Add to plan", key=f"{key}_add"):
                with guarded("The meal planner"):
                    planner.add_meal(day, recipe)
                    st.success(f"Added to {day}.")

        with col_fav:
            is_fav = recipe.id in fav_ids
            if st.button("Remove from favourites" if is_fav else "Save to favourites", key=f"{key}_fav"):
                saved = False
                with guarded("Saving favourites"):
                    current = [r for r in load_favourites() if r.id != recipe.id]
                    if not is_fav:
                        current.append(recipe)
                    storage.save_json(FAVOURITES_FILE, [r.to_dict() for r in current])
                    saved = True
                if saved:
                    st.rerun()   # refresh the Favourites tab

        # Gemini answer (shown after the buttons so it appears right after the click)
        if recipe.id in st.session_state.ai:
            show_ai_result(st.session_state.ai[recipe.id])

        st.markdown("**Original instructions**")
        st.markdown((recipe.instructions or "No instructions provided.").replace("\r\n", "\n\n"))


# ---------------------------------------------------------------- page

init_state()
st.title("Smart Meal Planner")

flash = st.session_state.pop("flash", None)   # message left by a callback
if flash:
    getattr(st, flash[0])(flash[1])

planner = st.session_state.planner
favourites = load_favourites()
fav_ids = {r.id for r in favourites}

# ---- sidebar: number of people -------------------------------------------
servings = None
with st.sidebar:
    st.header("Settings")
    raw_servings = st.text_input("Number of people", key="servings_input")
    try:
        servings = parse_servings(raw_servings)
    except (InvalidServingsError, ValueError) as e:
        st.error(str(e))
    except NotImplementedError:
        st.warning("Servings check isn't finished yet (parse_servings is still a TODO).")
    st.caption("Quantities in the shopping list are scaled for this many people.")
if servings:
    planner.servings = servings

tab_search, tab_plan, tab_shop, tab_fav = st.tabs(["Search", "Meal plan", "Shopping list", "Favourites"])

# ---- Search tab ------------------------------------------------------------
with tab_search:
    mode = st.radio("Search by", ["name", "ingredient", "category"], horizontal=True, key="search_mode")
    with st.form("search_form"):
        if mode == "category":
            categories = get_categories()
            if categories:
                query = st.selectbox("Category", categories, key="search_category")
            else:
                query = st.text_input("Category (e.g. Seafood)", key="search_query_category")
        elif mode == "ingredient":
            query = st.text_input("Main ingredient (e.g. chicken breast)", key="search_query_ingredient")
        else:
            query = st.text_input("Meal name (e.g. Arrabiata)", key="search_query")
        submitted = st.form_submit_button("Search")

    if submitted:
        st.session_state.results = []
        with guarded("Search"):
            with st.spinner("Searching..."):
                st.session_state.results = MealDBClient().search(query, mode)

    results = st.session_state.results
    if not results and not submitted:
        st.caption("Search for a meal to get started.")
    for recipe in results:
        show_recipe(recipe, "search", planner, fav_ids, expanded=(len(results) == 1))

# ---- Meal plan tab ---------------------------------------------------------
with tab_plan:
    st.subheader("Your weekly plan")
    if servings:
        st.caption(f"Planning for {servings} {'person' if servings == 1 else 'people'}")

    has_meals = False
    for day in DAYS:
        meals = planner.plan.get(day, [])
        if not meals:
            continue
        has_meals = True
        st.markdown(f"**{day}**")
        for idx, recipe in enumerate(list(meals)):
            col_name, col_btn = st.columns([4, 1])
            col_name.write(recipe.name)
            if col_btn.button("Remove", key=f"rm_{day}_{idx}_{recipe.id}"):
                removed = False
                with guarded("Removing a meal"):
                    planner.remove_meal(day, recipe.id)
                    removed = True
                if removed:
                    st.rerun()
    if not has_meals:
        st.info("No meals planned yet. Search for a meal and press 'Add to plan'.")

    col_save, col_load = st.columns(2)
    with col_save:
        if st.button("Save meal plan to file", key="save_plan"):
            with guarded("Saving the meal plan"):
                path = storage.save_json(PLAN_FILE, planner.to_dict())
                st.success(f"Saved to {path}")
    with col_load:
        st.button("Load saved plan", key="load_plan", on_click=load_plan_callback)

# ---- Shopping list tab -----------------------------------------------------
with tab_shop:
    st.subheader("Shopping list")
    items = None
    with guarded("The meal planner"):
        planned = planner.all_recipes()
        if not planned:
            st.info("Add some meals to your plan and the combined shopping list will appear here.")
        elif servings is None:
            st.warning("Fix the 'Number of people' box in the sidebar to see the scaled list.")
        else:
            with guarded("The shopping list"):
                items = ShoppingListGenerator().generate(planned, servings)

    if items:
        st.caption(f"Combined from {len(planned)} planned meal(s), scaled for {servings} "
                   f"{'person' if servings == 1 else 'people'}.")
        st.dataframe(
            [{"Item": i["name"].title(), "Quantity": format_quantity(i["quantity"]),
              "Unit": i["unit"], "Note": i["note"]} for i in items],
            hide_index=True,
        )
        if st.button("Save shopping list to file", key="save_shopping"):
            with guarded("Saving the shopping list"):
                path = storage.save_shopping_csv(SHOPPING_FILE, items)
                st.success(f"Saved to {path}")

# ---- Favourites tab --------------------------------------------------------
with tab_fav:
    st.subheader("Favourite recipes")
    if not favourites:
        st.caption("Recipes you save with 'Save to favourites' appear here.")
    for recipe in favourites:
        show_recipe(recipe, "fav", planner, fav_ids)