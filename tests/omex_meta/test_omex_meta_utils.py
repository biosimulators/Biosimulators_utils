from biosimulators_utils.omex_meta.data_model import OmexMetadataOutputFormat
from biosimulators_utils.omex_meta.utils import (
    build_omex_meta_file_for_model, _build_omex_meta_file_for_model, _build_omex_meta_file_for_model_error_wrapper,
    get_local_combine_archive_content_uri, get_global_combine_archive_content_uri)
import os
import shutil
import tempfile
import unittest


class OmexMetaUtilsTestCase(unittest.TestCase):
    FIXTURE_DIRNAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

    def setUp(self):
        self.temp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dirname)

    def test_build_omex_meta_file_for_model(self):
        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-metadata', 'demo1.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev

        build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

    def test_build_omex_meta_file_for_model_archive_uri(self):
        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-metadata', 'demo1.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        archive_uri = "demo1.omex"

        build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format, archive_uri=archive_uri)

    def test_build_omex_meta_file_for_model_error_handling(self):
        model_filename = 'not a file'
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        with self.assertRaisesRegex(FileNotFoundError, 'is not a file'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'BIOMD0000000075.xml')
        metadata_filename = os.path.join('not a directory', 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'BIOMD0000000075.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = None
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

    def test__build_omex_meta_file_for_model_error_handling(self):
        model_filename = os.path.join(self.temp_dirname, 'model.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        with open(model_filename, 'w') as file:
            file.write('<sbml></sbml')
        with self.assertRaisesRegex(ValueError, 'could not be extracted'):
            _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format.value)

        # model_filename = os.path.join(self.temp_dirname, 'model.xml')
        # metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        # metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        # with open(model_filename, 'w') as file:
        #     file.write('<sbml></sbml>')
        # with self.assertRaisesRegex(ValueError, 'could not be read'):
        #    _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format.value)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-metadata', 'simple-regulation.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format.value)

    def test__build_omex_meta_file_for_model_error_handling_wrapper(self):
        model_filename = os.path.join(self.temp_dirname, 'model.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        with open(model_filename, 'w') as file:
            file.write('<sbml></sbml')
        with self.assertRaisesRegex(SystemExit, 'could not be extracted'):
            _build_omex_meta_file_for_model_error_wrapper(model_filename, metadata_filename, metadata_format.value)

        # model_filename = os.path.join(self.temp_dirname, 'model.xml')
        # metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        # metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        # with open(model_filename, 'w') as file:
        #     file.write('<sbml></sbml>')
        # with self.assertRaisesRegex(SystemExit, 'could not be read'):
        #     _build_omex_meta_file_for_model_error_wrapper(model_filename, metadata_filename, metadata_format.value)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-metadata', 'simple-regulation.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        _build_omex_meta_file_for_model_error_wrapper(model_filename, metadata_filename, metadata_format.value)

    def test__build_omex_meta_file_for_model_error_handling_subprocess(self):
        model_filename = os.path.join(self.temp_dirname, 'model.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        with open(model_filename, 'w') as file:
            file.write('<sbml></sbml')
        with self.assertRaisesRegex(RuntimeError, 'could not be extracted'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.temp_dirname, 'model.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        with open(model_filename, 'w') as file:
            file.write('<sbml></sbml>')
        with self.assertRaisesRegex(RuntimeError, 'could not be read'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-metadata', 'simple-regulation.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetadataOutputFormat.rdfxml_abbrev
        build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

    def test_get_local_combine_archive_content_uri(self):
        self.assertEqual(
            get_local_combine_archive_content_uri('https://archives.org/archive.omex/thumb.png', 'https://archives.org/archive.omex'),
            ('./thumb.png', 'https://archives.org/archive.omex'))
        self.assertEqual(
            get_local_combine_archive_content_uri('https://archives.org/archive.omex/./thumb.png', 'https://archives.org/archive.omex'),
            ('./thumb.png', 'https://archives.org/archive.omex'))
        self.assertEqual(
            get_local_combine_archive_content_uri('https://archives.org/archive.omex', 'https://archives.org/archive.omex'),
            ('.', 'https://archives.org/archive.omex'))
        self.assertEqual(
            get_local_combine_archive_content_uri('thumb.png', 'https://archives.org/archive.omex'),
            ('thumb.png', None))
        self.assertEqual(
            get_local_combine_archive_content_uri('thumb.png'),
            ('thumb.png', None))

    def test_get_global_combine_archive_content_uri(self):
        self.assertEqual(
            get_global_combine_archive_content_uri('thumb.png', 'https://archives.org/archive.omex'),
            'https://archives.org/archive.omex/thumb.png')
        self.assertEqual(
            get_global_combine_archive_content_uri('./thumb.png', 'https://archives.org/archive.omex'),
            'https://archives.org/archive.omex/thumb.png'),
        self.assertEqual(
            get_global_combine_archive_content_uri('.', 'https://archives.org/archive.omex'),
            'https://archives.org/archive.omex'),
        self.assertEqual(
            get_global_combine_archive_content_uri('thumb.png'),
            'thumb.png')
