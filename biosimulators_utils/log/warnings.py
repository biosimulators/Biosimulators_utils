""" Warnings for logging

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-02-04
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning

__all__ = [
    'StandardOutputNotLoggedWarning',
]


class StandardOutputNotLoggedWarning(BioSimulatorsWarning):
    """ Warning that standard output and error could not be logged """
    pass  # pragma: no cover
