""" Utilities for reading and writing reports

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
from ..sedml.data_model import Output, Report, Plot2D, Plot3D  # noqa: F401
from ..utils.core import pad_arrays_to_consistent_shapes
from ..warnings import warn
from .data_model import DataSetResults, ReportFormat
from .warnings import (RepeatDataSetLabelsWarning, MissingReportMetadataWarning, MissingDataWarning,
                       ExtraDataWarning, CannotExportMultidimensionalTableWarning)
import enum
import glob
import h5py
import numpy
import openpyxl
import os
import pandas

__all__ = [
    'ReportWriter',
    'ReportReader',
]


class Hdf5DataSetType(enum.Enum):
    """ Type of data encoded in an HDF5 data set """
    SedReport = Report
    SedPlot2D = Plot2D
    SedPlot3D = Plot3D


class ReportWriter(object):
    """ Class for writing reports of simulation results """

    def run(self, report, results, base_path, rel_path, format=ReportFormat.h5, type=Report):
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
            type (:obj:`type`): type of output (e.g., subclass of :obj:`Output` such as :obj:`Report`, :obj:`Plot2D`)
        """
        results_array = []
        data_set_ids = []
        data_set_labels = []
        data_set_names = []
        data_set_data_types = []
        data_set_shapes = []
        for data_set in report.data_sets:
            if data_set.id in results:
                data_set_result = results[data_set.id]
                results_array.append(data_set_result)
                data_set_ids.append(data_set.id)
                data_set_labels.append(data_set.label)
                data_set_names.append(data_set.name or '')
                if data_set_result is None:
                    data_set_data_types.append('__None__')
                    data_set_shapes.append('')
                else:
                    data_set_data_types.append(data_set_result.dtype.name)
                    data_set_shapes.append(','.join(str(dim_len) for dim_len in data_set_result.shape))
        results_array = pad_arrays_to_consistent_shapes(results_array)
        results_array = numpy.array(results_array)

        if format in [ReportFormat.csv, ReportFormat.tsv, ReportFormat.xlsx]:
            if results_array.ndim > 2:
                msg = 'Report has {} dimensions. Multidimensional reports cannot be exported to {}.'.format(
                    results_array.ndim, format.value.upper())
                warn(msg, CannotExportMultidimensionalTableWarning)
                return

            if len(set(data_set.label for data_set in report.data_sets)) < len(report.data_sets):
                warn('To facilitate machine interpretation, data sets should have unique labels.',
                     RepeatDataSetLabelsWarning)

            msg = 'Reports exported to {} do not contain information about the data type or size of each data set.'.format(
                format.value.upper())
            warn(msg, MissingReportMetadataWarning)

            results_df = pandas.DataFrame(results_array, index=data_set_labels)

            if format in [ReportFormat.csv, ReportFormat.tsv]:
                filename = os.path.join(base_path, rel_path + '.' + format.value)
                out_dir = os.path.dirname(filename)
                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                results_df.to_csv(filename, header=False, sep=',' if format == ReportFormat.csv else '\t')
            else:
                filename = os.path.join(base_path, os.path.dirname(rel_path) + '.' + format.value)
                out_dir = os.path.dirname(filename)
                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                with pandas.ExcelWriter(filename, mode='a' if os.path.isfile(filename) else 'w', engine='openpyxl') as writer:
                    results_df.to_excel(writer, sheet_name=os.path.basename(rel_path), header=False)

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            if not os.path.isdir(base_path):
                os.makedirs(base_path)

            with h5py.File(filename, 'a') as file:
                try:
                    file[rel_path]
                    del file[rel_path]
                except KeyError:
                    pass

                data_set = file.create_dataset(rel_path, data=results_array,
                                               chunks=True, compression="gzip", compression_opts=9)
                data_set.attrs['_type'] = Hdf5DataSetType(type).name
                if report.id:
                    data_set.attrs['id'] = report.id
                if report.name:
                    data_set.attrs['name'] = report.name
                data_set.attrs['dataSetIds'] = data_set_ids
                data_set.attrs['dataSetNames'] = data_set_names
                data_set.attrs['dataSetLabels'] = data_set_labels
                data_set.attrs['dataSetDataTypes'] = data_set_data_types
                data_set.attrs['dataSetShapes'] = data_set_shapes

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
        if format in [ReportFormat.csv, ReportFormat.tsv, ReportFormat.xlsx]:
            warn('Reports exported to {} do not contain information about the data type or size of each data set.'.format(
                format.value.upper()), MissingReportMetadataWarning)

            if format in [ReportFormat.csv, ReportFormat.tsv]:
                filename = os.path.join(base_path, rel_path + '.' + format.value)
                df = pandas.read_csv(filename,
                                     index_col=0,
                                     header=None,
                                     sep=',' if format == ReportFormat.csv else '\t')
            else:
                filename = os.path.join(base_path, os.path.dirname(rel_path) + '.' + format.value)
                df = pandas.read_excel(filename,
                                       sheet_name=os.path.basename(rel_path),
                                       index_col=0,
                                       header=None,
                                       engine='openpyxl')
            df.columns = pandas.RangeIndex(start=0, stop=df.shape[1], step=1)

            results = DataSetResults()

            data_set_labels = [data_set.label for data_set in report.data_sets]
            if df.index.tolist() == data_set_labels:
                data = df.to_numpy()
                for i_data_set, data_set in enumerate(report.data_sets):
                    results[data_set.id] = data[i_data_set, :]
                extra_data_sets = set()

            else:
                data_set_label_to_index = {}
                for i_data_set, data_set_label in enumerate(df.index):
                    if data_set_label not in data_set_label_to_index:
                        data_set_label_to_index[data_set_label] = i_data_set
                    else:
                        data_set_label_to_index[data_set_label] = None

                unreadable_data_sets = []
                for data_set in report.data_sets:
                    i_data_set = data_set_label_to_index.get(data_set.label, None)
                    if i_data_set is None:
                        # results[data_set.id] = None
                        unreadable_data_sets.append(data_set.id)
                    else:
                        results[data_set.id] = df.loc[data_set.label, :].to_numpy()

                if unreadable_data_sets:
                    warn('Some data sets could not be read because their labels are not unique:\n  - {}'.format(
                        '\n'.join('`' + id + '`' for id in sorted(unreadable_data_sets))), RepeatDataSetLabelsWarning)

                data_set_id_to_label = {data_set.id: data_set.label for data_set in report.data_sets}
                extra_data_sets = set(df.index) - set(data_set_id_to_label[id] for id in results.keys()) - set(unreadable_data_sets)

            file_data_set_ids = set(results.keys()) | extra_data_sets

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)

            with h5py.File(filename, 'r') as file:
                data_set = file[rel_path]
                data_set_results = data_set[:]
                file_data_set_ids = data_set.attrs['dataSetIds']
                data_set_data_types = data_set.attrs['dataSetDataTypes']
                data_set_shapes = []
                for data_set_shape in data_set.attrs['dataSetShapes']:
                    if data_set_shape:
                        data_set_shapes.append([int(dim_len) for dim_len in data_set_shape.split(',')])
                    else:
                        data_set_shapes.append([])

            results = DataSetResults()
            data_set_id_to_index = {data_set_id: i_data_set for i_data_set, data_set_id in enumerate(file_data_set_ids)}

            data_set_ndim = data_set_results.ndim - 1
            for data_set in report.data_sets:
                i_data_set = data_set_id_to_index.get(data_set.id, None)
                if i_data_set is not None:
                    data_set_data_type = data_set_data_types[i_data_set]
                    if data_set_data_type == '__None__':
                        results[data_set.id] = None
                    else:
                        data_set_shape = data_set_shapes[i_data_set]
                        data_set_slice = [slice(0, dim_len) for dim_len in data_set_shape] + \
                            [slice(0, 1)] * (data_set_ndim - len(data_set_shape))
                        results[data_set.id] = (
                            data_set_results[i_data_set][data_set_slice]
                            .reshape(data_set_shape)
                            .astype(data_set_data_type)
                        )

            file_data_set_ids = set(file_data_set_ids)

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))

        report_data_set_ids = set(data_set.id for data_set in report.data_sets)
        missing_data_set_ids = report_data_set_ids.difference(file_data_set_ids)
        extra_data_set_ids = file_data_set_ids.difference(report_data_set_ids)

        if missing_data_set_ids:
            warn('File does not contain data for the following data sets of the report:\n  - {}'.format(
                '\n'.join('`' + id + '`' for id in sorted(missing_data_set_ids))), MissingDataWarning)

        if extra_data_set_ids:
            warn('File contains additional data that could not be mapped to data sets of the report:\n  - {}'.format(
                '\n'.join('`' + id + '`' for id in sorted(extra_data_set_ids))), ExtraDataWarning)

        return results

    def get_ids(self, base_path, format=ReportFormat.h5, type=Output):
        """ Get the ids of the reports in a file

        Args:
            base_path (:obj:`str`): path to save results

                * CSV: parent directory to save results
                * HDF5: file to save results

            format (:obj:`ReportFormat`, optional): report format
            type (:obj:`type`): type of report to get

        Returns:
            :obj:`list` of :obj:`str`: ids of reports
        """
        if format in [ReportFormat.csv, ReportFormat.tsv]:
            report_ids = []
            for path in glob.glob(os.path.join(base_path, '**/*.' + format.value), recursive=True):
                report_ids.append(os.path.relpath(path, base_path)[0:-len(format.value)-1])
            return report_ids

        elif format == ReportFormat.xlsx:
            report_ids = []
            for path in glob.glob(os.path.join(base_path, '**/*.' + format.value), recursive=True):
                wb = openpyxl.load_workbook(path)
                for sheet_name in wb.get_sheet_names():
                    report_ids.append(os.path.join(os.path.relpath(path, base_path)[0:-len(format.value)-1], sheet_name))
            return report_ids

        elif format == ReportFormat.h5:
            filename = os.path.join(base_path, get_config().H5_REPORTS_PATH)
            with h5py.File(filename, 'r') as file:
                report_ids = []

                def append_report_id(name, object, type=type):
                    if isinstance(object, h5py.Dataset):
                        data_set_type = object.attrs.get('_type', None)
                        if data_set_type and (Hdf5DataSetType[data_set_type].value == type or issubclass(Hdf5DataSetType[data_set_type].value, type)):
                            report_ids.append(name)

                file.visititems(append_report_id)

            return report_ids

        else:
            raise NotImplementedError('Report format {} is not supported'.format(format))
