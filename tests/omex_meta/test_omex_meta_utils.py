from biosimulators_utils.omex_meta.data_model import OmexMetaOutputFormat
from biosimulators_utils.omex_meta.utils import build_omex_meta_file_for_model, _build_omex_meta_file_for_model
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
        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-meta', 'demo1.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetaOutputFormat.rdfxml_abbrev

        _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format.value)

        build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

    def test_build_omex_meta_file_for_model_error_handling(self):
        model_filename = 'not a file'
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetaOutputFormat.rdfxml_abbrev
        with self.assertRaisesRegex(FileNotFoundError, 'is not a file'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'BIOMD0000000075.xml')
        metadata_filename = os.path.join('not a directory', 'metadata.rdf')
        metadata_format = OmexMetaOutputFormat.rdfxml_abbrev
        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'BIOMD0000000075.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = None
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)

        model_filename = os.path.join(self.temp_dirname, 'model.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetaOutputFormat.rdfxml_abbrev
        with open(model_filename, 'w') as file:
            file.write('<sbml></sbml')
        with self.assertRaisesRegex(RuntimeError, 'could not be generated'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)
        with self.assertRaisesRegex(RuntimeError, 'could not be read'):
            _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format.value)

        model_filename = os.path.join(self.FIXTURE_DIRNAME, 'omex-meta', 'simple-regulation.xml')
        metadata_filename = os.path.join(self.temp_dirname, 'metadata.rdf')
        metadata_format = OmexMetaOutputFormat.rdfxml_abbrev
        with self.assertRaisesRegex(RuntimeError, 'could not be generated'):
            build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format)
