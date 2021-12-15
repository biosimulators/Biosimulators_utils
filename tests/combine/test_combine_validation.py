from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveReader
from biosimulators_utils.combine.validation import validate, validate_format, validate_content
from biosimulators_utils.config import Config
from biosimulators_utils.omex_meta.data_model import OmexMetadataSchema
from biosimulators_utils.omex_meta.io import read_omex_meta_file
from biosimulators_utils.sedml.data_model import SedDocument, Model, ModelLanguage
from biosimulators_utils.sedml.io import SedmlSimulationReader, SedmlSimulationWriter
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
    OMEX_META_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-metadata')

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
        config = Config(OMEX_METADATA_SCHEMA=OmexMetadataSchema.rdf_triples)

        _, errors, warnings = read_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'libcombine.rdf'),
                                                  working_dir=self.tmp_dir, config=config)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        _, errors, warnings = read_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'biosimulations.rdf'),
                                                  working_dir=self.tmp_dir, config=config)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        _, errors, warnings = read_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'warning.rdf'),
                                                  working_dir=self.tmp_dir, config=config)
        self.assertIn("Unsupported version '1.2'", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        _, errors, warnings = read_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'invalid.rdf'),
                                                  working_dir=self.tmp_dir, config=config)
        self.assertEqual(len(errors), 4)
        self.assertIn("XML parser error", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        _, errors, warnings = read_omex_meta_file(os.path.join(self.OMEX_META_FIXTURES_DIR, 'malformed.rdf'),
                                                  working_dir=self.tmp_dir, config=config)
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

        def side_effect(self, filename, validate_models_with_languages=False, config=None):
            self.warnings = [['my warning']]
        with mock.patch.object(SedmlSimulationReader, 'run', side_effect):
            errors, warnings = validate(archive, self.tmp_dir)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn('may be invalid', flatten_nested_list_of_strings(warnings))
        self.assertIn('my warning', flatten_nested_list_of_strings(warnings))

    def test_manifest_in_manifest(self):
        out_dir = os.path.join(self.tmp_dir, 'out')
        archive = CombineArchiveReader().run(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'manifest-in-manifest.omex'), out_dir)
        errors, warnings = validate(archive, out_dir)
        self.assertEqual(errors, [])
        self.assertIn('manifests should not contain content entries for themselves', flatten_nested_list_of_strings(warnings))

        out_dir = os.path.join(self.tmp_dir, 'out')
        archive = CombineArchiveReader().run(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'multiple-manifests.omex'), out_dir)
        errors, warnings = validate(archive, out_dir)
        self.assertEqual(errors, [])
        self.assertIn('manifests should not contain content entries for themselves', flatten_nested_list_of_strings(warnings))

    def test_no_validation(self):
        archive_dirname = os.path.join(self.tmp_dir, 'archive')
        os.mkdir(archive_dirname)

        # OMEX manifests
        archive = CombineArchive()

        errors, warnings = validate(archive, archive_dirname)
        self.assertIn('must have at least one content', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        with mock.patch.dict('os.environ', {'VALIDATE_OMEX_MANIFESTS': '0'}):
            errors, warnings = validate(archive, archive_dirname)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        # SED-ML
        archive = CombineArchive()
        archive.contents.append(CombineArchiveContent(
            location='simulation.sedml',
            format=CombineArchiveContentFormat.SED_ML.value,
        ))

        sedml_filename = os.path.join(archive_dirname, 'simulation.sedml')
        with open(sedml_filename, 'w') as file:
            file.write('invalid')

        errors, warnings = validate(archive, archive_dirname)
        self.assertIn('Missing XML declaration', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        with mock.patch.dict('os.environ', {
            'VALIDATE_OMEX_MANIFESTS': '0',
            'VALIDATE_SEDML': '0',
        }):
            errors, warnings = validate(archive, archive_dirname)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        os.remove(sedml_filename)

        # models
        archive = CombineArchive()
        archive.contents.append(CombineArchiveContent(
            location='simulation.sedml',
            format=CombineArchiveContentFormat.SED_ML.value,
        ))

        model_filename = os.path.join(archive_dirname, 'model.xml')
        shutil.copyfile(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml'), model_filename)

        sed_doc = SedDocument()
        sed_doc.models.append(Model(id='model', source=model_filename, language=ModelLanguage.SBML.value))

        sedml_filename = os.path.join(archive_dirname, 'simulation.sedml')
        SedmlSimulationWriter().run(sed_doc, sedml_filename)

        with open(model_filename, 'w') as file:
            file.write('invalid')

        errors, warnings = validate(archive, archive_dirname)
        self.assertIn('Missing XML declaration', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        with mock.patch.dict('os.environ', {
            'VALIDATE_OMEX_MANIFESTS': '0',
            'VALIDATE_SEDML_MODELS': '0',
        }):
            errors, warnings = validate(archive, archive_dirname)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        os.remove(sedml_filename)
        os.remove(model_filename)

        # images
        archive = CombineArchive()
        archive.contents.append(CombineArchiveContent(
            location='image.png',
            format=CombineArchiveContentFormat.PNG.value,
        ))

        errors, warnings = validate(archive, archive_dirname, formats_to_validate=[CombineArchiveContentFormat.PNG])
        self.assertIn('The PNG file at location `image.png` is invalid.', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        with mock.patch.dict('os.environ', {
            'VALIDATE_OMEX_MANIFESTS': '0',
            'VALIDATE_IMAGES': '0',
        }):
            errors, warnings = validate(archive, archive_dirname, formats_to_validate=[CombineArchiveContentFormat.PNG])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        # OMEX metadata
        archive = CombineArchive()
        archive.contents.append(CombineArchiveContent(
            location='metadata.rdf',
            format=CombineArchiveContentFormat.OMEX_METADATA.value,
        ))

        metadata_file = os.path.join(archive_dirname, 'metadata.rdf')
        shutil.copyfile(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-metadata', 'invalid.rdf'), metadata_file)

        errors, warnings = validate(archive, archive_dirname, formats_to_validate=[CombineArchiveContentFormat.OMEX_METADATA])
        self.assertIn('The OMEX Metadata file at location `metadata.rdf` is invalid.', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        with mock.patch.dict('os.environ', {
            'VALIDATE_OMEX_MANIFESTS': '0',
            'VALIDATE_OMEX_METADATA': '0',
        }):
            errors, warnings = validate(archive, archive_dirname, formats_to_validate=[CombineArchiveContentFormat.OMEX_METADATA])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        os.remove(metadata_file)

    def test_validate_no_metadata(self):
        os.remove(os.path.join(self.tmp_dir, 'thumbnail.png'))

        config = Config(VALIDATE_OMEX_METADATA=True)
        archive = CombineArchiveReader().run(os.path.join(self.FIXTURES_DIR, 'no-metadata.omex'), self.tmp_dir, config=config)
        errors, warnings = validate(archive, self.tmp_dir, config=config)
        self.assertEqual(errors, [])

        config = Config(VALIDATE_OMEX_METADATA=False)
        archive = CombineArchiveReader().run(os.path.join(self.FIXTURES_DIR, 'no-metadata.omex'), self.tmp_dir, config=config)
        errors, warnings = validate(archive, self.tmp_dir, config=config)
        self.assertEqual(errors, [])

        config = Config(VALIDATE_OMEX_METADATA=True)
        archive = CombineArchiveReader().run(os.path.join(self.FIXTURES_DIR, 'no-metadata.omex'), self.tmp_dir, config=config)
        errors, warnings = validate(archive, self.tmp_dir, formats_to_validate=list(
            CombineArchiveContentFormat.__members__.values()), config=config)
        self.assertNotEqual(errors, [])

        config = Config(VALIDATE_OMEX_METADATA=False)
        archive = CombineArchiveReader().run(os.path.join(self.FIXTURES_DIR, 'no-metadata.omex'), self.tmp_dir, config=config)
        errors, warnings = validate(archive, self.tmp_dir, formats_to_validate=list(
            CombineArchiveContentFormat.__members__.values()), config=config)
        self.assertEqual(errors, [])
