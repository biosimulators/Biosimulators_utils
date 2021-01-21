""" Warnings for misuse of SED-ML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning

__all__ = [
    'IllogicalSedmlWarning',
    'InconsistentVariableShapesWarning',
    'NoTasksWarning',
    'NoOutputsWarning',
    'NoDataSetsWarning',
    'NoCurvesWarning',
    'NoSurfacesWarning',
    'SedmlFeatureNotSupportedWarning',
]


class IllogicalSedmlWarning(BioSimulatorsWarning):
    """ Warning that a SED document is illogical, such as when a report or plot contains
    no datasets, curves, or surfaces.
    """
    pass  # pragma: no cover


class InconsistentVariableShapesWarning(BioSimulatorsWarning):
    """ Warning that the variables of a data generator have different shapes. """
    pass  # pragma: no cover


class NoTasksWarning(IllogicalSedmlWarning):
    """ Warning that a SED document does not have any tasks """
    pass


class NoOutputsWarning(IllogicalSedmlWarning):
    """ Warning that a SED document does not have any outputs """
    pass


class NoDataSetsWarning(IllogicalSedmlWarning):
    """ Warning that a report does not contain any data sets """
    pass


class NoCurvesWarning(IllogicalSedmlWarning):
    """ Warning that a 2D plot does not contain any curves """
    pass  # pragma: no cover


class NoSurfacesWarning(IllogicalSedmlWarning):
    """ Warning that a 3D plot does not contain any surfaces """
    pass  # pragma: no cover


class SedmlFeatureNotSupportedWarning(BioSimulatorsWarning):
    """ Warning that a feature of a SED document was skipped because it requires a SED feature that is not
    yet supported. The warning is only used when skipping a portion of a document doesn't affect the semantic
    meaning of the unskipped portions of the document (e.g., skipping generating a plot doesn't adversely
    affect reports).
    """
    pass  # pragma: no cover
