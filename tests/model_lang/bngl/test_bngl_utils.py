from biosimulators_utils.model_lang.bngl.utils import get_parameters_variables_for_simulation
from biosimulators_utils.sedml.data_model import (ModelLanguage, SteadyStateSimulation,
                                                  OneStepSimulation, UniformTimeCourseSimulation, Symbol,
                                                  ModelAttributeChange, Variable)
from unittest import mock
import os
import unittest


class BgnlUtilsTestCase(unittest.TestCase):
    FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'valid.bngl')
    COMP_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'LR_comp.bngl')
    INVALID_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'invalid.bngl')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'is not a path to a model file'):
            get_parameters_variables_for_simulation(None, None, None, None)

        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            get_parameters_variables_for_simulation('not a file', None, None, None)

        with self.assertRaisesRegex(ValueError, 'not a valid BNGL or BNGL XML file'):
            get_parameters_variables_for_simulation(self.INVALID_FIXTURE_FILENAME, None, None, None)

    def test_get_parameters_variables_for_simulation(self):
        params, vars = get_parameters_variables_for_simulation(self.FIXTURE_FILENAME, None, None, None)

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='value_parameter_k_1',
            name='Value of parameter "k_1"',
            target='parameters.k_1.value',
            new_value='0.0',
        )))
        self.assertTrue(params[7].is_equal(ModelAttributeChange(
            id='value_parameter_fa',
            name='Value of parameter "fa"',
            target='parameters.fa.value',
            new_value='1E-5',
        )))
        self.assertTrue(params[9].is_equal(ModelAttributeChange(
            id='initial_amount_species_GeneA_00__',
            name='Initial amount of species "GeneA_00()"',
            target='species.GeneA_00().initialCount',
            new_value='1',
        )))
        self.assertTrue(params[17].is_equal(ModelAttributeChange(
            id='expression_function_gfunc',
            name='Expression of function "gfunc()"',
            target='functions.gfunc.expression',
            new_value='(0.5*(Atot^2))/(10+(Atot^2))',
        )))

        self.assertTrue(vars[0].is_equal(Variable(
            id='time',
            name='Time',
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='amount_molecule_A__',
            name='Dynamics of molecule "A()"',
            target='molecules.A().count',
        )))
        self.assertTrue(vars[9].is_equal(Variable(
            id='amount_species_GeneA_00__',
            name='Dynamics of species "GeneA_00()"',
            target='species.GeneA_00().count',
        )))
        self.assertEqual(len(vars), 17)

    def test_get_parameters_variables_for_simulation_compartmentalized(self):
        params, vars = get_parameters_variables_for_simulation(self.COMP_FIXTURE_FILENAME, None, None, None)

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='value_parameter_NaV',
            name='Value of parameter "NaV"',
            target='parameters.NaV.value',
            new_value='6.02e8',
        )))
        self.assertTrue(params[2].is_equal(ModelAttributeChange(
            id='value_parameter_Vec',
            name='Value of parameter "Vec"',
            target='parameters.Vec.value',
            new_value='1000*Vcell',
        )))
        self.assertTrue(params[11].is_equal(ModelAttributeChange(
            id='initial_size_compartment_EC',
            name='Initial size of 3-D compartment "EC"',
            target='compartments.EC.size',
            new_value='1000000',
        )))
        self.assertTrue(params[12].is_equal(ModelAttributeChange(
            id='initial_size_compartment_PM',
            name='Initial size of 2-D compartment "PM"',
            target='compartments.PM.size',
            new_value='10',
        )))
        self.assertTrue(params[14].is_equal(ModelAttributeChange(
            id='initial_amount_species__EC_L_r_',
            name='Initial amount of species "@EC:L(r)"',
            target='species.@EC:L(r).initialCount',
            new_value='L0',
        )))
        self.assertEqual(len(params), 16)

        self.assertTrue(vars[0].is_equal(Variable(
            id='time',
            name='Time',
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='amount_molecule_L_r_',
            name='Dynamics of molecule "L(r)"',
            target='molecules.L(r).count',
        )))
        self.assertTrue(vars[3].is_equal(Variable(
            id='amount_species__EC_L_r_',
            name='Dynamics of species "@EC:L(r)"',
            target='species.@EC:L(r).count',
        )))
        self.assertTrue(vars[5].is_equal(Variable(
            id='amount_molecule_L_r_1__R_l_1_',
            name='Dynamics of molecule "L(r!1).R(l!1)"',
            target='molecules.L(r!1).R(l!1).count',
        )))
        self.assertEqual(len(vars), 7)
