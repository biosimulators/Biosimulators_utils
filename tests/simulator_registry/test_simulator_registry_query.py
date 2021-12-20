from biosimulators_utils.simulator_registry.query import get_simulator_version_specs
from unittest import mock
import requests
import unittest


class QuerySimulatorRegistryTestCase(unittest.TestCase):
    def test_get_simulator_version_specs(self):
        version_specs = get_simulator_version_specs('tellurium')
        self.assertIsInstance(version_specs, list)
        self.assertIsInstance(version_specs[0], dict)
        self.assertEqual(set(version_spec['id'] for version_spec in version_specs), set(['tellurium']))

        def raise_for_status():
            raise requests.exceptions.HTTPError()

        def requests_get(self):
            return mock.Mock(
                status_code=404,
                raise_for_status=raise_for_status,
                json=lambda: {
                    'error': [
                        {
                            'status': 404,
                            'title': 'Error',
                            'detail': 'error',
                        },
                    ],
                },
            )

        with mock.patch('requests.get', side_effect=requests_get):
            self.assertEqual(get_simulator_version_specs('tellurium'), [])

        def requests_get(self):
            return mock.Mock(
                status_code=400,
                raise_for_status=raise_for_status,
                json=lambda: {
                    'error': [
                        {
                            'status': 400,
                            'title': 'Error',
                            'detail': 'error',
                        },
                    ],
                },
            )

        with mock.patch('requests.get', side_effect=requests_get):
            with self.assertRaises(ValueError):
                self.assertEqual(get_simulator_version_specs('tellurium'), [])
