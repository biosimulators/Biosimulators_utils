from biosimulators_utils.model_lang.smoldyn.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class SmoldynValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn')

    def test(self):
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'bounce1.txt'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid.txt'))
        self.assertIn("not a valid Smoldyn", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'not a file.txt'))
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(None)
        self.assertIn('must be a path', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
