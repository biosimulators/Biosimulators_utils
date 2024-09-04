from biosimulators_utils.model_lang.rba import validation
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import rba
import unittest


class RbaValidationTestCase(unittest.TestCase):
    FIXTURE_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'rba')

    def test(self):
        filename = os.path.join(self.FIXTURE_DIRNAME, 'Escherichia-coli-K12-WT.zip')
        errors, warnings, model = validation.validate_model(filename)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertIsInstance(model, rba.model.RbaModel)

        filename = None
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('is not a path', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'not exist.zip')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('does not exist', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = __file__
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('is not a valid RBA', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'Escherichia-coli-K12-WT-invalid.zip')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('is not a valid RBA', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)
