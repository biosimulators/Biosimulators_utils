""" Utilities for reading and writing reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
from .data_model import ReportFormat
import glob
import os
import pandas
import tables

__all__ = [
    'ReportWriter',
    'ReportReader',
]


class ReportWriter(object):
    """ Class for writing reports of simulation results """

    def run(self, results, base_path, rel_path, format=ReportFormat.h5):
        """ Save a report

        Args:
            results (:obj:`pandas.DataFrame`): report results
            base_path (:obj:`str`): path to save results

                * CSV: parent directory to save results
                * HDF5: file to save results

            rel_path (:obj:`str`): path to save results relative to :obj:`base_path`

                * CSV: relative path to :obj:`base_path`
                * HDF5: key within HDF5 file

            format (:obj:`ReportFormat`, optional): report format
        """

        if format == ReportFormat.csv:
            filename = os.path.join(base_path, rel_path + '.' + format.value)
            out_dir = os.path.dirname(filename)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            results.to_csv(filename,
                           header=False)

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            if not os.path.isdir(base_path):
                os.makedirs(base_path)
            results.to_hdf(filename,
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

    def run(self, base_path, rel_path, format=ReportFormat.h5):
        """ Read a report for a file

        Args:
            base_path (:obj:`str`): path to save results

                * CSV: parent directory to save results
                * HDF5: file to save results

            rel_path (:obj:`str`): path to save results relative to :obj:`base_path`

                * CSV: relative path to :obj:`base_path`
                * HDF5: key within HDF5 file

            format (:obj:`ReportFormat`, optional): report format

        Returns:
            :obj:`pandas.DataFrame`: report results
        """
        if format == ReportFormat.csv:
            filename = os.path.join(base_path, rel_path + '.' + format.value)
            df = pandas.read_csv(filename,
                                 index_col=0,
                                 header=None)
            df.columns = pandas.RangeIndex(start=0, stop=df.shape[1], step=1)
            return df

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            return pandas.read_hdf(filename,
                                   key=rel_path,
                                   )

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))

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
