""" Data model for reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum


__all__ = [
    'VariableResults',
    'DataGeneratorResults',
    'DataSetResults',
    'ReportResults',
    'ReportFormat',
    'SedDocumentResults',
]


class VariableResults(dict):
    """ Dictionary that maps the ids of variables (:obj:`Variable`) to their results (:obj:`numpy.ndarray`)

    * Keys (:obj:`str`): ids of variables (:obj:`Variable`)
    * Values (:obj:`numpy.ndarray`): result of each variable

        * Steady-state tasks of non-spatial models: results should be arrays of shape ``(1,)``
        * One-step tasks of non-spatial models: results should be arrays of shape ``(2,)``
        * Uniform time course tasks of non-spatial models: results should be arrays of shape ``(number_of_steps + 1,)``
    """
    pass


class DataGeneratorResults(dict):
    """ Dictionary that maps the ids of data generators (:obj:`DataGenerator`) to their results (:obj:`numpy.ndarray`)

    * Keys (:obj:`str`): ids of data generators (:obj:`DataGenerator`)
    * Values (:obj:`numpy.ndarray`): result of each variable

        * Steady-state tasks of non-spatial models: results should be arrays of shape ``(1,)``
        * One-step tasks of non-spatial models: results should be arrays of shape ``(2,)``
        * Uniform time course tasks of non-spatial models: results should be arrays of shape ``(number_of_steps + 1,)``
    """
    pass


class DataSetResults(dict):
    """ Dictionary that maps the ids of data sets to their results (:obj:`numpy.ndarray`)

    * Keys (:obj:`str`): ids of data sets
    * Values (:obj:`numpy.ndarray`): result of each data set

        * Steady-state tasks of non-spatial models: results should be arrays of shape ``(number of data sets, 1)``
        * One-step tasks of non-spatial models: results should be arrays of shape ``(number of data sets, 2)``
        * Uniform time course tasks of non-spatial models: results should be arrays of shape ``(number_of_steps + 1,)``
    """
    pass


class ReportResults(dict):
    """ Dictionary that maps the ids of reports (e.g., :obj:`Report`) to their results (:obj:`DataSetResults`)

    * Keys (:obj:`str`): ids of reports (e.g., :obj:`Report`)
    * Values (:obj:`DataSetResults`): result of each report
    """
    pass


class ReportFormat(str, enum.Enum):
    """ Format of a report """
    csv = 'csv'
    h5 = 'h5'
    hdf = 'h5'
    hdf5 = 'h5'
    tsv = 'tsv'
    xlsx = 'xlsx'


class SedDocumentResults(dict):
    """ Dictionary that maps the locations of SED-ML documents (e.g., :obj:`SedDocument`) to their results (:obj:`ReportResults`)

    * Keys (:obj:`str`): locations of SED documents (e.g., :obj:`SedDocument`)
    * Values (:obj:`ReportResults`): result of each document
    """
    pass
