from biosimulators_utils.model_lang.bngl.utils import get_parameters_variables_outputs_for_simulation, parse_expression
from biosimulators_utils.sedml.data_model import (ModelLanguage, SteadyStateSimulation,
                                                  OneStepSimulation, UniformTimeCourseSimulation,
                                                  Algorithm, AlgorithmParameterChange,
                                                  Symbol,
                                                  ModelAttributeChange, Variable)
from biosimulators_utils.warnings import BioSimulatorsWarning
from unittest import mock
import os
import unittest


class BgnlUtilsTestCase(unittest.TestCase):
    FIXTURE_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl')
    FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'valid.bngl')
    MULTIPLE_ACTIONS_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'multiple-actions.bngl')
    NO_ACTIONS_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'no-actions.bngl')
    COMP_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'LR_comp.bngl')
    INVALID_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'invalid.bngl')
    INVALID_SYNTAX_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'bngl', 'invalid-syntax.bngl')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'is not a path to a model file'):
            get_parameters_variables_outputs_for_simulation(None, None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            get_parameters_variables_outputs_for_simulation('not a file', None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(ValueError, 'not a valid BNGL or BNGL XML file'):
            get_parameters_variables_outputs_for_simulation(self.INVALID_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(NotImplementedError, 'must be'):
            get_parameters_variables_outputs_for_simulation(self.FIXTURE_FILENAME, None, SteadyStateSimulation, None)

        with self.assertRaisesRegex(ValueError, 'must define a `method` argument'):
            get_parameters_variables_outputs_for_simulation(os.path.join(self.FIXTURE_DIRNAME, 'insufficient-action-args.bngl'),
                                                            None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(ValueError, 'must define a `method` argument'):
            get_parameters_variables_outputs_for_simulation(os.path.join(self.FIXTURE_DIRNAME, 'insufficient-action-args.bngl'),
                                                            None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(ValueError, r'`Simulation end time \(`t_end`\) must be set'):
            get_parameters_variables_outputs_for_simulation(os.path.join(self.FIXTURE_DIRNAME, 'insufficient-action-args-2.bngl'),
                                                            None, UniformTimeCourseSimulation, None)

    def test_get_parameters_variables_for_simulation_action_syntax_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'not a valid BNGL or BNGL XML file'):
            get_parameters_variables_outputs_for_simulation(self.INVALID_SYNTAX_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

    def test_get_parameters_variables_for_simulation(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(self.FIXTURE_FILENAME, None, OneStepSimulation, None)
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

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

        self.assertEqual(len(sims), 5)
        self.assertIsInstance(sims[0], UniformTimeCourseSimulation)
        expected_sim = UniformTimeCourseSimulation(
            id='simulation_0',
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1000000.,
            number_of_steps=1000,
            algorithm=Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    AlgorithmParameterChange(
                        kisao_id='KISAO_0000488',
                        new_value='2',
                    )
                ]
            )
        )
        self.assertTrue(sims[0].is_equal(expected_sim))

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

    def test_get_parameters_variables_for_simulation_with_step_args(self):
        with self.assertWarnsRegex(BioSimulatorsWarning, r'Output step interval \(`output_step_interval`\) was ignored'):
            params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
                os.path.join(self.FIXTURE_DIRNAME, 'step-action-args.bngl'),
                None, UniformTimeCourseSimulation, None)

        self.assertEqual(sims[0].algorithm.changes[-1].kisao_id, 'KISAO_0000415')
        self.assertEqual(sims[0].algorithm.changes[-1].new_value, '10000')

    def test_get_parameters_variables_for_simulation_with_sample_times(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            os.path.join(self.FIXTURE_DIRNAME, 'sample-times.bngl'),
            None, UniformTimeCourseSimulation, None)

        self.assertEqual(sims[0].initial_time, 0)
        self.assertEqual(sims[0].output_start_time, 1)
        self.assertEqual(sims[0].output_end_time, 5)
        self.assertEqual(sims[0].number_of_steps, 4)

    def test_get_parameters_variables_for_simulation_with_empty_sample_times(self):
        with self.assertRaisesRegex(ValueError, 'must be a non-empty array'):
            get_parameters_variables_outputs_for_simulation(os.path.join(self.FIXTURE_DIRNAME, 'empty-sample-times.bngl'),
                                                            None, UniformTimeCourseSimulation, None)

    def test_get_parameters_variables_for_simulation_with_non_uniform_sample_times(self):
        with self.assertWarnsRegex(BioSimulatorsWarning, 'Non-uniformly-distributed sample times'):
            params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
                os.path.join(self.FIXTURE_DIRNAME, 'non-uniform-sample-times.bngl'),
                None, UniformTimeCourseSimulation, None)

        self.assertEqual(sims[0].initial_time, 0)
        self.assertEqual(sims[0].output_start_time, 1)
        self.assertEqual(sims[0].output_end_time, 6)
        self.assertEqual(sims[0].number_of_steps, 1)

    def test_get_parameters_variables_for_simulation_native_data_types(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None,
            native_ids=True, native_data_types=True)

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id='k_1',
            name=None,
            target='parameters.k_1.value',
            new_value=0.0,
        )))
        self.assertTrue(params[7].is_equal(ModelAttributeChange(
            id='fa',
            name=None,
            target='parameters.fa.value',
            new_value=1E-5,
        )))
        self.assertTrue(params[9].is_equal(ModelAttributeChange(
            id='GeneA_00()',
            name=None,
            target='species.GeneA_00().initialCount',
            new_value=1,
        )))
        self.assertTrue(params[17].is_equal(ModelAttributeChange(
            id='gfunc',
            name=None,
            target='functions.gfunc.expression',
            new_value='(0.5*(Atot^2))/(10+(Atot^2))',
        )))

        self.assertEqual(len(sims), 5)
        self.assertIsInstance(sims[0], UniformTimeCourseSimulation)
        expected_sim = UniformTimeCourseSimulation(
            id='simulation_0',
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1000000.,
            number_of_steps=1000,
            algorithm=Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    AlgorithmParameterChange(
                        kisao_id='KISAO_0000488',
                        new_value=2,
                    )
                ]
            )
        )

        self.assertTrue(sims[0].is_equal(expected_sim))

        self.assertTrue(vars[0].is_equal(Variable(
            id=None,
            name=None,
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='A()',
            name=None,
            target='molecules.A().count',
        )))
        self.assertTrue(vars[9].is_equal(Variable(
            id='GeneA_00()',
            name=None,
            target='species.GeneA_00().count',
        )))
        self.assertEqual(len(vars), 17)

    def test_get_parameters_variables_for_simulation_multiple_actions(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.MULTIPLE_ACTIONS_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)
        self.assertEqual(len(sims), 7)

    def test_get_parameters_variables_for_simulation_no_actions(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.NO_ACTIONS_FIXTURE_FILENAME, None, OneStepSimulation, None)
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.NO_ACTIONS_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

    def test_get_parameters_variables_for_simulation_compartmentalized(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.COMP_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

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

    def test_parse_expression(self):
        self.assertEqual(parse_expression('123', native_data_types=False), '123')
        self.assertEqual(parse_expression('123', native_data_types=True), 123)

        self.assertEqual(parse_expression('xyz', native_data_types=False), 'xyz')
        self.assertEqual(parse_expression('xyz', native_data_types=True), 'xyz')
