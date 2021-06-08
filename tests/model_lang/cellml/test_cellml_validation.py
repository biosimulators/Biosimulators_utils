from biosimulators_utils.model_lang.cellml.validation import validate_model
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import os
import unittest


class CellMlValidationTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'cellml')

    def test(self):
        # 1 model
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'albrecht_colegrove_friel_2002.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'albrecht_colegrove_friel_2002-error.xml'))
        self.assertIn("has extra content: units2", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # 1.1 model
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'parameters-1.1.cellml'))
        self.assertEqual(errors, [])
        self.assertIn("not available for CellML 1.1", flatten_nested_list_of_strings(warnings))

        # 2.0 model
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'version2.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'version2-with-imports.xml'))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'version2-missing-imports.xml'))
        self.assertIn("the file could not be opened", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # 2.0 error: invalid namespace
        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid_namespace.xml'))
        self.assertIn("default namespace must be", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'not_a_path.xml'))
        self.assertIn("is not a file", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid_cellml_2.0.xml'))
        self.assertIn("Start tag expected", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        return_value = mock.Mock(
            getroot=lambda: mock.Mock(
                nsmap=mock.Mock(
                    get=lambda x, y: 'http://www.cellml.org/cellml/2.0#'
                )
            )
        )
        with mock.patch('lxml.etree.parse', return_value=return_value):
            errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'invalid_cellml_2.0.xml'))
            self.assertIn("Start tag expected", flatten_nested_list_of_strings(errors))
            self.assertEqual(warnings, [])

        errors, warnings, _ = validate_model(os.path.join(self.FIXTURE_DIR, 'missing-attribute.xml'))
        self.assertIn("does not have a valid name attribute", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
