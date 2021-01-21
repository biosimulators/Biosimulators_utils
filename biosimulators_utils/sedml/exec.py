""" Utilities for executing tasks in SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config, Colors
from ..log.data_model import Status, SedDocumentLog, TaskLog, ReportLog, Plot2DLog, Plot3DLog  # noqa: F401
from ..log.utils import init_sed_document_log
from ..plot.data_model import PlotFormat
from ..plot.io import write_plot_2d, write_plot_3d
from ..report.data_model import VariableResults, DataSetResults, ReportResults, ReportFormat  # noqa: F401
from ..report.io import ReportWriter
from ..warnings import warn
from .data_model import SedDocument, Task, Report, Plot2D, Plot3D
from .exceptions import SedmlExecutionError
from .io import SedmlSimulationReader
from .utils import resolve_model_and_apply_xml_changes, get_variables_for_task, calc_data_generators_results
from .warnings import NoTasksWarning, NoOutputsWarning
import capturer
import copy
import datetime
import os
import sys
import termcolor
import types  # noqa: F401


__all__ = [
    'exec_sed_doc',
]


def exec_sed_doc(task_executer, doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=False, report_formats=None, plot_formats=None,
                 log=None, indent=0, pretty_print_modified_xml_models=False):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        task_executer (:obj:`types.FunctionType`): function to execute each task in the SED-ML file.
            The function must implement the following interface::

                def exec_task(task, variables, log=None):
                    ''' Execute a simulation and return its results

                    Args:
                       task (:obj:`Task`): task
                       variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
                       log (:obj:`TaskLog`, optional): log for the task

                    Returns:
                       :obj:`VariableResults`: results of variables
                    '''
                    pass

        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
        plot_formats (:obj:`list` of :obj:`PlotFormat`, optional): plot format (e.g., pdf)
        log (:obj:`SedDocumentLog`, optional): log of the document
        indent (:obj:`int`, optional): degree to indent status messages
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models

    Returns:
        :obj:`tuple`:

            * :obj:`ReportResults`: results of each report
            * :obj:`SedDocumentLog`: log of the document
    """
    config = get_config()

    # process arguments
    if not isinstance(doc, SedDocument):
        doc = SedmlSimulationReader().run(doc)
    else:
        doc = copy.deepcopy(doc)

    if report_formats is None:
        report_formats = [ReportFormat(format_value) for format_value in config.REPORT_FORMATS]

    if plot_formats is None:
        plot_formats = [PlotFormat(format_value) for format_value in config.PLOT_FORMATS]

    log = log or init_sed_document_log(doc)

    verbose = config.VERBOSE

    # update status
    exceptions = []

    # execute tasks
    if not doc.tasks:
        warn('SED document does not describe any tasks.', NoTasksWarning)

    # TODO: initialize reports with their eventual shapes; this requires individual simulation tools to pass
    # information about the shape of their output to this method
    variable_results = VariableResults()
    report_results = ReportResults()

    doc.tasks.sort(key=lambda task: task.id)
    print('{}Found {} tasks and {} outputs:\n{}Tasks:\n{}{}\n{}Outputs:\n{}{}'.format(
        ' ' * 2 * indent,
        len(doc.tasks),
        len(doc.outputs),
        ' ' * 2 * (indent + 1),
        ' ' * 2 * (indent + 2),
        ('\n' + ' ' * 2 * (indent + 2)).join(['`' + task.id + '`' for task in doc.tasks]),
        ' ' * 2 * (indent + 1),
        ' ' * 2 * (indent + 2),
        ('\n' + ' ' * 2 * (indent + 2)).join(['`' + output.id + '`' for output in doc.outputs]),
    ))
    for i_task, task in enumerate(doc.tasks):
        print('{}Executing task {}: `{}`'.format(' ' * 2 * indent, i_task + 1, task.id))

        task_log = log.tasks[task.id]
        task_log.status = Status.RUNNING
        task_log.export()

        # Execute task
        print('{}Executing simulation ...'.format(' ' * 2 * (indent + 1)), end='')
        sys.stdout.flush()
        with capturer.CaptureOutput(merged=True, relay=verbose) as captured:
            start_time = datetime.datetime.now()
            try:
                if isinstance(task, Task):
                    # get model and apply changes
                    original_model = task.model
                    task.model, temp_model_source, _ = resolve_model_and_apply_xml_changes(
                        task.model, doc, working_dir,
                        apply_xml_model_changes=apply_xml_model_changes,
                        pretty_print_modified_xml_models=pretty_print_modified_xml_models)

                    # get a list of the variables that the task needs to record
                    task_vars = get_variables_for_task(doc, task)

                    # execute task
                    task_variable_results, _ = task_executer(task, task_vars, log=task_log)

                    # check that the expected variables were recorded
                    missing_vars = []
                    for var in task_vars:
                        variable_results[var.id] = task_variable_results.get(var.id, None)
                        if variable_results[var.id] is None:
                            missing_vars.append(var.id)
                    if missing_vars:
                        msg = 'Task `{}` did not generate the following expected variables:\n  - {}'.format(
                            task.id, '\n  - '.join('`' + var + '`' for var in sorted(missing_vars)))
                        raise ValueError(msg)

                    # cleanup modified model source
                    if temp_model_source:
                        os.remove(temp_model_source)
                    task.model = original_model

                else:
                    raise NotImplementedError('Tasks of type {} are not supported.'.format(task.__class__.__name__))

                task_status = Status.SUCCEEDED
                task_exception = None
            except Exception as exception:
                exceptions.append(exception)
                task_status = Status.FAILED
                task_exception = exception

        if task_log:
            task_log.status = task_status
            task_log.exception = task_exception
            task_log.output = captured.get_bytes().decode()
            task_log.duration = (datetime.datetime.now() - start_time).total_seconds()
            task_log.export()
        print(' ' + termcolor.colored(task_status.value.lower(), Colors[task_status.value.lower()].value))

        # generate outputs
        print('{}Generating {} outputs ...'.format(' ' * 2 * (indent + 1), len(doc.outputs)))
        task_contributes_to_output = False
        for i_output, output in enumerate(doc.outputs):
            print('{}Generating output {}: `{}` ...'.format(' ' * 2 * (indent + 2), i_output + 1, output.id), end='')
            sys.stdout.flush()
            start_time = datetime.datetime.now()
            with capturer.CaptureOutput(merged=True, relay=verbose) as captured:
                try:
                    if log.outputs[output.id].status == Status.SUCCEEDED:
                        continue

                    if isinstance(output, Report):
                        report_results[output.id], output_status, output_exception, task_contributes_to_report = exec_report(
                            output, variable_results,
                            base_out_path, rel_out_path, report_formats,
                            task,
                            log.outputs[output.id])
                        task_contributes_to_output = task_contributes_to_output or task_contributes_to_report

                    elif isinstance(output, Plot2D):
                        output_status, output_exception, task_contributes_to_plot = exec_plot_2d(
                            output, variable_results,
                            base_out_path, rel_out_path, plot_formats,
                            task,
                            log.outputs[output.id])
                        task_contributes_to_output = task_contributes_to_output or task_contributes_to_plot

                    elif isinstance(output, Plot3D):
                        output_status, output_exception, task_contributes_to_plot = exec_plot_3d(
                            output, variable_results,
                            base_out_path, rel_out_path, plot_formats,
                            task,
                            log.outputs[output.id])
                        task_contributes_to_output = task_contributes_to_output or task_contributes_to_plot

                    else:
                        # unreachable because the above cases cover all types of outputs
                        raise NotImplementedError('Outputs of type {} are not supported.'.format(output.__class__.__name__))

                except Exception as exception:
                    output_status = Status.FAILED
                    output_exception = exception

            log.outputs[output.id].status = output_status
            log.outputs[output.id].exception = output_exception
            log.outputs[output.id].output = captured.get_bytes().decode()
            log.outputs[output.id].duration = (datetime.datetime.now() - start_time).total_seconds()
            log.outputs[output.id].export()

            if output_exception:
                exceptions.append(output_exception)

            print(' ' + termcolor.colored(output_status.value.lower(), Colors[output_status.value.lower()].value))

        if not task_contributes_to_output:
            warn('Task {} does not contribute to any outputs.'.format(task.id), NoOutputsWarning)

    # finalize the status of the outputs
    for output_log in log.outputs.values():
        output_log.finalize()

    # summarize execution
    task_status_count = {
        Status.SUCCEEDED: 0,
        Status.SKIPPED: 0,
        Status.FAILED: 0,
    }
    for task_log in log.tasks.values():
        task_status_count[task_log.status] += 1

    output_status_count = {
        Status.SUCCEEDED: 0,
        Status.SKIPPED: 0,
        Status.FAILED: 0,
    }
    for output_log in log.outputs.values():
        output_status_count[output_log.status] += 1

    print('')
    print('{}Executed {} tasks and {} outputs:'.format(' ' * 2 * indent, len(doc.tasks), len(doc.outputs)))
    print('{}  Tasks:'.format(' ' * 2 * indent))
    print('{}    Succeeded: {}'.format(' ' * 2 * indent, task_status_count[Status.SUCCEEDED]))
    print('{}    Skipped: {}'.format(' ' * 2 * indent, task_status_count[Status.SKIPPED]))
    print('{}    Failed: {}'.format(' ' * 2 * indent, task_status_count[Status.FAILED]))
    print('{}  Outputs:'.format(' ' * 2 * indent))
    print('{}    Succeeded: {}'.format(' ' * 2 * indent, output_status_count[Status.SUCCEEDED]))
    print('{}    Skipped: {}'.format(' ' * 2 * indent, output_status_count[Status.SKIPPED]))
    print('{}    Failed: {}'.format(' ' * 2 * indent, output_status_count[Status.FAILED]))

    # raise exceptions
    if exceptions:
        msg = 'The SED document did not execute successfully:\n\n  {}'.format(
            '\n\n  '.join(str(exceptions).replace('\n', '\n  ') for exceptions in exceptions))
        raise SedmlExecutionError(msg)

    # return the results of the reports
    return report_results, log


