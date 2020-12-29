""" Warnings for misuse of the KiSAO ontology

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning

__all__ = [
    'InvalidKisaoTermIdWarning',
]


class InvalidKisaoTermIdWarning(BioSimulatorsWarning):
    """ Warning that a string is likely not an id for a KiSAO term """
    pass  # pragma: no cover
