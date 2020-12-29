""" Standard warnings issued by biosimulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning

__all__ = [
    'AlternateAlgorithmWarning',
]


class AlternateAlgorithmWarning(BioSimulatorsWarning):
    """ Warning that an alternative algorithm was used rather than the requested algorithm """
    pass  # pragma: no cover
