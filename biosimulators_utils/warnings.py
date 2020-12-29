""" Standard warnings issued by biosimulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

__all__ = [
    'BioSimulatorsWarning',
]


class BioSimulatorsWarning(UserWarning):
    """ Base class for simulator warnings """
    pass  # pragma: no cover