def exec_report(report, variable_results, base_out_path, rel_out_path, formats, task, log):
    """ Execute a report, generating the data sets which are available

    Args:
        report (:obj:`Report`): report
        variable_results (:obj:`VariableResults`): result of each data generator
        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
        task (:obj:`Task`): task
        log (:obj:`ReportLog`, optional): log of report

    Returns:
        :obj:`tuple`:

            * :obj:`DataSetResults`: report
            * :obj:`Status`: status
            * :obj:`Exception`: exception for failure
            * :obj:`bool`: whether :obj:`task` contribute a variable to the report
    """
    # calculate data generators
    data_generators = set()
    for data_set in report.data_sets:
        data_generators.add(data_set.data_generator)

    data_gen_results, data_gen_statuses, data_gen_exceptions, task_contributes_to_report = calc_data_generators_results(
        data_generators, variable_results, report, task, make_shapes_consistent=False)

    # collect data sets
    data_set_results = {}

    running = False
    succeeded = True
    failed = False

    for data_set in report.data_sets:
        data_gen_res = data_gen_results[data_set.data_generator.id]
        data_set_results[data_set.id] = data_gen_res

        data_gen_status = data_gen_statuses[data_set.data_generator.id]
        log.data_sets[data_set.id] = data_gen_status
        if data_gen_status == Status.FAILED:
            failed = True
        if data_gen_status == Status.SUCCEEDED:
            running = True
        else:
            succeeded = False

    for format in formats:
        ReportWriter().run(report,
                           data_set_results,
                           base_out_path,
                           os.path.join(rel_out_path, report.id) if rel_out_path else report.id,
                           format=format)

    if failed:
        status = Status.FAILED

    elif running:
        if succeeded:
            status = Status.SUCCEEDED
        else:
            status = Status.RUNNING

    else:
        status = Status.QUEUED

    return data_set_results, status, data_gen_exceptions, task_contributes_to_report


