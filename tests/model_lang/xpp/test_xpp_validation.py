from biosimulators_utils.model_lang.xpp import validation
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import collections
import os
import shutil
import tempfile
import unittest


class XppValidationTestCase(unittest.TestCase):
    FIXTURE_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'xpp')

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

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
        }
        plot = {
            'elements': {
                1: {
                    'x': 'U',
                    'y': 'V',
                },
            },
            'xlo': -.1,
            'xhi': 1.,
            'ylo': -.1,
            'yhi': 1.,
        }
        self.assertEqual(list(model['parameters'].keys()), list(parameters.keys()))
        self.assertEqual(model['parameters'], parameters)
        self.assertEqual(model['simulation_method'], simulation_method)
        self.assertEqual(model['plot'], plot)
        self.assertEqual(model, {
            'parameters': parameters,
            'initial_conditions': initial_conditions,
            'sets': {},
            'auxiliary_variables': collections.OrderedDict(),
            'simulation_method': simulation_method,
            'plot': plot,
        })
        self.assertEqual(model['initial_conditions'], initial_conditions)

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-modified.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(model['simulation_method'], {
            'total': '130',
            'njmp': '20',
        })
        self.assertEqual(model['plot'], {
            'elements': {
                1: {
                    'x': 'U',
                    'y': 'V',
                },
            },
            'xlo': -.1,
            'xhi': 1.,
            'ylo': -.1,
            'yhi': 1.,
            'axes': 2,
        })

        filename = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-auxiliary-variables.ode')
        errors, warnings, model = validation.validate_model(filename)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(model['auxiliary_variables'], collections.OrderedDict({
            'dv': "-u+f(aee*u-aie*v-ze+i_e(t))",
        }))

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

    def test_get_xpp_input_configuration_from_directory(self):
        with self.assertRaisesRegex(ValueError, 'must contain an ODE file'):
            validation.get_xpp_input_configuration_from_directory(self.dirname)

        ode1 = os.path.join(self.dirname, 'my.ode')
        with open(ode1, 'w'):
            pass

        files = validation.get_xpp_input_configuration_from_directory(self.dirname)
        self.assertEqual(files, (ode1, None, None, None))

        set1 = os.path.join(self.dirname, 'my.set')
        with open(set1, 'w'):
            pass

        par1 = os.path.join(self.dirname, 'my.par')
        with open(par1, 'w'):
            pass

        ic1 = os.path.join(self.dirname, 'my.ic')
        with open(ic1, 'w'):
            pass

        files = validation.get_xpp_input_configuration_from_directory(self.dirname)
        self.assertEqual(files, (ode1, set1, par1, ic1))

        set2 = os.path.join(self.dirname, 'my2.set')
        with open(set2, 'w'):
            pass

        par2 = os.path.join(self.dirname, 'my2.par')
        with open(par2, 'w'):
            pass

        ic2 = os.path.join(self.dirname, 'my2.ic')
        with open(ic2, 'w'):
            pass

        with self.assertRaisesRegex(ValueError, 'Only 1'):
            validation.get_xpp_input_configuration_from_directory(self.dirname)

    def test_from_directory(self):
        dirname = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan')
        errors, warnings, model = validation.validate_model(dirname)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        parameters = dict([
            ('aee', 11.),
            ('aie', 8.),
            ('aei', 12.),
            ('aii', 3.),
            ('ze', .2),
            ('zi', 4.),
            ('tau', 1.),
            ('ie0', 0.0),
            ('ie1', 0.0),
            ('w', 0.25),
            ('ii0', 0.0),
            ('ii1', 0.0),
        ])
        initial_conditions = dict([
            ('U', .2),
            ('V', .1),
        ])
        simulation_method = {
            'total': '40',
        }
        plot = {
            'elements': {
                1: {
                    'x': 'U',
                    'y': 'V',
                },
            },
            'xlo': -.1,
            'xhi': 1.,
            'ylo': -.1,
            'yhi': 1.,
        }
        model['parameters'] = dict(model['parameters'])
        model['initial_conditions'] = dict(model['initial_conditions'])
        self.assertEqual(list(model['parameters'].keys()), list(parameters.keys()))
        self.assertEqual(model['parameters'], parameters)
        self.assertEqual(model['simulation_method'], simulation_method)
        self.assertEqual(model['plot'], plot)
        self.assertEqual(model, {
            'parameters': parameters,
            'initial_conditions': initial_conditions,
            'sets': {},
            'auxiliary_variables': collections.OrderedDict(),
            'simulation_method': simulation_method,
            'plot': plot,
        })

    def test_with_sets(self):
        dirname = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-with-sets.ode')
        errors, warnings, model = validation.validate_model(dirname)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        parameters = dict([
            ('aee', 10.),
            ('aie', 8.),
            ('aei', 12.),
            ('aii', 3.),
            ('ze', .2),
            ('zi', 4.),
            ('tau', 1.),
            ('ie0', 0.0),
            ('ie1', 0.0),
            ('w', 0.25),
            ('ii0', 0.0),
            ('ii1', 0.0),
        ])
        initial_conditions = dict([
            ('U', .3),
            ('V', .05),
        ])
        sets = {
            'set1': {
                'parameters': {'aee': 12.},
                'initial_conditions': {'U': 0.2},
            },
            'set2': {
                'parameters': {'aee': 13.},
                'initial_conditions': {'U': 0.3},
            },
        }
        simulation_method = {
            'total': '40',
        }
        plot = {
            'elements': {
                1: {
                    'x': 'U',
                    'y': 'V',
                },
            },
            'xlo': -.1,
            'xhi': 1.,
            'ylo': -.1,
            'yhi': 1.,
        }
        model['parameters'] = dict(model['parameters'])
        model['initial_conditions'] = dict(model['initial_conditions'])
        self.assertEqual(list(model['parameters'].keys()), list(parameters.keys()))
        self.assertEqual(model['parameters'], parameters)
        self.assertEqual(model['initial_conditions'], initial_conditions)
        self.assertEqual(model['sets'], sets)
        self.assertEqual(model['simulation_method'], simulation_method)
        self.assertEqual(model['plot'], plot)
        self.assertEqual(model, {
            'parameters': parameters,
            'initial_conditions': initial_conditions,
            'sets': sets,
            'auxiliary_variables': collections.OrderedDict(),
            'simulation_method': simulation_method,
            'plot': plot,
        })

    def test_from_directory_2(self):
        dirname = os.path.join(self.FIXTURE_DIRNAME, 'wilson-cowan-2')
        errors, warnings, model = validation.validate_model(dirname)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        parameters = dict([
            ('aee', 10.),
            ('aie', 9.),
            ('aei', 12.),
            ('aii', 3.),
            ('ze', .2),
            ('zi', 4.),
            ('tau', 1.),
            ('ie0', 0.0),
            ('ie1', 0.0),
            ('w', 0.25),
            ('ii0', 0.0),
            ('ii1', 0.0),
        ])
        initial_conditions = dict([
            ('U', .1),
            ('V', .04),
        ])
        sets = {}
        simulation_method = {
            'total': '40',
        }
        plot = {
            'elements': {
                1: {
                    'x': 'U',
                    'y': 'V',
                },
            },
            'xlo': -.1,
            'xhi': 1.,
            'ylo': -.1,
            'yhi': 1.,
        }
        model['parameters'] = dict(model['parameters'])
        model['initial_conditions'] = dict(model['initial_conditions'])
        self.assertEqual(list(model['parameters'].keys()), list(parameters.keys()))
        self.assertEqual(model['parameters'], parameters)
        self.assertEqual(model['initial_conditions'], initial_conditions)
        self.assertEqual(model['sets'], sets)
        self.assertEqual(model['simulation_method'], simulation_method)
        self.assertEqual(model['plot'], plot)
        self.assertEqual(model, {
            'parameters': parameters,
            'initial_conditions': initial_conditions,
            'sets': sets,
            'auxiliary_variables': collections.OrderedDict(),
            'simulation_method': simulation_method,
            'plot': plot,
        })

    def test_cannot_parse_other_formats(self):
        filename = os.path.join(self.FIXTURE_DIRNAME, '..', 'BIOMD0000000075.xml')
        errors, warnings, model = validation.validate_model(filename)
        self.assertNotEqual(errors, [])
        self.assertEqual(warnings, [])
