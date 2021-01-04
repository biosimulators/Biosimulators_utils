from biosimulators_utils.gh_action.core import GitHubAction, GitHubActionErrorHandling
from biosimulators_utils.gh_action.data_model import Comment, GitHubActionCaughtError
from unittest import mock
import os
import unittest


class GitHubActionTestCase(unittest.TestCase):
    def test(self):
        env = {
            'GH_REPO': 'biosimulators/Biosimulators',
            'GH_ISSUES_USER': 'username',
            'GH_ISSUES_ACCESS_TOKEN': 'token',
            'GH_ACTION_RUN_ID': '1000000',
            'GH_ISSUE_NUMBER': '4',
        }
        with mock.patch.dict(os.environ, env):
            class Action(GitHubAction):
                def run(self):
                    pass

            action = Action()
            self.assertEqual(action.gh_auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
            self.assertEqual(action.gh_repo, env['GH_REPO'])
            self.assertEqual(action.get_gh_action_run_id(), env['GH_ACTION_RUN_ID'])
            self.assertEqual(action.get_gh_action_run_url(), 'https://github.com/biosimulators/Biosimulators/actions/runs/1000000')

            self.assertEqual(action.get_issue_number(), env['GH_ISSUE_NUMBER'])

            def requests_method(url, auth):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                return mock.Mock(raise_for_status=lambda: None, json=lambda: [
                    {'name': 'X'},
                    {'name': 'Y'},
                ])
            with mock.patch('requests.get', side_effect=requests_method):
                self.assertEqual(action.get_labels_for_issue('4'), ['X', 'Y'])

            def requests_method(url, auth):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                return mock.Mock(raise_for_status=lambda: None, json=lambda: {
                    'body': (
                        '---\r\n'
                        'id: tellurium\r\n'
                        'version: 2.1.6\r\n'
                        'specificationsUrl: https://raw.githubusercontent.com/.../biosimulators.json\r\n'
                        '\r\n'
                        '---\r\n'
                    )
                })
            with mock.patch('requests.get', side_effect=requests_method):
                self.assertEqual(action.get_data_in_issue(action.get_issue('4')), {
                    'id': 'tellurium',
                    'version': '2.1.6',
                    'specificationsUrl': 'https://raw.githubusercontent.com/.../biosimulators.json',
                })

            def requests_method(url, headers, auth, json):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                self.assertEqual(json, {'labels': ['x', 'y']})
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.post', side_effect=requests_method):
                action.add_labels_to_issue('4', ['x', 'y'])

            def requests_method(url, auth):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels/x')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.delete', side_effect=requests_method):
                action.remove_label_from_issue('4', 'x')

            def requests_method(url, auth, headers, json):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/comments')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                self.assertEqual(json['body'], 'xxxx')
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.post', side_effect=requests_method):
                action.add_comment_to_issue('4', 'xxxx')

            def requests_method(url, auth, headers, json):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/comments')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                self.assertEqual(json['body'], '```diff\n- xxxx\n```\n')
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.post', side_effect=requests_method):
                with self.assertRaises(GitHubActionCaughtError):
                    action.add_error_comment_to_issue('4', [Comment(text='xxxx', error=True)])

            def requests_method(url, auth, json):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                self.assertEqual(json, {'state': 'closed'})
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.patch', side_effect=requests_method):
                action.close_issue('4')

            def requests_get(url, auth):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                return mock.Mock(raise_for_status=lambda: None, json=lambda: [{'name': 'x'}, {'name': 'y'}, {'name': 'z'}])

            def requests_delete_1(url, auth):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels/y')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.get', side_effect=requests_get):
                with mock.patch('requests.delete', side_effect=requests_delete_1):
                    action.reset_issue_labels('4', ['y'])

            def requests_post(url, json=None, auth=None, headers=None):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/assignees')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                self.assertEqual(json, {'assignees': ['userid']})
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.post', side_effect=requests_post):
                action.assign_issue('4', ['userid'])

            # error handling: caught error
            class Action(GitHubAction):
                @GitHubActionErrorHandling.catch_errors(caught_error_labels=['invalid'],
                                                        uncaught_error_labels=['action_error'])
                def run(self):
                    raise GitHubActionCaughtError()

            def requests_labels_method(url, headers, auth, json):
                self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels')
                self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                self.assertEqual(json, {'labels': ['invalid']})
                return mock.Mock(raise_for_status=lambda: None)
            with mock.patch('requests.post', side_effect=requests_labels_method):
                with self.assertRaises(GitHubActionCaughtError):
                    Action().run()

            # error handling: uncaught error
            class Action(GitHubAction):
                @GitHubActionErrorHandling.catch_errors(caught_error_labels=['invalid'],
                                                        uncaught_error_labels=['action_error'])
                def run(self):
                    raise ValueError('Details about error')

            class RequestMethod(object):
                def __init__(self, unittest_self):
                    self.i_request = 0
                    self.unittest_self = unittest_self

                def requests_method(self, url, headers, auth, json):
                    self.i_request += 1
                    if self.i_request == 1:
                        self.unittest_self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/labels')
                        self.unittest_self.assertEqual(json, {'labels': ['action_error']})
                    else:
                        self.unittest_self.assertEqual(url, 'https://api.github.com/repos/biosimulators/Biosimulators/issues/4/comments')
                        self.unittest_self.assertEqual(json['body'], (
                            'Sorry. We encountered an unexpected error. Our team will review the error.\n'
                            '\n'
                            '```diff\n'
                            '- Details about error\n'
                            '```\n'))
                    self.unittest_self.assertEqual(auth, (env['GH_ISSUES_USER'], env['GH_ISSUES_ACCESS_TOKEN']))
                    return mock.Mock(raise_for_status=lambda: None)

            with mock.patch('requests.post', side_effect=RequestMethod(self).requests_method):
                with self.assertRaises(ValueError):
                    Action().run()
