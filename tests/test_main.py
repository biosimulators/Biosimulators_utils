from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent
from biosimulators_utils.viz.vega.utils import dict_to_vega_dataset
from biosimulators_utils.warnings import BioSimulatorsWarning
from unittest import mock
import biosimulators_utils
import biosimulators_utils.__main__
import capturer
import json
import os
import shutil
import tempfile
import unittest


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_help(self):
        with biosimulators_utils.__main__.App(argv=[]) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                app.run()
                stdout = captured.stdout.get_text()
                self.assertTrue(stdout.startswith('usage: biosimulators-utils'))
                self.assertEqual(captured.stderr.get_text(), '')

    def test_version(self):
        with biosimulators_utils.__main__.App(argv=['-v']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertEqual(stdout, biosimulators_utils.__version__)
                self.assertEqual(captured.stderr.get_text(), '')

        with biosimulators_utils.__main__.App(argv=['--version']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertEqual(stdout, biosimulators_utils.__version__)
                self.assertEqual(captured.stderr.get_text(), '')

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['', '--help']):
            with self.assertRaises(SystemExit) as context:
                biosimulators_utils.__main__.main()
                self.assertRegex(context.Exception, 'usage: biosimulators-utils')

    def test_build_modeling_project(self):
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')

        with biosimulators_utils.__main__.App(argv=[
            'build-project',
            'undefined',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'bngl', 'valid.bngl'),
            'UniformTimeCourse',
            archive_filename,
        ]) as app:
            with self.assertRaisesRegex(SystemExit, 'Model language must be'):
                app.run()

        with biosimulators_utils.__main__.App(argv=[
            'build-project',
            'BNGL',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'bngl', 'valid.bngl'),
            'undefined',
            archive_filename,
        ]) as app:
            with self.assertRaisesRegex(SystemExit, 'Simulation type must be'):
                app.run()

        with biosimulators_utils.__main__.App(argv=[
            'build-project',
            'BNGL',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'bngl', 'valid.bngl'),
            'UniformTimeCourse',
            archive_filename,
        ]) as app:
            app.run()
        self.assertTrue(os.path.isfile(archive_filename))

    def test_validate_modeling_project(self):
        with biosimulators_utils.__main__.App(argv=[
            'validate',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with mock.patch('biosimulators_utils.combine.validation.validate', return_value=([], [])):
                    app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex'),
        ]) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                app.run()
                stdout = captured.stdout.get_text()
        self.assertRegex(stdout, 'Archive contains 1 SED-ML documents with 1 models')

        # warnings
        with biosimulators_utils.__main__.App(argv=[
            'validate',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[CombineArchiveContent(), CombineArchiveContent()])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with mock.patch('biosimulators_utils.combine.validation.validate', return_value=([['Bigger error']], [['Big warning']])):
                    with self.assertWarnsRegex(BioSimulatorsWarning, '- Big warning'):
                        with self.assertRaisesRegex(SystemExit, '- Bigger error'):
                            app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with self.assertRaisesRegex(SystemExit, 'must have at least one content element'):
                    with self.assertWarnsRegex(BioSimulatorsWarning, 'does not contain any SED-ML files'):
                        app.run()

        # error
        with biosimulators_utils.__main__.App(argv=[
            'validate',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'not-a-file'),
        ]) as app:
            with self.assertRaisesRegex(SystemExit, 'is not a file'):
                app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[CombineArchiveContent(), CombineArchiveContent()])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with self.assertRaisesRegex(SystemExit, '- Content element must'):
                    app.run()

    def test_exec_modeling_project(self):
        with biosimulators_utils.__main__.App(argv=[
            'exec',
            'ghcr.io/biosimulators/copasi:latest',
            '-i', os.path.join(os.path.dirname(__file__), 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex'),
            '-o', os.path.join(self.tmp_dir, 'results'),
            '--env', 'KEY1=value1', 'KEY2=value2',
            '--user', str(os.getuid()),
        ]) as app:
            app.run()

        outputs = os.listdir(os.path.join(self.tmp_dir, 'results'))
        self.assertIn('reports.h5', outputs)

    def test_exec_modeling_project_error_handling(self):
        with self.assertRaisesRegex(SystemExit, 'must be pairs of keys and values'):
            with biosimulators_utils.__main__.App(argv=[
                'exec',
                'ghcr.io/biosimulators/tellurium:latest',
                '-i', os.path.join(os.path.dirname(__file__), 'fixtures', 'BIOMD0000000297.omex'),
                '-o', os.path.join(self.tmp_dir, 'results'),
                '--env', 'KEY1:value1', 'KEY2-value2',
                '--user', str(os.getuid()),
            ]) as app:
                app.run()

    def test_convert_help(self):
        with biosimulators_utils.__main__.App(argv=['convert']) as app:
            app.run()

    def test_convert_escher(self):
        escher_filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'escher', 'e_coli_core.Core metabolism.json')
        vega_filename = os.path.join(self.tmp_dir, 'viz.json')

        # data from SED-ML report
        flux_url = 'http://site.com/flux.json'
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'escher-to-vega',
            '--flux-sedml-report', 'simulation.sedml/report_1',
            escher_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        reaction_data_set = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
        self.assertEqual(reaction_data_set, {'name': 'reactionFluxes', 'sedmlUri': ['simulation.sedml', 'report_1']})

        # data from file
        flux_filename = os.path.join(self.tmp_dir, 'fluxes.json')
        flux_values = dict_to_vega_dataset({
            'GND': 2.,
            'PGK': 10.,
        })
        with open(flux_filename, 'w') as file:
            json.dump(flux_values, file)
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'escher-to-vega',
            '--flux-file', flux_filename,
            escher_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        reaction_data_set = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
        self.assertEqual(reaction_data_set, {'name': 'reactionFluxes', 'values': flux_values})

        # data at URL
        flux_url = 'http://site.com/flux.json'
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'escher-to-vega',
            '--flux-url', flux_url,
            escher_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        reaction_data_set = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
        self.assertEqual(reaction_data_set, {'name': 'reactionFluxes', 'url': flux_url})

    def test_convert_escher_error_handling(self):
        with self.assertRaisesRegex(SystemExit, 'must be used'):
            with biosimulators_utils.__main__.App(argv=[
                'convert', 'escher-to-vega',
                'path/to/escher.json',
                'path/to/vega.json',
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'can be used'):
            with biosimulators_utils.__main__.App(argv=[
                'convert', 'escher-to-vega',
                '--flux-file', 'path/to/flux.json',
                '--flux-url', 'http://site.com/flux.json',
                'path/to/escher.json',
                'path/to/vega.json',
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'No such file or directory'):
            with biosimulators_utils.__main__.App(argv=[
                'convert', 'escher-to-vega',
                '--flux-url', 'path/to/flux.json',
                'path/to/escher.json',
                'path/to/vega.json',
            ]) as app:
                app.run()
