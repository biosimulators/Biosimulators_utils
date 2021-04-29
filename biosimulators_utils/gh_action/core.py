""" Utilities for GitHub action workflows for reviewing and committing simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-08
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Comment, GitHubActionCaughtError
import abc
import functools
import io
import os
import requests
import types  # noqa: F401
import yaml
import yamldown

__all__ = [
    'GitHubAction',
    'GitHubActionErrorHandling',
]


class GitHubActionErrorHandling(object):
    """ Methods for handing errors in the execution of GitHu actions """
    @classmethod
    def catch_errors(cls, uncaught_exception_msg_func=None,
                     caught_error_labels=None,
                     uncaught_error_labels=None):
        """ Generator for a decorator for CI actions that catches errors and reports them as comments to an issue

        Args:
            uncaught_exception_msg_func (:obj:`types.FunctionType`, optional): function to calculate error message to display to users
            caught_error_labels (:obj:`list` of :obj:`str`, optional): labels to apply to caught errors
            uncaught_error_labels (:obj:`list` of :obj:`str`, optional): labels to apply to uncaught errors
        """
        if uncaught_exception_msg_func is None:
            uncaught_exception_msg_func = cls.get_uncaught_exception_msg
        return functools.partial(cls._catch_errors, uncaught_exception_msg_func,
                                 caught_error_labels or [], uncaught_error_labels or [])

    @staticmethod
    def _catch_errors(uncaught_exception_msg_func, caught_error_labels, uncaught_error_labels, func):
        """ Decorator for CI actions that catches errors and reports them as comments to an issue

        Args:
            uncaught_exception_msg_func (:obj:`types.FunctionType`, optional): function to calculate error message to display to users
            caught_error_labels (:obj:`list` of :obj:`str`): labels to apply to caught errors
            uncaught_error_labels (:obj:`list` of :obj:`str`): labels to apply to uncaught errors
            func (:obj:`types.FunctionType`): decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except GitHubActionCaughtError:
                issue_number = os.getenv('GH_ISSUE_NUMBER')
                GitHubAction.add_labels_to_issue(issue_number, caught_error_labels)
                raise
            except Exception as exception:
                issue_number = os.getenv('GH_ISSUE_NUMBER')
                GitHubAction.add_labels_to_issue(issue_number, uncaught_error_labels)
                GitHubAction.add_error_comment_to_issue(issue_number,
                                                        uncaught_exception_msg_func(exception),
                                                        raise_error=False)
                raise
        return wrapper

    def get_uncaught_exception_msg(exception):
        """ Create an error message to display to users for all exceptions not caught during the
        exception of the :obj:`run` method for a GitHub action workflow (exceptions of all types
        except :obj:`GitHubActionCaughtError`)

        Args:
            exception (:obj:`Exception`): a failure encountered during the exception of the :obj:`run`
                method for the workflow

        Returns:
            :obj:`str`: error message to display to users
        """
        return [
            Comment(text='Sorry. We encountered an unexpected error. Our team will review the error.'),
            Comment(str(exception), error=True),
        ]


class GitHubAction(abc.ABC):
    """ A GitHub continuous integration action

    Attributes:
        gh_auth (:obj:`tuple` of :obj:`str`): authorization for GitHub (user and access token
        gh_repo (:obj:`str`): owner and name of the repository which triggered the action
    """
    GH_ACTION_RUN_URL = 'https://github.com/{}/actions/runs/{}'
    ISSUE_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}'
    ISSUE_COMMENTS_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}/comments'
    ISSUE_LABELS_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}/labels'
    ISSUE_ASIGNEES_ENDPOINT = 'https://api.github.com/repos/{}/issues/{}/assignees'

    def __init__(self):
        self.gh_auth = self.get_gh_auth()
        self.gh_repo = self.get_gh_repo()

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

        # hack to make yamldown work with Python 3.9
        if not hasattr(yaml, 'FullLoader'):
            yaml.FullLoader = yaml.Loader

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
    def reset_issue_labels(cls, issue_number, labels_to_remove):
        """ Reset the labels for an issue

        Args:
            issue_number (:obj:`str`): issue number
            labels_to_remove (:obj:`list` of :obj:`str`): labels to remove
        """
        labels = cls.get_labels_for_issue(issue_number)
        labels_to_remove = set(labels).intersection(set(labels_to_remove))

        for label in labels_to_remove:
            cls.remove_label_from_issue(issue_number, label)

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
    def add_error_comment_to_issue(cls, issue_number, comments, raise_error=True):
        """ Post an error to the GitHub issue

        Args:
            issue_number (:obj:`str`): issue number
            comments (:obj:`list` of :obj:`Comment`): comment
            raise_error (:obj:`bool`, optional): if :obj:`True`, raise error

        Raises:
            :obj:`ValueError`
        """
        formatted_text = []
        for comment in comments:
            if comment.error:
                formatted_text.append(cls.format_error_comment(comment.text))
            else:
                formatted_text.append(comment.text)

        cls.add_comment_to_issue(issue_number, '\n\n'.join(formatted_text))
        if raise_error:
            raise GitHubActionCaughtError('\n\n'.join(comment.text for comment in comments))

    @classmethod
    def format_error_comment(cls, comment):
        """ Format comment to display as error

        Args:
            comment (:obj:`str`): comment to format as error

        Returns:
            :obj:`str`: formatted comment
        """
        return ''.join([
            '```diff\n',
            '- ' + comment.rstrip().replace('\n', '\n- ') + '\n',
            '```\n',
        ])

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

    @classmethod
    def get_gh_action_run_url(cls):
        """ Get the URL for a GitHub action run

        Returns:
            :obj:`str`: URL for a GitHub action run
        """
        gh_repo = cls.get_gh_repo()
        gh_action_run_id = cls.get_gh_action_run_id()
        return cls.GH_ACTION_RUN_URL.format(gh_repo, gh_action_run_id)

    @staticmethod
    def get_gh_auth():
        """ Get authorization for GitHub

        Returns:
            :obj:`tuple` of :obj:`str`: authorization for GitHub (user and access token)
        """
        user = os.getenv('GH_ISSUES_USER')
        access_token = os.getenv('GH_ISSUES_ACCESS_TOKEN')
        return (user, access_token)

    @classmethod
    def assign_issue(cls, issue_number, users):
        """ Assign an issue to a list of users

        Args:
            issue_number (:obj:`str`): issue number
            users (:obj:`list` of :obj:`str`): GitHub ids of users to assign to issue
        """
        response = requests.post(
            cls.ISSUE_ASIGNEES_ENDPOINT.format(cls.get_gh_repo(), issue_number),
            auth=cls.get_gh_auth(),
            json={'assignees': users})
        response.raise_for_status()
