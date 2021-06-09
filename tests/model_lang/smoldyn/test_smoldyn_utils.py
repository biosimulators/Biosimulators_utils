from biosimulators_utils.model_lang.smoldyn.utils import get_parameters_variables_for_simulation, _parse_configuration_line
from biosimulators_utils.sedml.data_model import Symbol, ModelAttributeChange, Variable
from unittest import mock
import os
import unittest


try:
    import smoldyn.biosimulators
    smoldyn_biosimulators = True
except ModuleNotFoundError:
    smoldyn_biosimulators = False


@unittest.skipIf(not smoldyn_biosimulators, 'The smoldyn.biosimulators module is not available')
class SmoldynUtilsTestCase(unittest.TestCase):
    FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn', 'bounce1.txt')
    COMP_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn', 'compart.txt')
    INVALID_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn', 'invalid.txt')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'is not a path to a model file'):
            get_parameters_variables_for_simulation(None, None, None, None)

        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            get_parameters_variables_for_simulation('not a file', None, None, None)

        with self.assertRaisesRegex(ValueError, 'not a valid BNGL or BNGL XML file'):
            get_parameters_variables_for_simulation(self.INVALID_FIXTURE_FILENAME, None, None, None)

    def test__parse_configuration_line(self):
        param = _parse_configuration_line('dim 3', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='number_dimensions',
            name='Number of dimensions',
            target='dim',
            new_value='3',
        )))

        param = _parse_configuration_line('low_wall x -100 p', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='low_x_wall_1',
            name='Low x wall 1',
            target='low_wall x',
            new_value='-100 p',
        )))

        param = _parse_configuration_line('high_wall x -100 p', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='high_x_wall_1',
            name='High x wall 1',
            target='high_wall x',
            new_value='-100 p',
        )))

        param = _parse_configuration_line('boundaries x 0 1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='x_boundary',
            name='X boundary',
            target='boundaries x',
            new_value='0 1',
        )))

        param = _parse_configuration_line('define SYSLENGTH 50', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='value_parameter_SYSLENGTH',
            name='Value of parameter "SYSLENGTH"',
            target='define SYSLENGTH',
            new_value='50',
        )))

        param = _parse_configuration_line('difc all 1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='diffusion_coefficient_species_all',
            name='Diffusion coefficient of species "all"',
            target='difc all',
            new_value='1',
        )))

        param = _parse_configuration_line('difc all(x) 1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='diffusion_coefficient_species_all_state_x',
            name='Diffusion coefficient of species "all" in state "x"',
            target='difc all(x)',
            new_value='1',
        )))

        param = _parse_configuration_line('difc_rule Prot* 22', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='diffusion_coefficient_rule_species_Prot_',
            name='Diffusion coefficient rule for species "Prot*"',
            target='difc_rule Prot*',
            new_value='22',
        )))

        param = _parse_configuration_line('difc_rule Prot*(x) 22', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='diffusion_coefficient_rule_species_Prot__state_x',
            name='Diffusion coefficient rule for species "Prot*" in state "x"',
            target='difc_rule Prot*(x)',
            new_value='22',
        )))

        param = _parse_configuration_line('difm red 1 0 0 0 0 0 0 0 2', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='membrane_diffusion_coefficient_species_red',
            name='Membrane diffusion coefficient of species "red"',
            target='difm red',
            new_value='1 0 0 0 0 0 0 0 2',
        )))

        param = _parse_configuration_line('difm red(x) 1 0 0 0 0 0 0 0 2', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='membrane_diffusion_coefficient_species_red_state_x',
            name='Membrane diffusion coefficient of species "red" in state "x"',
            target='difm red(x)',
            new_value='1 0 0 0 0 0 0 0 2',
        )))

        param = _parse_configuration_line('difm_rule red* 1 0 0 0 0 0 0 0 2', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='membrane_diffusion_coefficient_rule_species_red_',
            name='Membrane diffusion coefficient rule for species "red*"',
            target='difm_rule red*',
            new_value='1 0 0 0 0 0 0 0 2',
        )))

        param = _parse_configuration_line('difm_rule red*(x) 1 0 0 0 0 0 0 0 2', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='membrane_diffusion_coefficient_rule_species_red__state_x',
            name='Membrane diffusion coefficient rule for species "red*" in state "x"',
            target='difm_rule red*(x)',
            new_value='1 0 0 0 0 0 0 0 2',
        )))

        param = _parse_configuration_line('drift red 0 0 0', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='drift_species_red',
            name='Drift of species "red"',
            target='drift red',
            new_value='0 0 0',
        )))

        param = _parse_configuration_line('drift red(x) 0 0 0', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='drift_species_red_state_x',
            name='Drift of species "red" in state "x"',
            target='drift red(x)',
            new_value='0 0 0',
        )))

        param = _parse_configuration_line('drift_rule red* 0 0 0', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='drift_rule_species_red_',
            name='Drift rule for species "red*"',
            target='drift_rule red*',
            new_value='0 0 0',
        )))

        param = _parse_configuration_line('drift_rule red*(x) 0 0 0', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='drift_rule_species_red__state_x',
            name='Drift rule for species "red*" in state "x"',
            target='drift_rule red*(x)',
            new_value='0 0 0',
        )))

        param = _parse_configuration_line('surface_drift red surf1 all 0.1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='surface_drift_species_red_surface_surf1_shape_all',
            name='Surface drift of species "red" on surface "surf1" with panel shape "all"',
            target='surface_drift red surf1 all',
            new_value='0.1',
        )))

        param = _parse_configuration_line('surface_drift red(x) surf1 all 0.1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='surface_drift_species_red_state_x_surface_surf1_shape_all',
            name='Surface drift of species "red" in state "x" on surface "surf1" with panel shape "all"',
            target='surface_drift red(x) surf1 all',
            new_value='0.1',
        )))

        param = _parse_configuration_line('surface_drift_rule red* surf1 all 0.1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='surface_drift_rule_species_red__surface_surf1_panel_all',
            name='Surface drift rule for species "red*" on surface "surf1" of panel shape "all"',
            target='surface_drift_rule red* surf1 all',
            new_value='0.1',
        )))

        param = _parse_configuration_line('surface_drift_rule red*(x) surf1 all 0.1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='surface_drift_rule_species_red__state_x_surface_surf1_panel_all',
            name='Surface drift rule for species "red*" in state "x" on surface "surf1" of panel shape "all"',
            target='surface_drift_rule red*(x) surf1 all',
            new_value='0.1',
        )))

        param = _parse_configuration_line('mol 167 A 5 u u', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='initial_count_species_A_5_u_u',
            name='Initial count of species "A 5 u u"',
            target='mol A 5 u u',
            new_value='167',
        )))

        param = _parse_configuration_line('compartment_mol 500 red intersection', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='initial_count_species_red_intersection',
            name='Initial count of species "red intersection"',
            target='compartment_mol red intersection',
            new_value='500',
        )))

        param = _parse_configuration_line('surface_mol 100 red(up) all rect r1', {})
        self.assertTrue(param.is_equal(ModelAttributeChange(
            id='initial_count_species_red_up__all_rect_r1',
            name='Initial count of species "red(up) all rect r1"',
            target='surface_mol red(up) all rect r1',
            new_value='100',
        )))

    def test_get_parameters_variables_for_simulation(self):
        params, vars = get_parameters_variables_for_simulation(self.FIXTURE_FILENAME, None, None, None)

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='number_dimensions',
            name='Number of dimensions',
            target='dim',
            new_value='1',
        )))
        self.assertTrue(params[1].is_equal(ModelAttributeChange(
            id='x_boundary',
            name='X boundary',
            target='boundaries x',
            new_value='0 100 r',
        )))

        self.assertTrue(vars[0].is_equal(Variable(
            id='time',
            name='Time',
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='count_species_red',
            name='Count of species "red"',
            target='molcount red',
        )))
        self.assertTrue(vars[2].is_equal(Variable(
            id='count_species_green',
            name='Count of species "green"',
            target='molcount green',
        )))

        params, vars = get_parameters_variables_for_simulation(self.COMP_FIXTURE_FILENAME, None, None, None)

        self.assertTrue(vars[0].is_equal(Variable(
            id='time',
            name='Time',
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='count_species_red',
            name='Count of species "red"',
            target='molcount red',
        )))
        self.assertTrue(vars[2].is_equal(Variable(
            id='count_species_red_compartment_middle',
            name='Count of species "red" in compartment "middle"',
            target='molcountincmpt red middle',
        )))
        self.assertTrue(vars[3].is_equal(Variable(
            id='count_species_red_surface_walls',
            name='Count of species "red" in surface "walls"',
            target='molcountonsurf red walls',
        )))
