from biosimulators_utils.sbml.validation import validate_model
import os
import unittest


class ValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

    def test(self):
        validate_model(os.path.join(self.FIXTURE_DIR, 'sbml-list-of-species.xml'))

        with self.assertRaisesRegex(ValueError, "species attribute 'id' is required"):
            validate_model(os.path.join(self.FIXTURE_DIR, 'sbml-invalid-model.xml'))
