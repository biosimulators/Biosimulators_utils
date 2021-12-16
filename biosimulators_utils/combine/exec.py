""" Utilities for executing tasks in SED-ML files in COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..archive.io import ArchiveWriter
from ..archive.utils import build_archive_from_paths
from ..config import get_config, Config  # noqa: F401
from ..log.data_model import Status, CombineArchiveLog, StandardOutputErrorCapturerLevel  # noqa: F401
from ..log.utils import init_combine_archive_log, get_summary_combine_archive_log, StandardOutputErrorCapturer
from ..report.data_model import VariableResults, ReportFormat, SedDocumentResults  # noqa: F401
from ..sedml.data_model import (SedDocument, Task, Output, Report, DataSet, Plot2D, Curve,  # noqa: F401
                                Plot3D, Surface, Variable)
from ..utils.core import flatten_nested_list_of_strings
from ..warnings import warn, BioSimulatorsWarning
from .exceptions import CombineArchiveExecutionError, NoSedmlError
from .data_model import CombineArchive
from .io import CombineArchiveReader
from .utils import get_sedml_contents, get_summary_sedml_contents
from .validation import validate
from ..viz.data_model import VizFormat  # noqa: F401
import copy
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
                               sed_doc_executer_logged_features=(Task, Report, DataSet, Plot2D, Curve, Plot3D, Surface),
                               log_level=StandardOutputErrorCapturerLevel.c,
                               config=None):
    """ Execute the SED-ML files in a COMBINE/OMEX archive (execute tasks and save outputs)

    Args:
        sed_doc_executer (:obj:`types.FunctionType`): function to execute each SED document in the archive.
            The function must implement the following interface::

                def sed_doc_executer(doc, working_dir, base_out_path, rel_out_path=None,
                             apply_xml_model_changes=False,
                             log=None, log_level=StandardOutputErrorCapturerLevel.c, indent=0, config=None):
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
                        log (:obj:`SedDocumentLog`, optional): execution status of document
                        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
                        indent (:obj:`int`, optional): degree to indent status messages
                        config (:obj:`Config`, optional): BioSimulators common configuration
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
        sed_doc_executer_logged_features (:obj:`list` of :obj:`type`, optional): list of the types fo elements which that
            the SED document executer logs. Default: tasks, reports, plots, data sets, curves, and surfaces.
        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
        config (:obj:`Config`): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    if not config:
        config = get_config()

    with StandardOutputErrorCapturer(relay=True, level=log_level, disabled=not config.LOG) as archive_captured:
        verbose = config.VERBOSE

        # initialize status and output
        supported_features = sed_doc_executer_supported_features
        logged_features = sed_doc_executer_logged_features

        if SedDocument not in supported_features:
            supported_features = tuple(list(supported_features) + [SedDocument])

        if SedDocument not in logged_features:
            logged_features = tuple(list(logged_features) + [SedDocument])

        start_time = datetime.datetime.now()

        # create output directory
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        # create temporary directory to unpack archive
        archive_tmp_dir = tempfile.mkdtemp()

        try:
            # unpack archive and read metadata
            archive = CombineArchiveReader().run(archive_filename, archive_tmp_dir, config=config)

            # validate archive
            errors, warnings = validate(archive, archive_tmp_dir, config=config)
            if warnings:
                msg = 'The COMBINE/OMEX archive may be invalid.\n  {}'.format(
                    flatten_nested_list_of_strings(warnings).replace('\n', '\n  '))
                warn(msg, BioSimulatorsWarning)

            if errors:
                msg = '`{}` is not a valid COMBINE/OMEX archive.\n  {}'.format(
                    archive_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  '))
                raise ValueError(msg)

            # determine files to execute
            sedml_contents = get_sedml_contents(archive)
            if not sedml_contents:
                msg = "COMBINE/OMEX archive '{}' does not contain any executing SED-ML files".format(archive_filename)
                raise NoSedmlError(msg)

            # print summary of SED documents
            print(get_summary_sedml_contents(archive, archive_tmp_dir, config=config))

        except Exception as exception:
            if config.DEBUG:
                raise
            shutil.rmtree(archive_tmp_dir)

            archive = CombineArchive()
            archive_tmp_dir = None

            if config.LOG:
                log = init_combine_archive_log(archive, archive_tmp_dir,
                                               supported_features=supported_features,
                                               logged_features=logged_features,
                                               config=config)

                log.status = Status.FAILED
                log.out_dir = out_dir
                log.exception = exception
                log.output = archive_captured.get_text()
                log.duration = (datetime.datetime.now() - start_time).total_seconds()
                log.finalize()
                log.export()
            else:
                log = None

            if config.DEBUG:
                raise
            else:
                return (None, log)

        if config.COLLECT_COMBINE_ARCHIVE_RESULTS:
            results = SedDocumentResults()
        else:
            results = None
        if config.LOG:
            log = init_combine_archive_log(archive, archive_tmp_dir,
                                           supported_features=supported_features,
                                           logged_features=logged_features,
                                           config=config)
            log.status = Status.RUNNING
            log.out_dir = out_dir
            log.export()
        else:
            log = None

        # execute SED-ML files: execute tasks and save output
        exceptions = []
        for i_content, content in enumerate(sedml_contents):
            content_filename = os.path.join(archive_tmp_dir, content.location)
            content_id = os.path.relpath(content_filename, archive_tmp_dir)

            print('Executing SED-ML file {}: {} ...'.format(i_content + 1, content_id))

            if config.LOG:
                doc_log = log.sed_documents[content_id]
                doc_log.status = Status.RUNNING
                doc_log.export()
            else:
                doc_log = None

            with StandardOutputErrorCapturer(relay=verbose, level=log_level, disabled=not config.LOG) as doc_captured:
                doc_start_time = datetime.datetime.now()
                if config.COLLECT_COMBINE_ARCHIVE_RESULTS != config.COLLECT_SED_DOCUMENT_RESULTS:
                    config = copy.copy(config)
                    config.COLLECT_SED_DOCUMENT_RESULTS = config.COLLECT_COMBINE_ARCHIVE_RESULTS

                try:
                    working_dir = os.path.dirname(content_filename)
                    doc_results, _ = sed_doc_executer(
                        content_filename,
                        working_dir,
                        out_dir,
                        os.path.relpath(content_filename, archive_tmp_dir),
                        apply_xml_model_changes=apply_xml_model_changes,
                        log=doc_log,
                        log_level=log_level,
                        indent=1,
                        config=config)
                    if config.COLLECT_COMBINE_ARCHIVE_RESULTS:
                        results[content.location] = doc_results
                    if config.LOG:
                        doc_log.status = Status.SUCCEEDED
                except Exception as exception:
                    if config.DEBUG:
                        raise
                    exceptions.append(exception)
                    if config.LOG:
                        doc_log.status = Status.FAILED
                        doc_log.exception = exception

                # update status
                if config.LOG:
                    doc_log.output = doc_captured.get_text()
                    doc_log.duration = (datetime.datetime.now() - doc_start_time).total_seconds()
                    doc_log.export()

        print('')

        if config.BUNDLE_OUTPUTS:
            print('Bundling outputs ...')

            # bundle CSV files of reports into zip archive
            report_formats = config.REPORT_FORMATS
            archive_paths = [os.path.join(out_dir, '**', '*.' + format.value) for format in report_formats if format != ReportFormat.h5]
            archive = build_archive_from_paths(archive_paths, out_dir)
            if archive.files:
                ArchiveWriter().run(archive, os.path.join(out_dir, config.REPORTS_PATH))

            # bundle PDF files of plots into zip archive
            viz_formats = config.VIZ_FORMATS
            archive_paths = [os.path.join(out_dir, '**', '*.' + format.value) for format in viz_formats]
            archive = build_archive_from_paths(archive_paths, out_dir)
            if archive.files:
                ArchiveWriter().run(archive, os.path.join(out_dir, config.PLOTS_PATH))

        # cleanup temporary files
        print('Cleaning up ...')
        if not config.KEEP_INDIVIDUAL_OUTPUTS:

            report_formats = config.REPORT_FORMATS
            viz_formats = config.VIZ_FORMATS
            path_patterns = (
                [os.path.join(out_dir, '**', '*.' + format.value) for format in report_formats if format != ReportFormat.h5]
                + [os.path.join(out_dir, '**', '*.' + format.value) for format in viz_formats]
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
        if config.LOG:
            log.status = Status.FAILED if exceptions else Status.SUCCEEDED
            log.duration = (datetime.datetime.now() - start_time).total_seconds()
            log.finalize()

            # summarize execution
            print('')
            print('============= SUMMARY =============')
            print(get_summary_combine_archive_log(log))

    # update status
    if config.LOG:
        log.output = archive_captured.get_text()
        log.export()

    # raise exceptions
    if exceptions:
        msg = 'The COMBINE/OMEX did not execute successfully:\n\n  {}'.format(
            '\n\n  '.join(str(exceptions).replace('\n', '\n  ') for exceptions in exceptions))
        exception = CombineArchiveExecutionError(msg)

        if config.LOG:
            log.exception = exception
            log.export()

        if config.DEBUG or not config.LOG:
            raise exception

    # flush log
    if config.LOG:
        log.export()

    # return results and log
    return (results, log)
