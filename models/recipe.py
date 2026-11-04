# OWNER: Team lead (DONE - do not edit without telling the lead)
"""Recipe data model. Every other module depends on these fields."""
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Ingredient:
    name: str      # e.g. "Chicken Breast"
    measure: str   # raw text from the API, e.g. "1 1/2 cups"


@dataclass
class Recipe:
    id: str
    name: str
    category: str = ""
    cuisine: str = ""
    instructions: str = ""
    thumbnail: str = ""
    ingredients: list[Ingredient] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, str | None]) -> "Recipe":
        """Build a Recipe from one TheMealDB meal dict."""
        ingredients = []
        for i in range(1, 21):
            name = (data.get(f"strIngredient{i}") or "").strip()
            measure = (data.get(f"strMeasure{i}") or "").strip()
            if name:
                ingredients.append(Ingredient(name=name, measure=measure))
        return cls(
            id=data.get("idMeal") or "",
            name=data.get("strMeal") or "",
            category=data.get("strCategory") or "",
            cuisine=data.get("strArea") or "",
            instructions=data.get("strInstructions") or "",
            thumbnail=data.get("strMealThumb") or "",
            ingredients=ingredients,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Recipe":
        d = dict(d)
        d["ingredients"] = [Ingredient(**i) for i in d.get("ingredients", [])]
        return cls(**d)
