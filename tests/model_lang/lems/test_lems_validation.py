from biosimulators_utils.model_lang.lems.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class LemsValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'lems')

    def test(self):
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'LEMS_NML2_Ex5_DetCell.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [['One or more includes could not be resolved and validated.']])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid.xml'))
        self.assertIn("<Lems> expected as root", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
