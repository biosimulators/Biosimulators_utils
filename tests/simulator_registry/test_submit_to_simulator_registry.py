from biosimulators_utils.simulator_registry.data_model import SimulatorSubmission
from biosimulators_utils.simulator_registry import process_submission
from biosimulators_utils.simulator_registry import submit
from unittest import mock
import unittest


class RegisterSimulatorTestCase(unittest.TestCase):
    def test(self):
        id = 'tellurium'
        version = '2.1.6'
        specUrl = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json'
        sim = SimulatorSubmission(id, version, specUrl)

        body = submit.build_gh_issue_body(sim)
        sim2 = process_submission.parse_gh_issue_body(body)
        self.assertTrue(sim.is_equal(sim2))

        gh_username = 'biosimulatorsdaemon'
        gh_access_token = ''
        with mock.patch('requests.post', return_value=mock.Mock(raise_for_status=lambda: None)):
            submit.submit_simulator_to_biosimulators_registry(sim, gh_username, gh_access_token)
