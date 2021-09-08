from biosimulators_utils.model_lang.smoldyn.utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.sedml.data_model import Symbol, ModelAttributeChange, Variable, SteadyStateSimulation, UniformTimeCourseSimulation
import os
import unittest


class SmoldynUtilsTestCase(unittest.TestCase):
    FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn', 'bounce1.txt')
    COMP_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn', 'compart.txt')
    INVALID_FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'smoldyn', 'invalid.txt')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'is not a path to a model file'):
            get_parameters_variables_outputs_for_simulation(None, None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            get_parameters_variables_outputs_for_simulation('not a file', None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(ValueError, 'not a valid BNGL or BNGL XML file'):
            get_parameters_variables_outputs_for_simulation(self.INVALID_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

        with self.assertRaisesRegex(NotImplementedError, 'must be'):
            get_parameters_variables_outputs_for_simulation(self.FIXTURE_FILENAME, None, SteadyStateSimulation, None)

    def test_get_parameters_variables_for_simulation(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

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

        self.assertEqual(len(sims), 1)

        sim = sims[0]
        self.assertEqual(sim.initial_time, 0.0)
        self.assertEqual(sim.output_start_time, 0.0)
        self.assertEqual(sim.output_end_time, 100.0)
        self.assertEqual(sim.number_of_steps, 10000)
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000057')

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

        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            self.COMP_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None)

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

    def test_get_parameters_variables_for_simulation_native_ids_data_types(self):
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(self.FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None,
                                                                                      native_ids=True, native_data_types=True)

        self.assertTrue(params[0].is_equal(ModelAttributeChange(
            id=None,
            name=None,
            target='dim',
            new_value=1,
        )))
        self.assertTrue(params[1].is_equal(ModelAttributeChange(
            id='x',
            name=None,
            target='boundaries x',
            new_value=['0', '100', 'r'],
        )))

        self.assertEqual(len(sims), 1)

        sim = sims[0]
        self.assertEqual(sim.initial_time, 0.0)
        self.assertEqual(sim.output_start_time, 0.0)
        self.assertEqual(sim.output_end_time, 100.0)
        self.assertEqual(sim.number_of_steps, 10000)
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000057')

        self.assertTrue(vars[0].is_equal(Variable(
            id=None,
            name=None,
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='red',
            name=None,
            target='molcount red',
        )))
        self.assertTrue(vars[2].is_equal(Variable(
            id='green',
            name=None,
            target='molcount green',
        )))

        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(self.COMP_FIXTURE_FILENAME, None, UniformTimeCourseSimulation, None,
                                                                                      native_ids=True, native_data_types=True)

        self.assertTrue(vars[0].is_equal(Variable(
            id=None,
            name=None,
            symbol=Symbol.time.value,
        )))
        self.assertTrue(vars[1].is_equal(Variable(
            id='red',
            name=None,
            target='molcount red',
        )))
        self.assertTrue(vars[2].is_equal(Variable(
            id='red.middle',
            name=None,
            target='molcountincmpt red middle',
        )))
        self.assertTrue(vars[3].is_equal(Variable(
            id='red.walls',
            name=None,
            target='molcountonsurf red walls',
        )))
