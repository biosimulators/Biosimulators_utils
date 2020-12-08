""" Utilities for GitHub action workflows for reviewing and committing simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-08
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc
import functools
import io
import os
import requests
import types  # noqa: F401
import yamldown

__all__ = [
    'GitHubAction',
    'GitHubActionErrorHandling',
    'GitHubActionCaughtError',
]


class GitHubActionCaughtError(Exception):
    """ An error caught during the execution of a GitHub action """
    pass  # pragma: no cover


class GitHubActionErrorHandling(object):
    """ Methods for handing errors in the execution of GitHu actions """
    @classmethod
    def catch_errors(cls, issue_number, error_msg='Sorry. We encountered an unexpected error. Our team will review the error.',
                     caught_error_labels=None, uncaught_error_labels=None):
        """ Generator for a decorator for CI actions that catches errors and reports them as comments to an issue

        Args:
            issue_number (:obj:`str`): issue number
            error_msg (:obj:`str`, optional): error message to display to users
            caught_error_labels (:obj:`list` of :obj:`str`, optional): labels to apply to caught errors
            uncaught_error_labels (:obj:`list` of :obj:`str`, optional): labels to apply to uncaught errors
        """
        return functools.partial(cls._catch_errors, issue_number, error_msg, caught_error_labels or [], uncaught_error_labels or [])

    @staticmethod
    def _catch_errors(issue_number, error_msg, caught_error_labels, uncaught_error_labels, func):
        """ Decorator for CI actions that catches errors and reports them as comments to an issue

        Args:
            issue_number (:obj:`str`): issue number
            error_msg (:obj:`str`): error message to display to users
            caught_error_labels (:obj:`list` of :obj:`str`): labels to apply to caught errors
            uncaught_error_labels (:obj:`list` of :obj:`str`): labels to apply to uncaught errors
            func (:obj:`types.FunctionType`): decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except GitHubActionCaughtError:
                GitHubAction.add_labels_to_issue(issue_number, caught_error_labels)
                raise
            except Exception as error:
                GitHubAction.add_labels_to_issue(issue_number, uncaught_error_labels)
                GitHubAction.add_error_comment_to_issue(issue_number,
                                                        error_msg + '\n\n  ' + str(error).replace('\n', '\n  '),
                                                        raise_error=False)
                raise
        return wrapper


