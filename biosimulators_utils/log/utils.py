""" Utilities for working with COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchive  # noqa: F401
from ..combine.utils import get_sedml_contents
from ..sedml.data_model import SedDocument, Task, Output, Report, Plot2D, Plot3D, DataSet, Curve, Surface
from ..sedml.io import SedmlSimulationReader
from ..warnings import warn
from .data_model import (Status, CombineArchiveLog, SedDocumentLog,  # noqa: F401
                         TaskLog, OutputLog, ReportLog, Plot2DLog, Plot3DLog)
from .warnings import StandardOutputNotLoggedWarning
try:
    import capturer
except ModuleNotFoundError:
    capturer = None
import contextlib
import os

__all__ = [
    'init_combine_archive_log',
    'init_sed_document_log',
    'init_task_log',
    'init_output_log',
    'init_report_log',
    'init_plot2d_log',
    'init_plot3d_log',
    'StandardOutputErrorCapturer',
    'get_summary_combine_archive_log',
]


def init_combine_archive_log(archive, archive_dir,
                             supported_features=(SedDocument, Task, Report, Plot2D, Plot3D, DataSet, Curve, Surface),
                             logged_features=(SedDocument, Task, Report, Plot2D, Plot3D, DataSet, Curve, Surface)):
    """ Initialize a log of a COMBINE/OMEX archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dir (:obj:`str`): path where the content of the archive is located
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: COMBINE/OMEX archives and SED documents, tasks, reports, plots,
            data sets, curves, and surfaces.
        logged_features (:obj:`list` of :obj:`type`, optional): list of elements which
            will be logged. Default: COMBINE/OMEX archives and SED documents, tasks, reports, plots,
            data sets, curves, and surfaces.

    Returns:
        :obj:`CombineArchiveLog`: initialized log of a COMBINE/OMEX archive
    """
    contents = get_sedml_contents(archive, include_non_executing_docs=False)

    log = CombineArchiveLog(status=Status.QUEUED)

    if SedDocument in logged_features:
        log.sed_documents = {}
        for content in contents:
            content_filename = os.path.join(archive_dir, content.location)
            doc = SedmlSimulationReader().run(content_filename)

            doc_log = init_sed_document_log(doc, supported_features=supported_features, logged_features=logged_features)
            doc_log.location = os.path.relpath(content.location, '.')
            doc_log.status = Status.QUEUED if isinstance(doc, supported_features) else Status.SKIPPED

            doc_log.parent = log
            doc_id = os.path.relpath(content_filename, archive_dir)
            log.sed_documents[doc_id] = doc_log

    else:
        log.sed_documents = None

    return log


def init_sed_document_log(doc,
                          supported_features=(Task, Report, Plot2D, Plot3D, DataSet, Curve, Surface),
                          logged_features=(Task, Report, Plot2D, Plot3D, DataSet, Curve, Surface)):
    """ Initialize a log of a SED document

    Args:
        doc (:obj:`SedDocument`): SED document
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: tasks, reports, plots, data sets, curves, and surfaces.
        logged_features (:obj:`list` of :obj:`type`, optional): list of SED elements which
            will be logged. Default: tasks, reports, plots, data sets, curves, and surfaces.

    Returns:
        :obj:`SedDocumentLog`: initialized log of a SED document
    """
    log = SedDocumentLog()

    if Task in logged_features:
        log.tasks = {}
        for task in doc.tasks:
            task_log = init_task_log(task, supported_features=supported_features, logged_features=logged_features)
            task_log.status = Status.QUEUED if isinstance(task, supported_features) else Status.SKIPPED
            task_log.parent = log
            log.tasks[task.id] = task_log
    else:
        log.tasks = None

    if set([Output, Report, Plot2D, Plot3D]).intersection(logged_features):
        log.outputs = {}

        for output in doc.outputs:
            if isinstance(output, logged_features):
                output_log = init_output_log(output, supported_features=supported_features, logged_features=logged_features)
                output_log.status = Status.QUEUED if isinstance(output, supported_features) else Status.SKIPPED
                output_log.parent = log
                log.outputs[output.id] = output_log

    else:
        log.outputs = None

    return log


def init_task_log(task,
                  supported_features=(),
                  logged_features=()):
    """ Initialize a log of a task

    Args:
        output (:obj:`Task`): a SED task
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: empty list.
        logged_features (:obj:`list` of :obj:`type`, optional): list of elements which
            will be logged. Default: empty list.

    Returns:
        :obj:`OutputLog`: initialized log of a SED document
    """
    return TaskLog(id=task.id)


def init_output_log(output,
                    supported_features=(DataSet, Curve, Surface),
                    logged_features=(DataSet, Curve, Surface)):
    """ Initialize a log of an output

    Args:
        output (:obj:`Output`): a SED output
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: data sets, curves, and surfaces.
        logged_features (:obj:`list` of :obj:`type`, optional): list of elements which
            will be logged. Default: data sets, curves, and surfaces.

    Returns:
        :obj:`OutputLog`: initialized log of a SED document
    """

    if isinstance(output, Report):
        log = init_report_log(output, supported_features=supported_features, logged_features=logged_features)

    elif isinstance(output, Plot2D):
        log = init_plot2d_log(output, supported_features=supported_features, logged_features=logged_features)

    elif isinstance(output, Plot3D):
        log = init_plot3d_log(output, supported_features=supported_features, logged_features=logged_features)

    else:
        raise NotImplementedError('`{}` outputs are not supported.'.format(
            output.__class__.__name__))  # pragma: no cover # unreachable because all cases are enumerated above

    return log


def init_report_log(report,
                    supported_features=(DataSet, Curve, Surface),
                    logged_features=(DataSet, Curve, Surface)):
    """ Initialize a log of a report

    Args:
        report (:obj:`Report`): a SED report
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: data sets.
        logged_features (:obj:`list` of :obj:`type`, optional): list of elements which
            will be logged. Default: data sets.

    Returns:
        :obj:`ReportLog`: initialized log of a report
    """

    log = ReportLog(id=report.id)

    if DataSet in logged_features:
        log.data_sets = {}
        for data_set in report.data_sets:
            log.data_sets[data_set.id] = (
                Status.QUEUED
                if isinstance(data_set, supported_features)
                else Status.SKIPPED)
    else:
        log.data_sets = None

    return log


def init_plot2d_log(plot,
                    supported_features=(Curve),
                    logged_features=(Curve)):
    """ Initialize a log of a 2D plot

    Args:
        plot (:obj:`Plot2D`): a SED 2D plot
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: curves.
        logged_features (:obj:`list` of :obj:`type`, optional): list of elements which
            will be logged. Default: curves.

    Returns:
        :obj:`Plot2DLog`: initialized log of a 2D plot
    """
    log = Plot2DLog(id=plot.id)

    if Curve in logged_features:
        log.curves = {}
        for curve in plot.curves:
            log.curves[curve.id] = (
                Status.QUEUED
                if isinstance(curve, supported_features)
                else Status.SKIPPED)
    else:
        log.curves = None

    return log


def init_plot3d_log(plot,
                    supported_features=(Surface),
                    logged_features=(Surface)):
    """ Initialize a log of a 3D plot

    Args:
        plot (:obj:`Plot3D`): a SED 3D plot
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported elements.
            Default: surfaces.
        logged_features (:obj:`list` of :obj:`type`, optional): list of elements which
            will be logged. Default: surfaces.

    Returns:
        :obj:`Plot3DLog`: initialized log of a 3D plot
    """
    log = Plot3DLog(id=plot.id)

    if Surface in logged_features:
        log.surfaces = {}
        for surface in plot.surfaces:
            log.surfaces[surface.id] = (
                Status.QUEUED
                if isinstance(surface, supported_features)
                else Status.SKIPPED)
    else:
        log.surfaces = None

    return log


class StandardOutputErrorCapturer(contextlib.AbstractContextManager):
    """ Context manager for capturing standard output/error. When :obj:`capturer` is available (i.e.,
    Linux, MacOS, Unix), :obj:`capturer` is used to capture standard output/error. When :obj:`capturer` is not
    available (i.e. Windows), this context manager issues a warn and collects no output. The purpose of this
    context manager is to encapsulate the handling of whether :obj:`capturer` is or isn't available so
    that the other modules can work seamless in Linux, as well as Windows (except without the ability to log
    standard output/error).

    Attributes:
        disabled (:obj:`bool`): whether to capture standard output and error
        _captured (:obj:`capturer.CaptureOutput`)
    """

    def __init__(self, relay=False, disabled=False):
        """
        Args:
            relay (:obj:`bool`): if :obj:`True`, collect the standard output/error streams and continue to pass
                them along. if :obj:`False`, collect the stream, squash them, and do not pass them along.
            disabled (:obj:`bool`, optional): whether to capture standard output and error
        """
        self.disabled = disabled
        if not self.disabled and capturer:
            self._captured = capturer.CaptureOutput(merged=True, relay=relay)
        else:
            msg = (
                'Standard output and error could not be logged because capturer is not installed. '
                'To install capturer, install BioSimulators utils with the `logging` option '
                '(`pip install biosimulators-utils[logging]`).'
            )
            warn(msg, StandardOutputNotLoggedWarning)

    def __enter__(self):
        """ Enter a context """
        if not self.disabled and capturer:
            self._captured.start_capture()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ Exit a context """
        if not self.disabled and capturer:
            self._captured.finish_capture()

    def get_text(self):
        """ Get the captured standard output/error

        Returns:
            :obj:`str`: captured standard output/error
        """
        if not self.disabled and capturer:
            return self._captured.get_bytes().decode()
        else:
            return None


