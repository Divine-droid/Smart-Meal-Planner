"""
WHAT THIS FILE DOES
-------------------
Defines our own error types. Instead of letting the program crash with a
confusing message, each part of the app raises one of these when something
specific goes wrong, and the UI (app.py) catches it and shows a friendly message.

HOW TO USE (example)
--------------------
    raise MealNotFoundError("No meal found for 'xyz'")      # in mealdb_client.py

    try:
        client.search("xyz", "name")
    except MealNotFoundError as e:
        st.warning(str(e))                                  # in app.py

All four classes inherit from MealPlannerError, so `except MealPlannerError`
catches any of them at once.
"""
"""Custom exceptions shared across the app."""


class MealPlannerError(Exception):
    """Base class for all app errors."""


class MealNotFoundError(MealPlannerError):
    """No meal matched the search."""


class APIRequestError(MealPlannerError):
    """An HTTP request to TheMealDB or Gemini failed."""


class InvalidServingsError(MealPlannerError):
    """Servings input was not a valid positive whole number."""
