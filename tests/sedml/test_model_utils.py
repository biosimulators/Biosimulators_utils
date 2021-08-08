from biosimulators_utils.combine.io import CombineArchiveReader
from biosimulators_utils.sedml import model_utils
from biosimulators_utils.sedml.data_model import ModelLanguage, Variable, Symbol, UniformTimeCourseSimulation, ModelAttributeChange
from biosimulators_utils.sedml.exceptions import UnsupportedModelLanguageError
from biosimulators_utils.sedml.io import SedmlSimulationReader
from unittest import mock
import os
import unittest
import shutil
import tempfile


class ModelUtilsTestCase(unittest.TestCase):
    FIXTURES_DIRNAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

    def setUp(self):
        self.dir_name = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_name)

    def test_get_parameters_variables_for_simulation(self):
        # BNGL
        filename = os.path.join(self.FIXTURES_DIRNAME, 'bngl', 'valid.bngl')
        params, sims, vars = model_utils.get_parameters_variables_for_simulation(
            filename, ModelLanguage.BNGL, UniformTimeCourseSimulation, None)
        self.assertTrue(vars[0].is_equal(Variable(
            id='time',
            name='Time',
            symbol=Symbol.time.value,
        )))

        # CellML
        filename = os.path.join(self.FIXTURES_DIRNAME, 'cellml', 'albrecht_colegrove_friel_2002.xml')
        params, sims, vars = model_utils.get_parameters_variables_for_simulation(
            filename, ModelLanguage.CellML, UniformTimeCourseSimulation, None)
        self.assertTrue(vars[0].is_equal(Variable(
            id='value_component_environment_variable_time',
            name='Value of variable "time" of component "environment"',
            target=(
                "/cellml:model"
                "/cellml:component[@name='environment']"
                "/cellml:variable[@name='time']"
            ),
            target_namespaces={'cellml': 'http://www.cellml.org/cellml/1.0#'},
        )))

        # SBML
        filename = os.path.join(self.FIXTURES_DIRNAME, 'BIOMD0000000297.xml')
        params, sims, vars = model_utils.get_parameters_variables_for_simulation(
            filename, ModelLanguage.SBML, UniformTimeCourseSimulation, 'KISAO_0000019')
        self.assertTrue(vars[0].is_equal(Variable(
            id='time',
            name='Time',
            symbol=Symbol.time.value,
        )))

        # Smoldyn
        filename = os.path.join(self.FIXTURES_DIRNAME, 'smoldyn', 'bounce1.txt')
        params, sims, vars = model_utils.get_parameters_variables_for_simulation(
            filename, ModelLanguage.Smoldyn, UniformTimeCourseSimulation, None)
        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='number_dimensions',
            name='Number of dimensions',
            target='dim',
            new_value='1',
        )))

        # XPP
        filename = os.path.join(self.FIXTURES_DIRNAME, 'xpp', 'wilson-cowan.ode')
        params, sims, vars = model_utils.get_parameters_variables_for_simulation(
            filename, ModelLanguage.XPP, UniformTimeCourseSimulation, None)
        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='parameter_aee',
            name='Value of parameter "aee"',
            target='parameters.aee',
            new_value='10.0',
        )))

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaisesRegex(UnsupportedModelLanguageError, 'are not supported'):
            model_utils.get_parameters_variables_for_simulation(None, 'not implemented', None, None)

    def test_build_combine_archive_for_model(self):
        model_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'smoldyn', 'bounce1.txt')
        archive_filename = os.path.join(self.dir_name, 'archive.omex')

        model_utils.build_combine_archive_for_model(
            model_filename,
            ModelLanguage.Smoldyn,
            UniformTimeCourseSimulation,
            archive_filename,
        )

        archive_dirname = os.path.join(self.dir_name, 'archive')
        archive = CombineArchiveReader().run(archive_filename, archive_dirname)

        doc = SedmlSimulationReader().run(os.path.join(archive_dirname, 'simulation.sedml'))
        sim = doc.simulations[0]
        self.assertEqual(sim.initial_time, 0.)
        self.assertEqual(sim.output_start_time, 0.)
        self.assertEqual(sim.output_end_time, 100.)
        self.assertEqual(sim.number_of_steps, 10000)
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000057')
