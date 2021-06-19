from biosimulators_utils.model_lang.lems.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class LemsValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'lems')

    def test(self):
        filename = os.path.join(self.FIXTURE_DIR, 'LEMS_NML2_Ex5_DetCell.xml')
        errors, warnings, _ = validate_model(filename)
        print(flatten_nested_list_of_strings(errors))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'no-simulation.xml')
        errors, warnings, _ = validate_model(filename)
        self.assertIn("No component found: sim1", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'undefined-target.xml')
        errors, warnings, _ = validate_model(filename)
        self.assertIn("No component found: net2", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'missing-include.xml')
        errors, warnings, _ = validate_model(filename)
        self.assertIn("Can't find file at path: Cells2.xml", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'invalid.xml')
        errors, warnings, _ = validate_model(filename)
        self.assertIn("Can't read LEMS from XMLElt", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
