# OWNER: ______
"""Streamlit UI. Run with: streamlit run app.py"""
from importlib import import_module

try:
	st = import_module("streamlit")
except ModuleNotFoundError as exc:
	if exc.name != "streamlit":
		raise
	raise SystemExit("Streamlit is required. Install it with: python -m pip install streamlit") from exc

from services.mealdb_client import MealDBClient
from services.planner import MealPlanner
from services.shopping import ShoppingListGenerator
from utils.parsing import parse_servings

st.title("Smart Meal Planner")

# TODO 1: search box + radio ("name", "ingredient", "category") -> client.search()
# TODO 2: show results (name, image, category, cuisine, ingredients, instructions)
# TODO 3: "Simplify with AI" button -> AIHelper.enhance_recipe()
# TODO 4: choose day + "Add to plan" (keep MealPlanner in st.session_state)
# TODO 5: servings input (validate with parse_servings, show st.error on failure)
# TODO 6: "Generate shopping list" -> table + "Save plan and list" buttons
# Wrap every call in try/except and show friendly messages with st.error / st.warning.
