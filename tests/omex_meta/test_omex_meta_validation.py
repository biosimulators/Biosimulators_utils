from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.omex_meta import data_model
from biosimulators_utils.omex_meta.io import read_omex_meta_file
from biosimulators_utils.omex_meta.validation import validate_biosimulations_metadata
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import copy
import os
import shutil
import tempfile
import unittest


class OmexMetaValidationTestCase(unittest.TestCase):
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
    FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta', 'biosimulations.rdf')

    def setUp(self):
        self.dir_name = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_name)

    def test_validate_biosimulations_metadata(self):
        md, _, _ = read_omex_meta_file(self.FIXTURE, schema=data_model.OmexMetaSchema.biosimulations)
        md = md[0]

        with mock.patch('requests.get', return_value=mock.Mock(status_code=200)):
            errors, warnings = validate_biosimulations_metadata(md)
            self.assertEqual(errors, [])
            self.assertIn('thumbnails could not be validated', flatten_nested_list_of_strings(warnings))

            errors, warnings = validate_biosimulations_metadata(md, working_dir=self.dir_name)
            self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
            self.assertEqual(warnings, [])

            shutil.copyfile(
                os.path.join(self.FIXTURES_DIR, 'images', 'PNG_transparency_demonstration_1.png'),
                os.path.join(self.dir_name, 'thumbnail.png'))
            errors, warnings = validate_biosimulations_metadata(md, working_dir=self.dir_name)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

            shutil.copyfile(
                os.path.join(self.FIXTURES_DIR, 'images', 'PNG_transparency_demonstration_1.png'),
                os.path.join(self.dir_name, 'thumbnail.png'))
            archive = CombineArchive(
                contents=[
                    CombineArchiveContent(
                        location='thumbnail.png',
                        format=CombineArchiveContentFormat.PNG.value,
                    ),
                ]
            )
            errors, warnings = validate_biosimulations_metadata(md, archive=archive, working_dir=self.dir_name)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

            archive.contents[0].format = CombineArchiveContentFormat.PDF.value
            errors, warnings = validate_biosimulations_metadata(md, archive=archive, working_dir=self.dir_name)
            self.assertNotEqual(errors, [])
            self.assertEqual(warnings, [])

            md2 = copy.deepcopy(md)
            md2['title'] = None
            errors, warnings = validate_biosimulations_metadata(md2, working_dir=self.dir_name)
            self.assertIn('is required', flatten_nested_list_of_strings(errors))
            self.assertEqual(warnings, [])

            md2 = copy.deepcopy(md)
            md2['creators'][0]['uri'] = 'xyz'
            errors, warnings = validate_biosimulations_metadata(md2, working_dir=self.dir_name)
            self.assertIn('is not a valid URL', flatten_nested_list_of_strings(errors))
            self.assertEqual(warnings, [])

            md2 = copy.deepcopy(md)
            md2['created'] = 'xyz'
            errors, warnings = validate_biosimulations_metadata(md2, working_dir=self.dir_name)
            self.assertIn('is not a valid date', flatten_nested_list_of_strings(errors))
            self.assertEqual(warnings, [])

            md2 = copy.deepcopy(md)
            md2['modified'].append('xyz')
            errors, warnings = validate_biosimulations_metadata(md2, working_dir=self.dir_name)
            self.assertIn('is not a valid date', flatten_nested_list_of_strings(errors))
            self.assertEqual(warnings, [])

        md2 = copy.deepcopy(md)
        md2['creators'][0]['uri'] = 'https://identifiers.org/not-a-namespace:invalid'
        with mock.patch('requests.get', return_value=mock.Mock(status_code=400)):
            errors, warnings = validate_biosimulations_metadata(md2, working_dir=self.dir_name)
        self.assertIn('is not a valid identifier', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        md2 = copy.deepcopy(md)
        md2['creators'][0]['uri'] = 'https://identifiers.org/not-a-namespace:invalid'
        with mock.patch('requests.get', return_value=mock.Mock(status_code=500, ok=False)):
            errors, warnings = validate_biosimulations_metadata(md2, working_dir=self.dir_name)
        self.assertEqual(errors, [])
        self.assertIn('could not be validated', flatten_nested_list_of_strings(warnings))
