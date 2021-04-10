from biosimulators_utils.sedml import model_utils
from biosimulators_utils.sedml.data_model import ModelLanguage
from unittest import mock
import unittest


class ModelUtilsTestCase(unittest.TestCase):
    def test_get_parameters_variables_for_simulation(self):
        with mock.patch('biosimulators_utils.sbml.utils.get_parameters_variables_for_simulation', return_value=(['a', 'b'], ['c', 'd'])):
            params, vars = model_utils.get_parameters_variables_for_simulation(None, ModelLanguage.SBML, None, None)
        self.assertEqual(params, ['a', 'b'])
        self.assertEqual(vars, ['c', 'd'])

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            model_utils.get_parameters_variables_for_simulation(None, 'not implemented', None, None)
