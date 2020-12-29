""" Warnings for misuse of COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning


__all__ = ['NoSedmlWarning']


class NoSedmlWarning(BioSimulatorsWarning):
    """ Warning that a COMBINE/OMEX archive does not contain any SED-ML files """
    pass  # pragma: no cover
