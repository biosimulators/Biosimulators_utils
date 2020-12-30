""" Standard exceptions issued by biosimulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..exceptions import BioSimulatorsException

__all__ = [
    'AlgorithmDoesNotSupportModelFeatureException',
    'AlgorithmCannotBeSubstitutedException',
]


class AlgorithmDoesNotSupportModelFeatureException(BioSimulatorsException):
    """ Exception that an algorithm does not support a feature of a model """
    pass  # pragma: no cover


class AlgorithmCannotBeSubstitutedException(BioSimulatorsException):
    """ Exception that the algorithm substitution policy does not allow an algorithm to be substituted """
    pass  # pragma: no cover
