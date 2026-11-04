import unittest
from exceptions import InvalidServingsError
from utils.parsing import parse_measure, parse_servings, clean_ingredient_name


class TestParsing(unittest.TestCase):
    def test_parse_measure(self):
        cases = [
            ("2 tbsp", (2.0, "tbsp")),
            ("500g", (500.0, "g")),
            ("1 1/2 cups", (1.5, "cups")),
            ("1/4 tsp", (0.25, "tsp")),
            ("pinch", (None, "pinch")),
            ("", (None, "")),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(parse_measure(text), expected)


    def test_parse_servings_valid(self):
        self.assertEqual(parse_servings("4"), 4)
        self.assertEqual(parse_servings(" 2 "), 2)


    def test_parse_servings_invalid(self):
        for bad in ["0", "-3", "abc", "2.5", ""]:
            with self.subTest(value=bad):
                with self.assertRaises(InvalidServingsError):
                    parse_servings(bad)


    def test_clean_ingredient_name(self):
        self.assertEqual(clean_ingredient_name("  Chicken Breasts "), "chicken breast")
        self.assertEqual(clean_ingredient_name("Tomato (chopped)"), "tomato")
        self.assertEqual(clean_ingredient_name("Olive  Oil"), "olive oil")
