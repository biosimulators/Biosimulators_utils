from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveReader
from biosimulators_utils.combine.validation import validate
from biosimulators_utils.sedml.io import SedmlSimulationReader
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import os
import shutil
import tempfile
import unittest


class ValidationTestCase(unittest.TestCase):
    FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex')

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_validate(self):
        archive = CombineArchiveReader().run(self.FIXTURE, self.tmp_dir)
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_error_handling(self):
        archive = CombineArchive()
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(errors[0]), 1)
        self.assertIn('must have at least one content element', errors[0][0])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(len(warnings[0]), 1)
        self.assertIn('does not contain any SED-ML files', warnings[0][0])

        archive = CombineArchive(contents=[
            None,
        ])
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(warnings), 1)
        self.assertIn('must be an instance of', flatten_nested_list_of_strings(errors))
        self.assertIn('does not contain any SED-ML files', flatten_nested_list_of_strings(warnings))

        archive = CombineArchive(contents=[
            CombineArchiveContent(),
        ])
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(warnings), 1)
        self.assertIn('must have a location', flatten_nested_list_of_strings(errors))
        self.assertIn('must have a format', flatten_nested_list_of_strings(errors))
        self.assertIn('does not contain any SED-ML files', flatten_nested_list_of_strings(warnings))

        archive = CombineArchive(contents=[
            CombineArchiveContent(
                location='plain.txt',
                format='plain/text',
            ),
        ])
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(warnings), 1)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertIn('does not contain any SED-ML files', flatten_nested_list_of_strings(warnings))

        with open(os.path.join(self.tmp_dir, 'sim.sedml'), 'w') as file:
            pass

        archive = CombineArchive(contents=[
            CombineArchiveContent(
                location='sim.sedml',
                format=CombineArchiveContentFormat.SED_ML,
            ),
        ])
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(len(errors), 1)
        self.assertEqual(warnings, [])
        self.assertIn('is invalid', flatten_nested_list_of_strings(errors))

        archive = CombineArchive(contents=[
            CombineArchiveContent(
                location='sim.sedml',
                format=CombineArchiveContentFormat.SED_ML,
            ),
        ])
        with mock.patch.object(SedmlSimulationReader, 'run', side_effect=ValueError('other error')):
            with self.assertRaisesRegex(ValueError, 'other error'):
                validate(archive, self.tmp_dir)

        def side_effect(self, filename, validate_models_with_languages=False):
            self.warnings = [['my warning']]
        with mock.patch.object(SedmlSimulationReader, 'run', side_effect):
            errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn('may be invalid', flatten_nested_list_of_strings(warnings))
        self.assertIn('my warning', flatten_nested_list_of_strings(warnings))
