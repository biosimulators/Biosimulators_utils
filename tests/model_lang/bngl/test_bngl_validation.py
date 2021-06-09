from biosimulators_utils.model_lang.bngl.validation import validate_model, read_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import os
import shutil
import tempfile
import unittest


class BgnlValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl')

    def test(self):
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'valid.bngl'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        fid, filename = tempfile.mkstemp()
        os.close(fid)
        shutil.copyfile(os.path.join(self.FIXTURE_DIR, 'valid.bngl'), filename)
        errors, warnings, _ = validate_model(filename)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        os.remove(filename)

        _, errors, _ = read_model(os.path.join(self.FIXTURE_DIR, 'invalid.bngl2'), '')
        self.assertIn("not a valid BNGL or BGNL XML file", flatten_nested_list_of_strings(errors))

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid.bngl'))
        self.assertIn("XML file couldn't be generated", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'does-not-exist'))
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(None)
        self.assertIn('must be a path', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
