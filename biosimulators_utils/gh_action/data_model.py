""" Data model for GitHub action workflows

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-08
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..exceptions import BioSimulatorsException

__all__ = [
    'GitHubActionCaughtError',
    'Comment',
]


class GitHubActionCaughtError(BioSimulatorsException):
    """ An error caught during the execution of a GitHub action """
    pass  # pragma: no cover


class Comment(object):
    """ A comment on an issue

    Attributes:
        text (:obj:`str`): text
        error (:obj:`bool`): if :obj:`True`, format as error
    """

    def __init__(self, text=None, error=None):
        """
        Args:
            text (:obj:`str`): text
            error (:obj:`bool`): if :obj:`True`, format as error
        """
        self.text = text
        self.error = error
