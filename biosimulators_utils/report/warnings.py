""" Warnings for reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-01-21
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import BioSimulatorsWarning

__all__ = [
    'RepeatDataSetLabelsWarning',
    'MissingReportMetadataWarning',
    'MissingDataWarning',
    'ExtraDataWarning',
    'CannotExportMultidimensionalTableWarning',
]


class RepeatDataSetLabelsWarning(BioSimulatorsWarning):
    """ Warning that multiple data sets with a report have the same label """
    pass  # pragma: no cover


class MissingReportMetadataWarning(BioSimulatorsWarning):
    """ Warning that an exported file of a report will not or does contain comprehensive metadata about the report
    such as the data type and shape of each data set.
    """
    pass  # pragma: no cover


class MissingDataWarning(BioSimulatorsWarning):
    """ Warning that a file does not contain data for one or more data sets of a report. """
    pass  # pragma: no cover


class ExtraDataWarning(BioSimulatorsWarning):
    """ Warning that a file contains additional data that could not be mapped to a data set of a report. """
    pass  # pragma: no cover


class CannotExportMultidimensionalTableWarning(BioSimulatorsWarning):
    """ Warning that a multidimensional report cannot be exported (e.g., to CSV, Excel, or TSV). """
    pass  # pragma: no cover
