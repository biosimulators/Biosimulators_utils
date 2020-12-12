""" Data model for reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum


__all__ = ['DataGeneratorVariableResults', 'OutputResults', 'ReportFormat']


class DataGeneratorVariableResults(dict):
    """ Dictionary that maps the ids of variables (:obj:`DataGeneratorVariable`) to their results (:obj:`numpy.ndarray`)

    * Keys (:obj:`str`): ids of variables (:obj:`DataGeneratorVariable`)
    * Values (:obj:`numpy.ndarray`): result of each variable

        * Steady-state tasks of non-spatial models: results should be arrays of shape ``(1,)``
        * One-step tasks of non-spatial models: results should be arrays of shape ``(2,)``
        * Uniform time course tasks of non-spatial models: results should be arrays of shape ``(number_of_points + 1,)``
    """
    pass


class OutputResults(dict):
    """ Dictionary that maps the ids of outputs (e.g., :obj:`Report`) to their results (:obj:`pandas.DataFrame`)

    * Keys (:obj:`str`): ids of outputs (e.g., :obj:`Report`)
    * Values (:obj:`pandas.DataFrame`): result of each output

        * Data:

            * Steady-state tasks of non-spatial models: results should be arrays of shape ``(number of data sets, 1)``
            * One-step tasks of non-spatial models: results should be arrays of shape ``(number of data sets, 2)``
            * Uniform time course tasks of non-spatial models: results should be arrays of shape ``(number of data sets, number_of_points + 1)``

        * Indices (row labels)

            * Reports: equal to the ids of the data sets if each report
    """
    pass


class ReportFormat(str, enum.Enum):
    """ Format of a report """
    csv = 'csv'
    h5 = 'h5'
    hdf = 'h5'
    hdf5 = 'h5'
