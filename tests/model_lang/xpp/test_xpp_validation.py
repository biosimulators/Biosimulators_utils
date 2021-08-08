from biosimulators_utils.model_lang.xpp import validation
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import collections
import os
import unittest


class XppValidationTestCase(unittest.TestCase):
    FIXTURE_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'xpp')

    def test(self):
        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        parameters = collections.OrderedDict([
            ('aee', 10),
            ('aie', 8),
            ('aei', 12),
            ('aii', 3),
            ('ze', .2),
            ('zi', 4),
            ('tau', 1),
            ('ie0', 0.0),
            ('ie1', 0.0),
            ('w', 0.25),
            ('ii0', 0.0),
            ('ii1', 0.0),
        ])
        initial_conditions = collections.OrderedDict([
            ('U', .1),
            ('V', .05),
        ])
        simulation_method = {
            'total': '40',
            'xp': 'u',
            'yp': 'v',
            'xlo': '-.1',
            'xhi': '1',
            'ylo': '-.1',
            'yhi': '1',
        }
        self.assertEqual(list(model['parameters'].keys()), list(parameters.keys()))
        self.assertEqual(model['parameters'], parameters)
        self.assertEqual(model['simulation_method'], simulation_method)
        self.assertEqual(model, {
            'parameters': parameters,
            'initial_conditions': initial_conditions,
            'simulation_method': simulation_method,
        })
        self.assertEqual(model['initial_conditions'], initial_conditions)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-modified.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(model['simulation_method'], {
            'total': '130',
            'njmp': '20',
            'xp': 'u',
            'yp': 'v',
            'xlo': '-.1',
            'xhi': '1',
            'ylo': '-.1',
            'yhi': '1',
        })

        filename = None
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('is not a path', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'not exist.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('does not exist', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-invalid.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('is not a valid XPP', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-invalid.ode')
        return_value_1 = mock.Mock(
            returncode=1,
            stdout=mock.Mock(
                decode=lambda errors: 'Error message',
            ),
        )
        with mock.patch('subprocess.run', return_value=return_value_1):
            errors, warnings, model = validation.validate_model(filename)
        self.assertIn('could not be validated', flatten_nested_list_of_strings(errors))
        self.assertIn('Error message', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-modified-3.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('T0 must be a float', flatten_nested_list_of_strings(errors))
        self.assertIn('TOTAL must be a float', flatten_nested_list_of_strings(errors))
        self.assertIn('DT must be a float', flatten_nested_list_of_strings(errors))
        self.assertIn('NJMP must be a positive integer', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertNotEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-modified-4.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('T0 must be a float', flatten_nested_list_of_strings(errors))
        self.assertIn('TOTAL must be a float', flatten_nested_list_of_strings(errors))
        self.assertIn('DT must be a float', flatten_nested_list_of_strings(errors))
        self.assertIn('NJMP must be a positive integer', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertNotEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-modified-5.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertIn('Number of steps must be an integer', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        self.assertNotEqual(model, None)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'BIOMD0000000001.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertEqual(errors, [])
        self.assertIn("I' is a duplicate name", flatten_nested_list_of_strings(warnings))
        self.assertEqual(model['simulation_method'], {
            'delay': '50',
            'meth': 'cvode',
            'tol': '1e-6',
            'atol': '1e-8',
            'bound': '40000',
            'total': '200',
        })
