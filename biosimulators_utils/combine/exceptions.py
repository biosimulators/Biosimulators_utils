""" Exceptions for COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-01-12
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..exceptions import BioSimulatorsException

__all__ = [
    'CombineArchiveExecutionError',
]


class CombineArchiveExecutionError(BioSimulatorsException):
    """ Error that a SED document could not be executed """
    pass  # pragma: no cover
