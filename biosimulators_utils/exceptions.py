""" Standard exceptions issued by biosimulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

__all__ = [
    'BioSimulatorsException',
]


class BioSimulatorsException(Exception):
    """ Base class for simulator exceptions """
    pass  # pragma: no cover