class GitHubAction(abc.ABC):
    """ A GitHub continuous integration action

    Attributes:
        gh_auth (:obj:`tuple` of :obj:`str`): authorization for GitHub (user and access token
        gh_repo (:obj:`str`): owner and name of the repository which triggered the action
        gh_action_run_id (:obj:`str`): GitHub action run id
        gh_action_run_url (:obj:`str`): URL for the GitHub action run
    """
    GH_ACTION_RUN_URL = 'https://github.com/{}/actions/runs/{}'
    ISSUE_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}'
    ISSUE_COMMENTS_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}/comments'
    ISSUE_LABELS_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}/labels'

    def __init__(self):
        self.gh_auth = self.get_gh_auth()
        self.gh_repo = self.get_gh_repo()
        self.gh_action_run_id = self.get_gh_action_run_id()
        self.gh_action_run_url = self.GH_ACTION_RUN_URL.format(self.gh_repo, self.gh_action_run_id)

    @abc.abstractmethod
    def run(self):
        pass  # pragma: no cover

    @staticmethod
    def get_gh_repo():
        """ Get the owner and name of the repository which triggered the action

        Returns:
            :obj:`str`: owner and name of the repository which triggered the action
        """
        return os.getenv('GH_REPO')

    @staticmethod
    def get_issue_number():
        """ Get the number of the issue which triggered the action

        Returns:
            :obj:`str`: issue number
        """
        return os.getenv('GH_ISSUE_NUMBER')

    @classmethod
    def get_issue(cls, issue_number):
        """ Get the properties of the GitHub issue for the submission

        Args:
            issue_number (:obj:`str`): issue number

        Returns:
            :obj:`dict`: properties of the GitHub issue for the submission
        """
        response = requests.get(
            cls.ISSUE_ENDPOINT.format(cls.get_gh_repo(), issue_number),
            auth=cls.get_gh_auth())
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_data_in_issue(issue):
        """ Get the YAML-structured data in an issue

        Args:
           issue (:obj:`dict`): properties of the GitHub issue for the submission

        Returns:
            :obj:`object`: YAML-structured data in an issue
        """
        body = io.StringIO(issue['body'].replace('\r', ''))
        data, _ = yamldown.load(body)
        return data

    @classmethod
    def get_labels_for_issue(cls, issue_number):
        """ Get the labels for an issue

        Args:
            issue_number (:obj:`str`): issue number

        Returns:
            :obj:`list` of :obj:`str`: labels
        """
        response = requests.get(
            cls.ISSUE_LABELS_ENDPOINT.format(cls.get_gh_repo(), issue_number),
            auth=cls.get_gh_auth())
        response.raise_for_status()

        labels = []
        for label in response.json():
            labels.append(label['name'])
        return labels

    @classmethod
    def add_labels_to_issue(cls, issue_number, labels):
        """ Add one or more labels to an issue

        Args:
            issue_number (:obj:`str`): issue number
            labels (:obj:`list` of :obj:`str`): labels to add to the issue
        """
        response = requests.post(
            cls.ISSUE_LABELS_ENDPOINT.format(cls.get_gh_repo(), issue_number),
            headers={'accept': 'application/vnd.github.v3+json'},
            auth=cls.get_gh_auth(),
            json={'labels': labels})
        response.raise_for_status()

    @classmethod
    def remove_label_from_issue(cls, issue_number, label):
        """ Remove a label from an issue

        Args:
            issue_number (:obj:`str`): issue number
            label (:obj:`str`): labels to add to the issue
        """
        response = requests.delete(
            cls.ISSUE_LABELS_ENDPOINT.format(cls.get_gh_repo(), issue_number) + '/' + label,
            auth=cls.get_gh_auth())
        response.raise_for_status()

    @classmethod
    def add_comment_to_issue(cls, issue_number, comment):
        """ Post a comment to the GitHub issue

        Args:
            issue_number (:obj:`str`): issue number
            comment (:obj:`str`): comment
        """
        response = requests.post(
            cls.ISSUE_COMMENTS_ENDPOINT.format(cls.get_gh_repo(), issue_number),
            headers={'accept': 'application/vnd.github.v3+json'},
            auth=cls.get_gh_auth(),
            json={'body': comment})
        response.raise_for_status()

    @classmethod
    def add_error_comment_to_issue(cls, issue_number, comment, raise_error=True):
        """ Post an error to the GitHub issue

        Args:
            issue_number (:obj:`str`): issue number
            comment (:obj:`str`): comment
            raise_error (:obj:`bool`, optional): if :obj:`True`, raise error

        Raises:
            :obj:`ValueError`
        """
        cls.add_comment_to_issue(issue_number, ''.join([
            '```diff\n',
            '- ' + comment.rstrip().replace('\n', '\n- ') + '\n',
            '```\n',
        ]))
        if raise_error:
            raise GitHubActionCaughtError(comment)

    @classmethod
    def close_issue(cls, issue_number):
        """ Close a GitHub issue

        Args:
            issue_number (:obj:`str`): issue number
        """
        response = requests.patch(
            cls.ISSUE_ENDPOINT.format(cls.get_gh_repo(), issue_number),
            auth=cls.get_gh_auth(),
            json={'state': 'closed'})
        response.raise_for_status()

    @staticmethod
    def get_gh_action_run_id():
        """ Get the id for the current GitHub action run

        Returns:
            :obj:`str`: GitHub action run id
        """
        return os.getenv('GH_ACTION_RUN_ID')

    @staticmethod
    def get_gh_auth():
        """ Get authorization for GitHub

        Returns:
            :obj:`tuple` of :obj:`str`: authorization for GitHub (user and access token)
        """
        user = os.getenv('GH_ISSUES_USER')
        access_token = os.getenv('GH_ISSUES_ACCESS_TOKEN')
        return (user, access_token)
