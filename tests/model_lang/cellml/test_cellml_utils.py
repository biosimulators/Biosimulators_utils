from biosimulators_utils.model_lang.cellml.utils import get_parameters_variables_for_simulation
from biosimulators_utils.sedml.data_model import (ModelLanguage, SteadyStateSimulation,
                                                  OneStepSimulation, UniformTimeCourseSimulation, Symbol,
                                                  ModelAttributeChange, Variable)
from unittest import mock
import os
import unittest


class CellmlUtilsTestCase(unittest.TestCase):
    V1_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'cellml', 'albrecht_colegrove_friel_2002.xml')
    V2_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'cellml', 'version2.xml')
    INVALID_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'cellml', 'invalid_namespace.xml')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'is not a path to a model file'):
            get_parameters_variables_for_simulation(None, None, None, None)

        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            get_parameters_variables_for_simulation('not a file', None, None, None)

        with self.assertRaisesRegex(ValueError, 'not a valid CellML file'):
            get_parameters_variables_for_simulation(self.INVALID_FIXTURE_FILENAME, None, None, None)

    def test_get_parameters_variables_for_simulation_version_1(self):
        params, vars = get_parameters_variables_for_simulation(self.V1_FIXTURE_FILENAME, None, None, None)

        self.assertEqual(len(params), 13)
        self.assertEqual(len(vars), 54)

        namespaces = {
            'cellml': 'http://www.cellml.org/cellml/1.0#',
        }

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='initial_value_component_total_cytoplasmic_Ca_flux_variable_F',
            name='Initial value of variable "F" of component "total_cytoplasmic_Ca_flux"',
            target=(
                "/cellml:model"
                "/cellml:component[@name='total_cytoplasmic_Ca_flux']"
                "/cellml:variable[@name='F']"
                "/@initial_value"
            ),
            target_namespaces=namespaces,
            new_value='96.5',
        )))

        self.assertTrue(vars[0].is_equal(Variable(
            id='value_component_environment_variable_time',
            name='Value of variable "time" of component "environment"',
            target=(
                "/cellml:model"
                "/cellml:component[@name='environment']"
                "/cellml:variable[@name='time']"
            ),
            target_namespaces=namespaces,
        )))

    def test_get_parameters_variables_for_simulation_version_2(self):
        params, vars = get_parameters_variables_for_simulation(self.V2_FIXTURE_FILENAME, None, None, None)

        self.assertEqual(len(params), 1)
        self.assertEqual(len(vars), 3)

        namespaces = {
            'cellml': 'http://www.cellml.org/cellml/2.0#',
        }

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='initial_value_component_level2_component_variable_cosine',
            name='Initial value of variable "cosine" of component "level2_component"',
            target=(
                "/cellml:model"
                "/cellml:component[@name='level2_component']"
                "/cellml:variable[@name='cosine']"
                "/@initial_value"
            ),
            target_namespaces=namespaces,
            new_value='0',
        )))

        self.assertTrue(vars[0].is_equal(Variable(
            id='value_component_level2_component_variable_time',
            name='Value of variable "time" of component "level2_component"',
            target=(
                "/cellml:model"
                "/cellml:component[@name='level2_component']"
                "/cellml:variable[@name='time']"
            ),
            target_namespaces=namespaces,
        )))