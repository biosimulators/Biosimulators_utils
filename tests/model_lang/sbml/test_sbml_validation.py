from biosimulators_utils.model_lang.sbml.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class ValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures')

    def test(self):
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'sbml-list-of-species.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'sbml-invalid-model.xml'))
        self.assertIn("species attribute 'id' is required", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(None)
        self.assertIn('must be a path', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
