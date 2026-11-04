import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from validation import find_placeholders


class PlaceholderTests(unittest.TestCase):

    def test_multiple_placeholders(self):
        text = "[Date] at [Time], [Location]"
        expected = ["[Date]", "[Time]", "[Location]"]

        self.assertEqual(find_placeholders(text), expected)

    def test_no_placeholders(self):
        text = "Meeting on 10 January 2027 at Community Hall"

        self.assertEqual(find_placeholders(text), [])

    def test_duplicate_placeholders(self):
        text = "[Date] and another [Date]"

        self.assertEqual(find_placeholders(text), ["[Date]"])

    def test_empty_brackets(self):
        text = "Hello []"

        self.assertEqual(find_placeholders(text), [])

    def test_empty_text(self):
        self.assertEqual(find_placeholders(""), [])

    def test_invalid_input(self):
        with self.assertRaises(TypeError):
            find_placeholders(123)


if __name__ == "__main__":
    unittest.main(verbosity=2)