def get_summary_combine_archive_log(log):
    """ Get a summary of the log of a COMBINE/OMEX archive

    Args:
        log (:obj:`CombineArchiveLog`): log of a COMBINE/OMEX archive

    Returns:
        :obj:`str`: summary of the log
    """
    tasks_logged = False
    outputs_logged = False

    n_archives = 0
    n_tasks = 0
    n_outputs = 0

    sed_doc_status_count = {
        Status.SUCCEEDED: 0,
        Status.SKIPPED: 0,
        Status.FAILED: 0,
        None: 0,
    }
    task_status_count = {
        Status.SUCCEEDED: 0,
        Status.SKIPPED: 0,
        Status.FAILED: 0,
        None: 0,
    }
    output_status_count = {
        Status.SUCCEEDED: 0,
        Status.SKIPPED: 0,
        Status.FAILED: 0,
        None: 0,
    }
    for doc_log in log.sed_documents.values():
        n_archives += 1
        sed_doc_status_count[doc_log.status] += 1
        if doc_log.tasks is not None:
            tasks_logged = True
            for task_log in doc_log.tasks.values():
                n_tasks += 1
                task_status_count[task_log.status if task_log else None] += 1
        if doc_log.outputs is not None:
            outputs_logged = True
            for output_log in doc_log.outputs.values():
                n_outputs += 1
                output_status_count[output_log.status if output_log else None] += 1

    msg = ''
    msg += 'Executed {} SED documents:\n'.format(n_archives)
    msg += '  SED documents ({}):\n'.format(n_archives)
    msg += '    Succeeded: {}\n'.format(sed_doc_status_count[Status.SUCCEEDED])
    msg += '    Skipped: {}\n'.format(sed_doc_status_count[Status.SKIPPED])
    msg += '    Failed: {}\n'.format(sed_doc_status_count[Status.FAILED])

    if tasks_logged:
        msg += '  Tasks ({}):\n'.format(n_tasks)
        msg += '    Succeeded: {}\n'.format(task_status_count[Status.SUCCEEDED])
        msg += '    Skipped: {}\n'.format(task_status_count[Status.SKIPPED])
        msg += '    Failed: {}\n'.format(task_status_count[Status.FAILED])
        if task_status_count[None]:
            msg += '    Unknown: {}\n'.format(task_status_count[None])

    if outputs_logged:
        msg += '  Outputs ({}):\n'.format(n_outputs)
        msg += '    Succeeded: {}\n'.format(output_status_count[Status.SUCCEEDED])
        msg += '    Skipped: {}\n'.format(output_status_count[Status.SKIPPED])
        msg += '    Failed: {}\n'.format(output_status_count[Status.FAILED])
        if output_status_count[None]:
            msg += '    Unknown: {}\n'.format(output_status_count[None])

    return msg
