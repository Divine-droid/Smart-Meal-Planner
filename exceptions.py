"""Custom exceptions shared across the app."""


class MealPlannerError(Exception):
    """Base class for all app errors."""


class MealNotFoundError(MealPlannerError):
    """No meal matched the search."""


class APIRequestError(MealPlannerError):
    """An HTTP request to TheMealDB or Gemini failed."""


class InvalidServingsError(MealPlannerError):
    """Servings input was not a valid positive whole number."""
