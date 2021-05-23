from biosimulators_utils.cellml.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class CellMlValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'cellml')

    def test(self):
        errors, warnings = validate_model(os.path.join(self.FIXTURE_DIR, 'level2.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings = validate_model(os.path.join(self.FIXTURE_DIR, 'not_a_path.xml'))
        self.assertIn("is not a file", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid_cellml_2.0.xml'))
        self.assertIn("Start tag expected", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings = validate_model(os.path.join(self.FIXTURE_DIR, 'missing-attribute.xml'))
        self.assertIn("does not have a valid name attribute", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
