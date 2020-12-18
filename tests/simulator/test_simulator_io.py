from biosimulators_utils.simulator.io import read_simulator_specs
from unittest import mock
import requests
import simplejson.errors
import unittest


class SimulatorIoTestCase(unittest.TestCase):
    def test(self):
        url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json'
        specs = read_simulator_specs(url)

        with self.assertRaises(requests.RequestException):
            url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/__undefined__'
            read_simulator_specs(url)

        with self.assertRaises(ValueError):
            url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/README.md'
            read_simulator_specs(url)

        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: True, json=lambda: {})):
            with self.assertRaises(ValueError):
                url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/README.md'
                read_simulator_specs(url)
