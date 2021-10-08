from biosimulators_utils.model_lang.neuroml.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import unittest


class NeuroMlValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'neuroml')

    def test(self):
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'IM.channel.nml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid-model.nml'))
        self.assertIn("is not valid against the schema", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, '..', 'BIOMD0000000075.xml'))
        self.assertIn("is not valid against the schema", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
