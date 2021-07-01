from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveReader
from biosimulators_utils.combine.validation import validate, validate_format, validate_content, validate_omex_meta_file
from biosimulators_utils.sedml.io import SedmlSimulationReader
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import copy
import csv
import os
import shutil
import tempfile
import unittest


class ValidationTestCase(unittest.TestCase):
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
    OMEX_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex')
    OMEX_META_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta')

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        shutil.copyfile(
            os.path.join(self.FIXTURES_DIR, 'images', 'PNG_transparency_demonstration_1.png'),
            os.path.join(self.tmp_dir, 'thumbnail.png'))

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_validate_format(self):
        self.assertEqual(validate_format('http://purl.org/NET/mediatypes/text/plain'), [])
        self.assertEqual(validate_format('http://purl.org/NET/mediatypes/application/pdf'), [])

        for format in CombineArchiveContentFormat.__members__.values():
            self.assertEqual(validate_format(format), [])

        filename = os.path.join(os.path.join(self.FIXTURES_DIR, 'combine-formats.csv'))
        with open(filename, newline='') as file:
            reader = csv.DictReader(file, dialect='excel')
            for format in reader:
                url = 'http://identifiers.org/combine.specifications/' + format['Identifier (in the combine.specifications collection)']
                self.assertEqual(validate_format(url), [])

        self.assertNotEqual(validate_format('text/plain'), [])
        self.assertNotEqual(validate_format('sbml'), [])

    def test_validate_content(self):
        fixtures_dir = os.path.join(self.FIXTURES_DIR, 'images')
        formats_to_validate = list(CombineArchiveContentFormat.__members__.values())

        content = CombineArchiveContent(
            location='all_gray.bmp',
            format=CombineArchiveContentFormat.BMP.value,
        )
        self.assertEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))
        content.format = CombineArchiveContentFormat.GIF.value
        self.assertNotEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))

        content = CombineArchiveContent(
            location='Rotating_earth_(large).gif',
            format=CombineArchiveContentFormat.GIF.value,
        )
        self.assertEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))
        content.format = CombineArchiveContentFormat.BMP.value
        self.assertNotEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))

        content = CombineArchiveContent(
            location='Jpegvergroessert.jpg',
            format=CombineArchiveContentFormat.JPEG.value,
        )
        self.assertEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))
        content.format = CombineArchiveContentFormat.GIF.value
        self.assertNotEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))

        content = CombineArchiveContent(
            location='PNG_transparency_demonstration_1.png',
            format=CombineArchiveContentFormat.PNG.value,
        )
        self.assertEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))
        content.format = CombineArchiveContentFormat.GIF.value
        self.assertNotEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))

        content = CombineArchiveContent(
            location='Tif.tif',
            format=CombineArchiveContentFormat.TIFF.value,
        )
        self.assertEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))
        content.format = CombineArchiveContentFormat.GIF.value
        self.assertNotEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))

        content = CombineArchiveContent(
            location='Johnrogershousemay2020.webp',
            format=CombineArchiveContentFormat.WEBP.value,
        )
        self.assertEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))
        content.format = CombineArchiveContentFormat.GIF.value
        self.assertNotEqual(validate_content(content, fixtures_dir, formats_to_validate=formats_to_validate), ([], []))

    def test_validate_omex_meta_file(self):
        errors, warnings = validate_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'libcombine.rdf'),
                                                   archive_dirname=self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings = validate_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'biosimulations.rdf'),
                                                   archive_dirname=self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        errors, warnings = validate_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'warning.rdf'),
                                                   archive_dirname=self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertIn("Unsupported version '1.1'", flatten_nested_list_of_strings(warnings))

        errors, warnings = validate_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'invalid.rdf'),
                                                   archive_dirname=self.tmp_dir)
        self.assertEqual(len(errors), 1)
        self.assertIn("has multiple object node elements", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        errors, warnings = validate_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'malformed.rdf'),
                                                   archive_dirname=self.tmp_dir)
        self.assertEqual(len(errors), 3)
        self.assertIn("Opening and ending tag mismatch", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_validate(self):
        os.remove(os.path.join(self.tmp_dir, 'thumbnail.png'))

        archive = CombineArchiveReader().run(self.OMEX_FIXTURE, self.tmp_dir)
        errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertNotEqual(warnings, [])

        archive2 = copy.deepcopy(archive)
        for content in archive.contents:
            archive2.contents.append(content)
        errors, warnings = validate(archive2, self.tmp_dir)
        self.assertIn('contains repeated content items', flatten_nested_list_of_strings(errors))

        archive2 = copy.deepcopy(archive)
        archive2.contents = []
        errors, warnings = validate(archive2, self.tmp_dir)
        self.assertIn('does not contain content items', flatten_nested_list_of_strings(errors))

    def test_error_handling(self):
        os.remove(os.path.join(self.tmp_dir, 'thumbnail.png'))

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
