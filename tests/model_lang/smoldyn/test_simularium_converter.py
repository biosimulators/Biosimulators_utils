import unittest
import os
import shutil
import tempfile
from biosimulators_utils.model_lang.smoldyn.simularium_converter import SmoldynCombineArchive, SmoldynDataConverter


class TestSimulariumConverter(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to simulate a combine archive
        self.temp_dir = tempfile.mkdtemp()
        # Create a dummy Smoldyn model.txt file in the temporary directory
        self.dummy_smoldyn_model_file = os.path.join(self.temp_dir, "model.txt")
        with open(self.dummy_smoldyn_model_file, 'w') as f:
            f.write("test content")
        # Create a dummy manifest file in the temporary directory
        self.dummy_manifest_file = os.path.join(self.temp_dir, "manifest.xml")
        with open(self.dummy_manifest_file, 'w') as f:
            f.write("<smoldyn>dummy manifest content</smoldyn>")

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.temp_dir)

    def test_smoldyn_combine_archive(self):
        # Initialize SmoldynCombineArchive with the temporary directory
        archive = SmoldynCombineArchive(rootpath=self.temp_dir)

        # Test the paths attribute
        self.assertIn("root", archive.paths)
        self.assertIn("model.txt", archive.paths)
        self.assertIn("manifest.xml", archive.paths)

        # Test the model_path setter/getter
        self.assertEqual(archive.set_model_filepath(), self.dummy_smoldyn_model_file)

        # Test manifest file path getter
        self.assertEqual(archive.get_manifest_filepath(), self.dummy_manifest_file)

    def test_smoldyn_data_converter(self):
        # Initialize SmoldynCombineArchive and SmoldynDataConverter with the temporary directory
        archive = SmoldynCombineArchive(rootpath=self.temp_dir)
        converter = SmoldynDataConverter(archive=archive)

        # Test reading a model output dataframe
        output_df = converter.read_model_output_dataframe()
        self.assertEqual(output_df.columns.tolist(), ['mol_name', 'x', 'y', 'z', 't'])

        # Verify smoldyn in manifest
        self.assertTrue(converter.verify_smoldyn_in_manifest())
        # Further tests for other methods can be added here
