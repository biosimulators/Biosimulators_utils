from biosimulators_utils.lems.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class LemsValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'lems')

    def test(self):
        errors, warnings = validate_model(os.path.join(self.FIXTURE_DIR, 'LEMS_NML2_Ex5_DetCell.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [['Includes could not be validated.']])

        errors, warnings = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid.xml'))
        self.assertIn("<Lems> expected as root", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
