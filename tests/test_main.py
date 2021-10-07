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

    def test_validate_model(self):
        with biosimulators_utils.__main__.App(argv=[
            'validate-model',
            'SBML',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'BIOMD0000000297.xml'),
        ]) as app:
            app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-model',
                'SBML',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'does not exist'),
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'Model language must be'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-model',
                'invalid',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'BIOMD0000000297.xml'),
            ]) as app:
                app.run()

    def test_validate_simulation(self):
        with biosimulators_utils.__main__.App(argv=[
            'validate-simulation',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml', 'BIOMD0000000673_sim.sedml'),
        ]) as app:
            app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-simulation',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.sedml'),
        ]) as app:
            app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-simulation',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml',
                         'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint-invalid-model.sedml'),
        ]) as app:
            app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-simulation',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml',
                         'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint-invalid-target.sedml'),
        ]) as app:
            app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid.'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-simulation',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml',
                             'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint-invalid-xpath.sedml'),
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid.'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-simulation',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml', 'does not exist'),
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid.'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-simulation',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml', 'no-id.sedml'),
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid.'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-simulation',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml', 'duplicate-ids.sedml'),
            ]) as app:
                app.run()

        with self.assertRaisesRegex(ValueError, 'Big error'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-simulation',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'sedml', 'duplicate-ids.sedml'),
            ]) as app:
                with mock.patch.object(biosimulators_utils.sedml.io.SedmlSimulationReader, 'run', side_effect=ValueError('Big error')):
                    app.run()

    def test_validate_metadata(self):
        with biosimulators_utils.__main__.App(argv=[
            'validate-metadata',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'omex-metadata', 'biosimulations-abbrev.rdf'),
        ]) as app:
            with mock.patch.dict(os.environ, {'OMEX_METADATA_SCHEMA': 'BioSimulations'}):
                app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-metadata',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'omex-metadata', 'biosimulations-abbrev.rdf'),
        ]) as app:
            with mock.patch.dict(os.environ, {'OMEX_METADATA_SCHEMA': 'rdf_triples'}):
                app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-metadata',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'omex-metadata', 'malformed.rdf'),
            ]) as app:
                with mock.patch.dict(os.environ, {'OMEX_METADATA_SCHEMA': 'BioSimulations'}):
                    app.run()

        with self.assertRaisesRegex(SystemExit, 'is invalid'):
            with biosimulators_utils.__main__.App(argv=[
                'validate-metadata',
                os.path.join(os.path.dirname(__file__), 'fixtures', 'omex-metadata', 'missing-required.rdf'),
            ]) as app:
                with mock.patch.dict(os.environ, {'OMEX_METADATA_SCHEMA': 'BioSimulations'}):
                    app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-metadata',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'omex-metadata', 'missing-required.rdf'),
        ]) as app:
            with mock.patch.dict(os.environ, {'OMEX_METADATA_SCHEMA': 'rdf_triples'}):
                app.run()

    def test_validate_modeling_project(self):
        with biosimulators_utils.__main__.App(argv=[
            'validate-project',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with mock.patch('biosimulators_utils.combine.validation.validate', return_value=([], [])):
                    app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-project',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex'),
        ]) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                app.run()
                stdout = captured.stdout.get_text()
        self.assertRegex(stdout, 'Archive contains 1 SED-ML documents with 1 models')

        # warnings
        with biosimulators_utils.__main__.App(argv=[
            'validate-project',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[CombineArchiveContent(), CombineArchiveContent()])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with mock.patch('biosimulators_utils.combine.validation.validate', return_value=([['Bigger error']], [['Big warning']])):
                    with self.assertWarnsRegex(BioSimulatorsWarning, '- Big warning'):
                        with self.assertRaisesRegex(SystemExit, '- Bigger error'):
                            app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-project',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'mock-file'),
        ]) as app:
            archive = CombineArchive(contents=[])
            with mock.patch('biosimulators_utils.combine.io.CombineArchiveReader.run', return_value=archive):
                with self.assertRaisesRegex(SystemExit, 'must have at least one content element'):
                    with self.assertWarnsRegex(BioSimulatorsWarning, 'does not contain any SED-ML files'):
                        app.run()

        # error
        with biosimulators_utils.__main__.App(argv=[
            'validate-project',
            os.path.join(os.path.dirname(__file__), 'fixtures', 'not-a-file'),
        ]) as app:
            with self.assertRaisesRegex(SystemExit, 'is not a file'):
                app.run()

        with biosimulators_utils.__main__.App(argv=[
            'validate-project',
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

    def test_convert_escher_to_vega(self):
        escher_filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'escher', 'e_coli_core.Core metabolism.json')
        vega_filename = os.path.join(self.tmp_dir, 'viz.json')

        # data from SED-ML report
        data_url = 'http://site.com/flux.json'
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'escher-to-vega',
            '--data-sedml', 'simulation.sedml/report_1',
            escher_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        reaction_data_set = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
        self.assertEqual(reaction_data_set, {'name': 'reactionFluxes', 'sedmlUri': ['simulation.sedml', 'report_1']})

        # data from file
        data_filename = os.path.join(self.tmp_dir, 'fluxes.json')
        flux_values = dict_to_vega_dataset({
            'GND': 2.,
            'PGK': 10.,
        })
        with open(data_filename, 'w') as file:
            json.dump(flux_values, file)
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'escher-to-vega',
            '--data-file', data_filename,
            escher_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        reaction_data_set = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
        self.assertEqual(reaction_data_set, {'name': 'reactionFluxes', 'values': flux_values})

        # data at URL
        data_url = 'http://site.com/flux.json'
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'escher-to-vega',
            '--data-url', data_url,
            escher_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        reaction_data_set = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
        self.assertEqual(reaction_data_set, {'name': 'reactionFluxes', 'url': data_url})

    def test_convert_ginml_to_vega(self):
        ginml_filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'ginml', 'ginsim-35-regulatoryGraph.ginml')
        vega_filename = os.path.join(self.tmp_dir, 'viz.json')

        # data from SED-ML report
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'ginml-to-vega',
            '--data-sedml',
            ginml_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        data_set = next(data for data in vega['data'] if data['name'] == 'nodesValues')
        self.assertEqual(data_set, {'name': 'nodesValues', 'sedmlUri': []})

    def test_convert_sbgn_to_vega(self):
        sbgn_filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'sbgn', 'Repressilator_PD_v6_color-modified.sbgn')
        vega_filename = os.path.join(self.tmp_dir, 'viz.json')

        # data from SED-ML report
        with biosimulators_utils.__main__.App(argv=[
            'convert', 'sbgn-to-vega',
            '--data-sedml', 'simulation.sedml/report',
            sbgn_filename,
            vega_filename,
        ]) as app:
            app.run()

        with open(vega_filename, 'rb') as file:
            vega = json.load(file)
        data_set = next(data for data in vega['data'] if data['name'] == 'glyphsValues')
        self.assertEqual(data_set, {'name': 'glyphsValues', 'sedmlUri': ['simulation.sedml', 'report']})

    def test_convert_diagram_error_handling(self):
        with self.assertRaisesRegex(SystemExit, 'must be used'):
            with biosimulators_utils.__main__.App(argv=[
                'convert', 'escher-to-vega',
                'path/to/escher.json',
                'path/to/vg.json',
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'can be used'):
            with biosimulators_utils.__main__.App(argv=[
                'convert', 'escher-to-vega',
                '--data-file', 'path/to/flux.json',
                '--data-url', 'http://site.com/flux.json',
                'path/to/escher.json',
                'path/to/vg.json',
            ]) as app:
                app.run()

        with self.assertRaisesRegex(SystemExit, 'No such file or directory'):
            with biosimulators_utils.__main__.App(argv=[
                'convert', 'escher-to-vega',
                '--data-url', 'path/to/flux.json',
                'path/to/escher.json',
                'path/to/vg.json',
            ]) as app:
                app.run()
