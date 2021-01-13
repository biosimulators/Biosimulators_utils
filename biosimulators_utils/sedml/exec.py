""" Utilities for executing tasks in SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config, Colors
from ..log.data_model import Status, SedDocumentLog, ReportLog, Plot2DLog, Plot3DLog  # noqa: F401
from ..log.utils import init_sed_document_log
from ..plot.data_model import PlotFormat
from ..report.data_model import DataGeneratorVariableResults, OutputResults, ReportFormat
from ..report.io import ReportWriter
from ..warnings import warn
from .data_model import SedDocument, Task, Report, Plot2D, Plot3D
from .exceptions import SedmlExecutionError
from .warnings import RepeatDataSetLabelsWarning, SedmlFeatureNotSupportedWarning
from .io import SedmlSimulationReader
from .utils import resolve_model, apply_changes_to_xml_model, get_variables_for_task, calc_data_generator_results
from .warnings import NoTasksWarning, NoOutputsWarning
import capturer
import copy
import datetime
import numpy
import os
import pandas
import sys
import termcolor
import tempfile
import types  # noqa: F401


__all__ = [
    'exec_sed_doc',
]


def exec_sed_doc(task_executer, doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=False, report_formats=None, plot_formats=None,
                 log=None, indent=0):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        task_executer (:obj:`types.FunctionType`): function to execute each task in the SED-ML file.
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

    Returns:
        :obj:`tuple`:

            * :obj:`OutputResults`: results of each report
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
    variable_results = DataGeneratorVariableResults()
    report_results = OutputResults()

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
                    # resolve model
                    original_model = task.model
                    model = copy.deepcopy(original_model)
                    task.model = model
                    is_model_source_temp = resolve_model(model, doc, working_dir)

                    # apply changes to model
                    unmodified_model_filename = model.source
                    if apply_xml_model_changes and model.changes:
                        modified_model_file, modified_model_filename = tempfile.mkstemp(suffix='.xml')
                        os.close(modified_model_file)

                        apply_changes_to_xml_model(model.changes, unmodified_model_filename, modified_model_filename)

                        model.source = modified_model_filename
                    else:
                        modified_model_filename = None

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

                    # cleanup modified models
                    task.model = original_model
                    if is_model_source_temp:
                        os.remove(unmodified_model_filename)
                    if modified_model_filename:
                        os.remove(modified_model_filename)

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
                        report_results[output.id], output_status, task_contributes_to_report = exec_report(
                            output, variable_results,
                            base_out_path, rel_out_path, report_formats,
                            task,
                            log.outputs[output.id])
                        task_contributes_to_output = task_contributes_to_output or task_contributes_to_report

                    elif isinstance(output, Plot2D):
                        output_status = Status.SKIPPED
                        warn('Output {} skipped because outputs of type {} are not yet supported.'.format(
                            output.id, output.__class__.__name__), SedmlFeatureNotSupportedWarning)
                        # write_plot_2d()

                    elif isinstance(output, Plot3D):
                        output_status = Status.SKIPPED
                        warn('Output {} skipped because outputs of type {} are not yet supported.'.format(
                            output.id, output.__class__.__name__), SedmlFeatureNotSupportedWarning)
                        # write_plot_3d()

                    else:
                        # unreachable because the above cases cover all types of outputs
                        raise NotImplementedError('Outputs of type {} are not supported.'.format(output.__class__.__name__))

                    output_exception = None

                except Exception as exception:
                    exceptions.append(exception)
                    output_status = Status.FAILED
                    output_exception = exception

            log.outputs[output.id].status = output_status
            log.outputs[output.id].exception = output_exception
            log.outputs[output.id].output = captured.get_bytes().decode()
            log.outputs[output.id].duration = (datetime.datetime.now() - start_time).total_seconds()
            log.outputs[output.id].export()

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
    """ Execute a report, generating the datasets which are available

    Args:
        report (:obj:`Report`): report
        variable_results (:obj:`DataGeneratorVariableResults`): result of each data generator
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

            * :obj:`pandas.DataFrame`: report
            * :obj:`Status`: status
            * :obj:`bool`: whether :obj:`task` contribute a variable to the report
    """
    dataset_labels = []
    dataset_results = []
    dataset_shapes = set()

    task_contributes_to_report = False
    running = False
    succeeded = True
    failed = False

    # calculate data generators
    data_gen_results = {}
    for data_set in report.data_sets:
        dataset_labels.append(data_set.label)

        data_gen = data_set.data_generator
        if data_gen.id in data_gen_results:
            data_gen_res = data_gen_results[data_gen.id]
        else:
            vars_available = True
            vars_failed = False
            for variable in data_gen.variables:
                if variable.task == task:
                    task_contributes_to_report = True
                if variable.id in variable_results:
                    if variable_results.get(variable.id, None) is None:
                        vars_available = False
                        vars_failed = True
                else:
                    vars_available = False

            if vars_available and not vars_failed:
                data_gen_res = calc_data_generator_results(data_gen, variable_results)
            else:
                data_gen_res = None
            data_gen_results[data_gen.id] = data_gen_res

        dataset_results.append(data_gen_res)
        if data_gen_res is None:
            if vars_failed:
                failed = True
                log.data_sets[data_set.id] = Status.FAILED
            succeeded = False
        else:
            running = True
            data_set_shape = data_gen_res.shape
            if not data_set_shape and data_gen_res.size:
                data_set_shape = (1,)

            dataset_shapes.add(data_set_shape)
            log.data_sets[data_set.id] = Status.SUCCEEDED

    if len(dataset_shapes) > 1:
        warn('Data generators for report {} do not have consistent shapes'.format(report.id), UserWarning)

    if len(set(dataset_labels)) < len(dataset_labels):
        warn('To facilitate machine interpretation, data sets should have unique ids.',
             RepeatDataSetLabelsWarning)

    dataset_max_shape = []
    for dataset_shape in dataset_shapes:
        dataset_max_shape = dataset_max_shape + [1 if dataset_max_shape else 0] * (len(dataset_shape) - len(dataset_max_shape))
        dataset_shape = list(dataset_shape) + [1 if dataset_shape else 0] * (len(dataset_shape) - len(dataset_max_shape))
        dataset_max_shape = [max(x, y) for x, y in zip(dataset_max_shape, dataset_shape)]

    for i_result, dataset_result in enumerate(dataset_results):
        if dataset_result is None:
            dataset_results[i_result] = numpy.full(dataset_max_shape, numpy.nan)

        dataset_shape = tuple(list(dataset_results[i_result].shape)
                              + [1 if dataset_results[i_result].size else 0]
                              * (len(dataset_max_shape) - dataset_results[i_result].ndim))
        dataset_results[i_result].reshape(dataset_shape)

        pad_width = tuple((0, x - y) for x, y in zip(dataset_max_shape, dataset_shape))
        if pad_width:
            dataset_results[i_result] = numpy.pad(dataset_results[i_result],
                                                  pad_width,
                                                  mode='constant',
                                                  constant_values=numpy.nan)

    output_df = pandas.DataFrame(numpy.array(dataset_results), index=dataset_labels)
    for format in formats:
        ReportWriter().run(output_df,
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

    return output_df, status, task_contributes_to_report