def exec_plot_2d(plot, variable_results, base_out_path, rel_out_path, formats, task, log):
    """ Execute a 2D plot, generating the curves which are available

    Args:
        plot (:obj:`Plot2D`): plot
        variable_results (:obj:`VariableResults`): result of each data generator
        base_out_path (:obj:`str`): base path to store the plot. Complete path is
            ``{base_out_path}/{rel_out_path}/{plot.id}.csv``
        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the plot
        formats (:obj:`list` of :obj:`PlotFormat`, optional): plot format (e.g., pdf)
        task (:obj:`Task`): task
        log (:obj:`ReportLog`, optional): log of plot

    Returns:
        :obj:`tuple`:

            * :obj:`Status`: status
            * :obj:`Exception`: exception for failure
            * :obj:`bool`: whether :obj:`task` contributes a variable to the plot
    """
    # calculate data generators
    data_generators = set()
    for curve in plot.curves:
        data_generators.add(curve.x_data_generator)
        data_generators.add(curve.y_data_generator)

    data_gen_results, data_gen_statuses, data_gen_exceptions, task_contributes_to_plot = calc_data_generators_results(
        data_generators, variable_results, plot, task)

    # collect data sets
    running = False
    succeeded = True
    failed = False

    succeeded_curves = []
    for curve in plot.curves:
        x_data_gen_status = data_gen_statuses[curve.x_data_generator.id]
        y_data_gen_status = data_gen_statuses[curve.y_data_generator.id]

        if x_data_gen_status == Status.SUCCEEDED and y_data_gen_status == Status.SUCCEEDED:
            curve_status = Status.SUCCEEDED
            succeeded_curves.append(curve)
        elif x_data_gen_status == Status.FAILED or y_data_gen_status == Status.FAILED:
            curve_status = Status.FAILED
        else:
            curve_status = Status.QUEUED

        log.curves[curve.id] = curve_status

        if curve_status == Status.FAILED:
            failed = True
        if curve_status == Status.SUCCEEDED:
            running = True
        else:
            succeeded = False

    for format in formats:
        write_plot_2d(Plot2D(curves=succeeded_curves),
                      data_gen_results,
                      base_out_path,
                      os.path.join(rel_out_path, plot.id) if rel_out_path else plot.id,
                      format=format)

    # determine the overall status of the plot
    if failed:
        status = Status.FAILED

    elif running:
        if succeeded:
            status = Status.SUCCEEDED
        else:
            status = Status.RUNNING

    else:
        status = Status.QUEUED

    # return
    return status, data_gen_exceptions, task_contributes_to_plot


