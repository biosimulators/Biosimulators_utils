""" Utilities for reading and writing reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ReportFormat
import os
import pandas

__all__ = [
    'ReportWriter',
    'ReportReader',
]


class ReportWriter(object):
    """ Class for writing reports of simulation results """

    def run(self, results, base_path, rel_path, format=ReportFormat.CSV):
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

        if format == ReportFormat.CSV:
            filename = os.path.join(base_path, rel_path + '.csv')
            out_dir = os.path.dirname(filename)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            results.to_csv(filename,
                           header=False)

        elif format == ReportFormat.HDF5:
            filename = os.path.join(base_path, 'reports.h5')
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

    def run(self, base_path, rel_path, format=ReportFormat.CSV):
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
        if format == ReportFormat.CSV:
            filename = os.path.join(base_path, rel_path + '.csv')
            df = pandas.read_csv(filename,
                                 index_col=0,
                                 header=None)
            df.columns = pandas.RangeIndex(start=0, stop=df.shape[1], step=1)
            return df

        elif format == ReportFormat.HDF5:
            filename = os.path.join(base_path, 'reports.h5')
            return pandas.read_hdf(filename,
                                   key=rel_path,
                                   )

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))