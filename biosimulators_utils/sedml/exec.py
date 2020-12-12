""" Utilities for executing tasks in SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
from ..plot.data_model import PlotFormat
from ..report.data_model import DataGeneratorVariableResults, OutputResults, ReportFormat
from ..report.io import ReportWriter
from .data_model import SedDocument, Task, Report
from .io import SedmlSimulationReader
from .utils import apply_changes_to_xml_model, get_variables_for_task
import copy
import numpy
import os
import pandas
import tempfile
import types  # noqa: F401


__all__ = [
    'exec_doc',
]


def exec_doc(doc, working_dir, task_executer, base_out_path, rel_out_path=None,
             apply_xml_model_changes=False, report_formats=None, plot_formats=None):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        doc (:obj:`SedDocument` of :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)
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

        out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., csv or h5)
        plot_formats (:obj:`list` of :obj:`PlotFormat`, optional): plot format (e.g., pdf)
    """
    # process arguments
    if not isinstance(doc, SedDocument):
        doc = SedmlSimulationReader().run(doc)
    else:
        doc = copy.deepcopy(doc)

    if report_formats is None:
        report_formats = [ReportFormat(format_value) for format_value in get_config().REPORT_FORMATS]

    if plot_formats is None:
        plot_formats = [PlotFormat(format_value) for format_value in get_config().PLOT_FORMATS]

    # apply changes to models
    modified_model_filenames = []
    for model in doc.models:
        if not os.path.isabs(model.source):
            model.source = os.path.join(working_dir, model.source)

        if apply_xml_model_changes and model.changes:
            original_model_filename = model.source

            modified_model_file, modified_model_filename = tempfile.mkstemp(suffix='.xml')
            os.close(modified_model_file)

            apply_changes_to_xml_model(model.changes, original_model_filename, modified_model_filename)

            model.source = modified_model_filename

            modified_model_filenames.append(modified_model_filename)

    # execute simulations
    variable_results = DataGeneratorVariableResults()
    for task in doc.tasks:
        if isinstance(task, Task):
            # get a list of the variables that the task needs to record
            task_vars = get_variables_for_task(doc, task)

            # execute task and record variables
            task_variable_results = task_executer(task, task_vars)

            for var in task_vars:
                variable_results[var.id] = task_variable_results.get(var.id, None)
                if variable_results[var.id] is None:
                    raise ValueError('Variable {} must be generated for task {}'.format(var.id, task.id))

        else:
            raise NotImplementedError('Tasks of type {} are not supported'.format(task.__class__.__name__))

    # generate outputs
    report_results = OutputResults()
    for output in doc.outputs:
        if isinstance(output, Report):
            dataset_ids = []
            dataset_results = []
            dataset_shapes = set()

            for data_set in output.data_sets:
                if len(data_set.data_generator.variables) != 1 or data_set.data_generator.parameters:
                    raise NotImplementedError('Data generator {} must be equal to a single variable'.format(data_set.data_generator.id))
                if (
                    len(data_set.data_generator.variables) == 1
                    and not data_set.data_generator.parameters
                    and data_set.data_generator.math != data_set.data_generator.variables[0].id
                ):
                    raise ValueError('Math of data generator must be equal to the id of the variable')
                dataset_ids.append(data_set.id)
                var_res = variable_results[data_set.data_generator.variables[0].id]
                dataset_results.append(var_res)
                dataset_shapes.add(var_res.shape)

            if len(dataset_shapes) > 1:
                raise ValueError('Data generators for report {} must have consistent shapes'.format(output.id))

            output_df = pandas.DataFrame(numpy.array(dataset_results), index=dataset_ids)
            report_results[output.id] = output_df

            for report_format in report_formats:
                ReportWriter().run(output_df,
                                   base_out_path,
                                   os.path.join(rel_out_path, output.id) if rel_out_path else output.id,
                                   format=report_format)

        else:
            raise NotImplementedError('Outputs of type {} are not supported'.format(output.__class__.__name__))

    # cleanup modified models
    for modified_model_filename in modified_model_filenames:
        os.remove(modified_model_filename)

    return (report_results, variable_results)
