from biosimulators_utils.biosimulations.utils import submit_project_to_runbiosimulations
from unittest import mock
import os
import unittest


class BioSimulationsUtilsTestCase(unittest.TestCase):
    def test_submit_project_to_runbiosimulations_by_file(self):
        name = 'test'
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex')
        simulator = 'copasi'
        with mock.patch('requests.post', return_value=mock.Mock(
            raise_for_status=lambda: None,
            json=lambda: {
                'id': '*' * 30
            }
        )):
            id = submit_project_to_runbiosimulations(name, filename, simulator)
        self.assertIsInstance(id, str)
        self.assertNotEqual(id, '')

    def test_submit_project_to_runbiosimulations_by_url(self):
        name = 'test'
        url = 'https://github.com/biosimulators/Biosimulators_utils/blob/dev/tests/fixtures/Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex?raw=true'
        simulator = 'copasi'
        with mock.patch('requests.post', return_value=mock.Mock(
            raise_for_status=lambda: None,
            json=lambda: {
                'id': '*' * 30
            }
        )):
            id = submit_project_to_runbiosimulations(name, url, simulator)
        self.assertIsInstance(id, str)
        self.assertNotEqual(id, '')
