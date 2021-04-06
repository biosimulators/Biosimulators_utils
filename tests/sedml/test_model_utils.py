from biosimulators_utils.sedml import model_utils
from biosimulators_utils.sedml.data_model import ModelLanguage
from unittest import mock
import unittest


class ModelUtilsTestCase(unittest.TestCase):
    def test_get_variables_for_simulation(self):
        with mock.patch('biosimulators_utils.sbml.utils.get_variables_for_simulation', return_value=['a', 'b']):
            vars = model_utils.get_variables_for_simulation(None, ModelLanguage.SBML, None, None)
        self.assertEqual(vars, ['a', 'b'])

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            vars = model_utils.get_variables_for_simulation(None, 'not implemented', None, None)
