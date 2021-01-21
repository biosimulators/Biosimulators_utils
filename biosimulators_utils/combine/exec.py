""" Utilities for executing tasks in SED-ML files in COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..archive.io import ArchiveWriter
from ..archive.utils import build_archive_from_paths
from ..config import get_config
from ..log.data_model import Status, CombineArchiveLog  # noqa: F401
from ..log.utils import init_combine_archive_log, get_summary_combine_archive_log
from ..plot.data_model import PlotFormat  # noqa: F401
from ..report.data_model import VariableResults, ReportFormat  # noqa: F401
from ..sedml.data_model import (SedDocument, Task, Output, Report, DataSet, Plot2D, Curve,  # noqa: F401
                                Plot3D, Surface, Variable)
from ..sedml.io import SedmlSimulationReader  # noqa: F401
from ..warnings import warn
from .exceptions import CombineArchiveExecutionError
from .io import CombineArchiveReader
from .utils import get_sedml_contents, get_summary_sedml_contents
from .warnings import NoSedmlWarning
import capturer
import datetime
import glob
import os
import tempfile
import shutil
import types  # noqa: F401

__all__ = [
    'exec_sedml_docs_in_archive',
]


def exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, apply_xml_model_changes=False,
                               sed_doc_executer_supported_features=(Task, Report, DataSet, Plot2D, Curve, Plot3D, Surface),
                               report_formats=None, plot_formats=None,
                               bundle_outputs=None, keep_individual_outputs=None,
                               sed_doc_executer_logged_features=(Task, Report, DataSet, Plot2D, Curve, Plot3D, Surface)):
    """ Execute the SED-ML files in a COMBINE/OMEX archive (execute tasks and save outputs)

    Args:
        sed_doc_executer (:obj:`types.FunctionType`): function to execute each SED document in the archive.
            The function must implement the following interface::

                def sed_doc_executer(doc, working_dir, base_out_path, rel_out_path=None,
                             apply_xml_model_changes=False, report_formats=None, plot_formats=None,
                             log=None, indent=0):
                    ''' Execute the tasks specified in a SED document and generate the specified outputs

                    Args:
                        doc (:obj:`SedDocument` of :obj:`str`): SED document or a path to SED-ML file which defines a SED document
                        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

                        out_path (:obj:`str`): path to store the outputs

                            * CSV: directory in which to save outputs to files
                              ``{out_path}/{rel_out_path}/{report.id}.csv``
                            * HDF5: directory in which to save a single HDF5 file (``{out_path}/reports.h5``),
                              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

                        rel_out_path (:obj:`str`, optional): path relative to :obj:`out_path` to store the outputs
                        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file
                        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
                        plot_formats (:obj:`list` of :obj:`PlotFormat`, optional): plot format (e.g., pdf)
                        log (:obj:`SedDocumentLog`, optional): execution status of document
                        indent (:obj:`int`, optional): degree to indent status messages
                    '''

        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        apply_xml_model_changes (:obj:`bool`): if :obj:`True`, apply any model changes specified in the SED-ML files before
            calling :obj:`task_executer`.
        sed_doc_executer_supported_features (:obj:`list` of :obj:`type`, optional): list of the types of elements that the
            SED document executer supports. Default: tasks, reports, plots, data sets, curves, and surfaces.
        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
        plot_formats (:obj:`list` of :obj:`PlotFormat`, optional): report format (e.g., pdf)
        bundle_outputs (:obj:`bool`, optional): if :obj:`True`, bundle outputs into archives for reports and plots
        keep_individual_outputs (:obj:`bool`, optional): if :obj:`True`, keep individual output files
        sed_doc_executer_logged_features (:obj:`list` of :obj:`type`, optional): list of the types fo elements which that
            the SED document executer logs. Default: tasks, reports, plots, data sets, curves, and surfaces.

    Returns:
        :obj:`CombineArchiveLog`: log
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

    verbose = config.VERBOSE

    # create temporary directory to unpack archive
    archive_tmp_dir = tempfile.mkdtemp()

    # unpack archive and read metadata
    archive = CombineArchiveReader.run(archive_filename, archive_tmp_dir)

    # determine files to execute
    sedml_contents = get_sedml_contents(archive)
    if not sedml_contents:
        warn("COMBINE/OMEX archive '{}' does not contain any executing SED-ML files".format(archive_filename), NoSedmlWarning)

    # print summary of SED documents
    print(get_summary_sedml_contents(archive, archive_tmp_dir))

    # create output directory
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # initialize status and output
    supported_features = sed_doc_executer_supported_features
    logged_features = sed_doc_executer_logged_features

    if SedDocument not in supported_features:
        supported_features = tuple(list(supported_features) + [SedDocument])

    if SedDocument not in logged_features:
        logged_features = tuple(list(logged_features) + [SedDocument])

    log = init_combine_archive_log(archive, archive_tmp_dir,
                                   supported_features=supported_features,
                                   logged_features=logged_features)
    log.status = Status.RUNNING
    log.out_dir = out_dir
    log.export()
    start_time = datetime.datetime.now()

    # execute SED-ML files: execute tasks and save output
    exceptions = []
    for i_content, content in enumerate(sedml_contents):
        content_filename = os.path.join(archive_tmp_dir, content.location)
        content_id = os.path.relpath(content_filename, archive_tmp_dir)

        print('Executing SED-ML file {}: {} ...'.format(i_content, content_id))

        doc_log = log.sed_documents[content_id]
        doc_log.status = Status.RUNNING
        doc_log.export()

        with capturer.CaptureOutput(merged=True, relay=verbose) as captured:
            doc_start_time = datetime.datetime.now()
            try:
                working_dir = os.path.dirname(content_filename)
                sed_doc_executer(content_filename,
                                 working_dir,
                                 out_dir,
                                 os.path.relpath(content_filename, archive_tmp_dir),
                                 apply_xml_model_changes=apply_xml_model_changes,
                                 report_formats=report_formats,
                                 plot_formats=plot_formats,
                                 log=doc_log,
                                 indent=1)
                doc_log.status = Status.SUCCEEDED
            except Exception as exception:
                exceptions.append(exception)
                doc_log.status = Status.FAILED
                doc_log.exception = exception

            # update status
            doc_log.output = captured.get_bytes().decode()
            doc_log.duration = (datetime.datetime.now() - doc_start_time).total_seconds()
            doc_log.export()

    print('')

    if bundle_outputs:
        print('Bundling outputs ...')

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
    print('Cleaning up ...')
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
    log.status = Status.FAILED if exceptions else Status.SUCCEEDED
    log.duration = (datetime.datetime.now() - start_time).total_seconds()
    log.finalize()
    log.export()

    # summarize execution
    print('')
    print('============= SUMMARY =============')
    print(get_summary_combine_archive_log(log))

    # raise exceptions
    if exceptions:
        msg = 'The COMBINE/OMEX did not execute successfully:\n\n  {}'.format(
            '\n\n  '.join(str(exceptions).replace('\n', '\n  ') for exceptions in exceptions))
        raise CombineArchiveExecutionError(msg)

    # return log
    return log
