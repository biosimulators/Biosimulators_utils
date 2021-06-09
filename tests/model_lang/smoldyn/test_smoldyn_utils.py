from biosimulators_utils.model_lang.smoldyn.utils import get_parameters_variables_for_simulation
from biosimulators_utils.sedml.data_model import Symbol, ModelAttributeChange, Variable
import os
import unittest


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
