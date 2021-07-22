""" Warnings for plots

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-01-20
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning

__all__ = [
    'IllogicalVizWarning',
]


class IllogicalVizWarning(BioSimulatorsWarning):
    """ Warning that a plot is may be illogical (e.g., has mixed axes or scales) """
    pass  # pragma: no cover
