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
        sim2 = process_submission.get_simulator_submission_from_gh_issue_body(body)
        self.assertTrue(sim.is_equal(sim2))

        gh_username = 'biosimulatorsdaemon'
        gh_access_token = ''
        with mock.patch('requests.post', return_value=mock.Mock(raise_for_status=lambda: None)):
            submit.submit_simulator_to_biosimulators_registry(sim, gh_username, gh_access_token)

        sim = SimulatorSubmission(id, version, specUrl, False, False)
        body = submit.build_gh_issue_body(sim)
        sim2 = process_submission.get_simulator_submission_from_gh_issue_body(body)
        self.assertTrue(sim.is_equal(sim2))

        sim = SimulatorSubmission(id, version, specUrl, True, True)
        body = submit.build_gh_issue_body(sim)
        sim2 = process_submission.get_simulator_submission_from_gh_issue_body(body)
        self.assertTrue(sim.is_equal(sim2))

    def test_error_handling(self):
        data = {}
        with self.assertRaises(ValueError):
            process_submission.get_simulator_submission_from_gh_issue_body_data(data)

        data = {'id': 'sim'}
        with self.assertRaises(ValueError):
            process_submission.get_simulator_submission_from_gh_issue_body_data(data)

        data = {'id': 'sim', 'version': '1.0'}
        with self.assertRaises(ValueError):
            process_submission.get_simulator_submission_from_gh_issue_body_data(data)

        data = {'id': 'sim', 'version': '1.0', 'specificationsUrl': 'https://github.com/'}
        submission = process_submission.get_simulator_submission_from_gh_issue_body_data(data)
        self.assertTrue(submission.is_equal(SimulatorSubmission(
            'sim', '1.0', 'https://github.com/', False, False)))

        data = {'id': 'sim', 'version': '1.0', 'specificationsUrl': 'https://github.com/', 'bad': 'x'}
        with self.assertRaises(ValueError):
            process_submission.get_simulator_submission_from_gh_issue_body_data(data)
