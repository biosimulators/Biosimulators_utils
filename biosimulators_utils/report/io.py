""" Utilities for reading and writing reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
from ..sedml.data_model import Report  # noqa: F401
from ..sedml.utils import pad_arrays_to_consistent_shapes
from ..sedml.warnings import RepeatDataSetLabelsWarning
from ..warnings import warn
from .data_model import DataSetResults, ReportFormat
import glob
import numpy
import os
import pandas
import tables
import warnings

__all__ = [
    'ReportWriter',
    'ReportReader',
]


class ReportWriter(object):
    """ Class for writing reports of simulation results """

    def run(self, report, results, base_path, rel_path, format=ReportFormat.h5):
        """ Save a report

        Args:
            report (:obj:`Report`): report
            results (:obj:`DataSetResults`): results of the data sets
            base_path (:obj:`str`): path to save results

                * CSV: parent directory to save results
                * HDF5: file to save results

            rel_path (:obj:`str`): path to save results relative to :obj:`base_path`

                * CSV: relative path to :obj:`base_path`
                * HDF5: key within HDF5 file

            format (:obj:`ReportFormat`, optional): report format
        """
        data_set_labels = [data_set.label for data_set in report.data_sets]
        if len(set(data_set_labels)) < len(report.data_sets):
            warn('To facilitate machine interpretation, data sets should have unique ids.',
                 RepeatDataSetLabelsWarning)

        results_list = []
        data_set_labels = []
        for data_set in report.data_sets:
            if data_set.id in results:
                results_list.append(results[data_set.id])
                data_set_labels.append(data_set.label)
        results_list = pad_arrays_to_consistent_shapes(results_list)
        results_df = pandas.DataFrame(numpy.array(results_list), index=data_set_labels)

        if format == ReportFormat.csv:
            filename = os.path.join(base_path, rel_path + '.' + format.value)
            out_dir = os.path.dirname(filename)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            results_df.to_csv(filename,
                              header=False)

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            if not os.path.isdir(base_path):
                os.makedirs(base_path)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", tables.NaturalNameWarning)
                results_df.to_hdf(filename,
                                  key=rel_path,
                                  format='table',
                                  complevel=9,
                                  complib='zlib',
                                  mode='a',
                                  append=False,
                                  )

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))


class ReportReader(object):
    """ Class for reading reports of simulation results """

    def run(self, report, base_path, rel_path, format=ReportFormat.h5):
        """ Read a report for a file

        Args:
            report (:obj:`Report`): report
            base_path (:obj:`str`): path to save results

                * CSV: parent directory to save results
                * HDF5: file to save results

            rel_path (:obj:`str`): path to save results relative to :obj:`base_path`

                * CSV: relative path to :obj:`base_path`
                * HDF5: key within HDF5 file

            format (:obj:`ReportFormat`, optional): report format

        Returns:
            :obj:`DataSetResults`: report results
        """
        if format == ReportFormat.csv:
            filename = os.path.join(base_path, rel_path + '.' + format.value)
            df = pandas.read_csv(filename,
                                 index_col=0,
                                 header=None)
            df.columns = pandas.RangeIndex(start=0, stop=df.shape[1], step=1)

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            df = pandas.read_hdf(filename,
                                 key=rel_path,
                                 )

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))

        results = DataSetResults()

        data_set_labels = [data_set.label for data_set in report.data_sets]
        unreadable_data_sets = []
        if df.index.tolist() == data_set_labels:
            for data_set in report.data_sets:
                results[data_set.id] = df.loc[data_set.label, :]

        else:
            data_set_label_to_index = {}
            for i_data_set, data_set_label in enumerate(df.index):
                if data_set_label not in data_set_label_to_index:
                    data_set_label_to_index[data_set_label] = i_data_set
                else:
                    data_set_label_to_index[data_set_label] = None

            for data_set in report.data_sets:
                i_data_set = data_set_label_to_index.get(data_set.label, None)
                if i_data_set is None:
                    # results[data_set.id] = None
                    unreadable_data_sets.append(data_set.id)
                else:
                    results[data_set.id] = df.loc[data_set.label, :]

        if unreadable_data_sets:
            warn('Some data sets could not be read because their labels are not unique:\n  - {}'.format(
                '\n'.join('`' + id + '`' for id in sorted(unreadable_data_sets))), RepeatDataSetLabelsWarning)

        return results

    def get_ids(self, base_path, format=ReportFormat.h5):
        """ Get the ids of the reports in a file

        Args:
            base_path (:obj:`str`): path to save results

                * CSV: parent directory to save results
                * HDF5: file to save results

            format (:obj:`ReportFormat`, optional): report format

        Returns:
            :obj:`set` of :obj:`str`: ids of reports
        """
        if format == ReportFormat.csv:
            report_ids = set()
            for path in glob.glob(os.path.join(base_path, '**/*.' + format.value), recursive=True):
                report_ids.add(os.path.relpath(path, base_path)[0:-len(format.value)-1])
            return report_ids

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            reports_file = tables.open_file(filename, mode="r")
            report_ids = set()
            for node in reports_file.walk_nodes():
                base_path, _, rel_path = node._v_pathname.rpartition('/')
                if rel_path == 'table':
                    report_ids.add(base_path[1:])
            reports_file.close()
            return report_ids

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))
