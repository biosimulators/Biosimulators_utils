""" Standard warnings issued by biosimulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .config import Colors
import termcolor
import warnings

__all__ = [
    'BioSimulatorsWarning',
    'warn',
]


class BioSimulatorsWarning(UserWarning):
    """ Base class for simulator warnings """
    pass  # pragma: no cover


def warn(message, category):
    """ Issue a warning in a color

    Args:
        message (:obj:`str`): message
        category (:obj:`type`): category
    """
    warnings.warn(termcolor.colored(message, Colors.warning.value), category)
