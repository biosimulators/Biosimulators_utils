""" Utilities for executing tasks in SED-ML files in COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..archive.io import ArchiveWriter
from ..archive.utils import build_archive_from_paths
from ..config import get_config
from ..exec_status.data_model import ExecutionStatus
from ..exec_status.utils import init_combine_archive_exec_status
from ..plot.data_model import PlotFormat  # noqa: F401
from ..report.data_model import DataGeneratorVariableResults, OutputResults, ReportFormat  # noqa: F401
from ..sedml.data_model import Task, DataGeneratorVariable  # noqa: F401
from ..sedml.io import SedmlSimulationReader  # noqa: F401
from .io import CombineArchiveReader
from .utils import get_sedml_contents, get_summary_sedml_contents
from .warnings import NoSedmlWarning
import biosimulators_utils.sedml.exec
import glob
import os
import tempfile
import shutil
import types  # noqa: F401
import warnings

__all__ = [
    'exec_sedml_docs_in_archive',
]


def exec_sedml_docs_in_archive(archive_filename, sed_task_executer, out_dir, apply_xml_model_changes=False,
                               report_formats=None, plot_formats=None,
                               bundle_outputs=None, keep_individual_outputs=None):
    """ Execute the SED-ML files in a COMBINE/OMEX archive (execute tasks and save outputs)

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        sed_task_executer (:obj:`types.FunctionType`): function to execute each SED task in each SED-ML file in the archive.
            The function must implement the following interface::

                def exec_task(task, variables):
                    ''' Execute a simulation and return its results

                    Args:
                       task (:obj:`Task`): task
                       variables (:obj:`list` of :obj:`DataGeneratorVariable`): variables that should be recorded

                    Returns:
                       :obj:`DataGeneratorVariableResults`: results of variables
                    '''
                    pass

        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        apply_xml_model_changes (:obj:`bool`): if :obj:`True`, apply any model changes specified in the SED-ML files before
            calling :obj:`task_executer`.
        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
        plot_formats (:obj:`list` of :obj:`PlotFormat`, optional): report format (e.g., pdf)
        bundle_outputs (:obj:`bool`, optional): if :obj:`True`, bundle outputs into archives for reports and plots
        keep_individual_outputs (:obj:`bool`, optional): if :obj:`True`, keep individual output files
    """
    config = get_config()

    # process arguments
    if report_formats is None:
        report_formats = [ReportFormat(format_value) for format_value in config.REPORT_FORMATS]

    if plot_formats is None:
        plot_formats = [PlotFormat(format_value) for format_value in config.PLOT_FORMATS]

    if bundle_outputs is None:
        bundle_outputs = config.BUNDLE_OUTPUTS

    if keep_individual_outputs is None:
        keep_individual_outputs = config.KEEP_INDIVIDUAL_OUTPUTS

    # create temporary directory to unpack archive
    archive_tmp_dir = tempfile.mkdtemp()

    # unpack archive and read metadata
    archive = CombineArchiveReader.run(archive_filename, archive_tmp_dir)

    # determine files to execute
    sedml_contents = get_sedml_contents(archive)
    if not sedml_contents:
        warnings.warn("COMBINE/OMEX archive '{}' does not contain any executing SED-ML files".format(archive_filename), NoSedmlWarning)

    # print summary of SED documents
    print(get_summary_sedml_contents(archive, archive_tmp_dir))

    # create output directory
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # initialize status and output
    exec_status = init_combine_archive_exec_status(archive, archive_tmp_dir)
    exec_status.status = ExecutionStatus.RUNNING
    exec_status.out_dir = out_dir
    exec_status.export()

    # execute SED-ML files: execute tasks and save output
    for i_content, content in enumerate(sedml_contents):
        content_filename = os.path.join(archive_tmp_dir, content.location)
        content_id = os.path.relpath(content_filename, archive_tmp_dir)

        print('Executing SED-ML file {}: {}'.format(i_content, content_id))

        working_dir = os.path.dirname(content_filename)
        biosimulators_utils.sedml.exec.exec_doc(content_filename,
                                                working_dir,
                                                sed_task_executer,
                                                out_dir,
                                                os.path.relpath(content_filename, archive_tmp_dir),
                                                apply_xml_model_changes=apply_xml_model_changes,
                                                report_formats=report_formats,
                                                plot_formats=plot_formats,
                                                exec_status=exec_status.sed_documents[content_id],
                                                indent=1)

    if bundle_outputs:
        # bundle CSV files of reports into zip archive
        archive_paths = [os.path.join(out_dir, '**', '*.' + format.value) for format in report_formats if format != ReportFormat.h5]
        archive = build_archive_from_paths(archive_paths, out_dir)
        if archive.files:
            ArchiveWriter().run(archive, os.path.join(out_dir, config.REPORTS_PATH))

        # bundle PDF files of plots into zip archive
        archive_paths = [os.path.join(out_dir, '**', '*.' + format.value) for format in plot_formats]
        archive = build_archive_from_paths(archive_paths, out_dir)
        if archive.files:
            ArchiveWriter().run(archive, os.path.join(out_dir, config.PLOTS_PATH))

    # cleanup temporary files
    if not keep_individual_outputs:
        path_patterns = (
            [os.path.join(out_dir, '**', '*.' + format.value) for format in report_formats if format != ReportFormat.h5]
            + [os.path.join(out_dir, '**', '*.' + format.value) for format in plot_formats]
        )
        for path_pattern in path_patterns:
            for path in glob.glob(path_pattern, recursive=True):
                os.remove(path)

        for dir_path, dir_names, file_names in os.walk(out_dir, topdown=False):
            for dir_name in list(dir_names):
                full_dir_name = os.path.join(dir_path, dir_name)
                if not os.path.isdir(full_dir_name):
                    dir_names.remove(dir_name)
                elif not os.listdir(full_dir_name):
                    # not reachable because directory would
                    # have already been removed by the iteration for the directory
                    shutil.rmtree(full_dir_name)  # pragma: no cover
                    dir_names.remove(dir_name)  # pragma: no cover
            if not dir_names and not file_names:
                shutil.rmtree(dir_path)

    shutil.rmtree(archive_tmp_dir)

    # update status
    exec_status.status = ExecutionStatus.SUCCEEDED
    exec_status.finalize()
    exec_status.export()