def exec_plot_3d(plot, variable_results, base_out_path, rel_out_path, formats, task, log):
    """ Execute a 3D plot, generating the surfaces which are available

    Args:
        plot (:obj:`Plot3D`): plot
        variable_results (:obj:`VariableResults`): result of each data generator
        base_out_path (:obj:`str`): base path to store the plot. Complete path is
          ``{base_out_path}/{rel_out_path}/{plot.id}.pdf``
        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the plot
        formats (:obj:`list` of :obj:`PlotFormat`, optional): plot format (e.g., pdf)
        task (:obj:`Task`): task
        log (:obj:`ReportLog`, optional): log of plot

    Returns:
        :obj:`tuple`:

            * :obj:`Status`: status
            * :obj:`Exception`: exception for failure
            * :obj:`bool`: whether :obj:`task` contributes a variable to the plot
    """
    # calculate data generators
    data_generators = set()
    for surface in plot.surfaces:
        data_generators.add(surface.x_data_generator)
        data_generators.add(surface.y_data_generator)
        data_generators.add(surface.z_data_generator)

    data_gen_results, data_gen_statuses, data_gen_exceptions, task_contributes_to_plot = calc_data_generators_results(
        data_generators, variable_results, plot, task)

    # collect data sets
    running = False
    succeeded = True
    failed = False

    succeeded_surfaces = []
    for surface in plot.surfaces:
        x_data_gen_status = data_gen_statuses[surface.x_data_generator.id]
        y_data_gen_status = data_gen_statuses[surface.y_data_generator.id]
        z_data_gen_status = data_gen_statuses[surface.z_data_generator.id]

        if x_data_gen_status == Status.SUCCEEDED and y_data_gen_status == Status.SUCCEEDED and z_data_gen_status == Status.SUCCEEDED:
            surface_status = Status.SUCCEEDED
            succeeded_surfaces.append(surface)
        elif x_data_gen_status == Status.FAILED or y_data_gen_status == Status.FAILED or z_data_gen_status == Status.FAILED:
            surface_status = Status.FAILED
        else:
            surface_status = Status.QUEUED

        log.surfaces[surface.id] = surface_status

        if surface_status == Status.FAILED:
            failed = True
        if surface_status == Status.SUCCEEDED:
            running = True
        else:
            succeeded = False

    for format in formats:
        write_plot_3d(Plot3D(surfaces=succeeded_surfaces),
                      data_gen_results,
                      base_out_path,
                      os.path.join(rel_out_path, plot.id) if rel_out_path else plot.id,
                      format=format)

    # determine the overall status of the plot
    if failed:
        status = Status.FAILED

    elif running:
        if succeeded:
            status = Status.SUCCEEDED
        else:
            status = Status.RUNNING

    else:
        status = Status.QUEUED

    # return
    return status, data_gen_exceptions, task_contributes_to_plot
