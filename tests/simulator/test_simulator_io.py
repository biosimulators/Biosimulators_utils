from biosimulators_utils.simulator.io import read_simulator_specs
from unittest import mock
import os
import requests
import unittest
import tempfile


class SimulatorIoTestCase(unittest.TestCase):
    def test_file(self):
        url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json'
        response = requests.get(url)
        response.raise_for_status()
        file, filename = tempfile.mkstemp(suffix='.json')
        os.close(file)
        with open(filename, 'wb') as file:
            file.write(response.content)
        read_simulator_specs(filename)
        os.remove(filename)

        with self.assertRaisesRegex(ValueError, 'must be encoded into JSON'):
            path = __file__
            read_simulator_specs(path)

    def test_url(self):
        url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json'
        specs = read_simulator_specs(url, patch={'version': '0.0.0'})
        self.assertEqual(specs['version'], '0.0.0')

        with self.assertRaises(requests.RequestException):
            url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/__undefined__'
            read_simulator_specs(url)

        with self.assertRaisesRegex(ValueError, 'must be encoded into JSON'):
            url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/README.md'
            read_simulator_specs(url)

        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: True, json=lambda: {})):
            with self.assertRaises(requests.RequestException):
                url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/README.md'
                read_simulator_specs(url)
