""" Utilities for executing tasks in SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Task, Report
from .io import SedmlSimulationReader
from .utils import apply_changes_to_xml_model
import numpy
import os
import pandas
import tempfile
import types  # noqa: F401


__all__ = [
    'exec_doc',
]


def exec_doc(filename, task_executer, out_dir, apply_xml_model_changes=False):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        filename (:obj:`str`): path to SED-ML file
        task_executer (:obj:`types.FunctionType`): function to execute each task in the SED-ML file.
            The function must implement the following interface::

                def exec_task(task, variables):
                    ''' Execute a simulation and return its results

                    Args:
                       task (:obj:`Task`): task
                       variables (:obj:`list` of :obj:`DataGeneratorVariable`): variables that should be recorded
                    '''
                    pass

        out_dir (:obj:`str`): directory to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
    """
    doc = SedmlSimulationReader().run(filename)

    # apply changes to models
    working_dir = os.path.dirname(filename)
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

            modified_model_filenames.append(modified_model_file)

    # execute simulations
    variable_results = {}
    for task in doc.tasks:
        if isinstance(task, Task):
            # get a list of the variables that the task needs to record
            variables = set()
            for data_gen in doc.data_generators:
                for i_var, var in enumerate(data_gen.variables):
                    if var.task == task:
                        if var.model and var.model != model:
                            raise ValueError('Model {} of variable {} of data generator {} does not participate in task {}'.format(
                                var.model.id, i_var, data_gen.id, task.id))
                        var.model = task.model

            # execute task and record variables
            task_variable_results = task_executer(task, variables)
            for var, var_res in task_variable_results.items():
                variable_results[var] = var_res

        else:
            raise NotImplementedError('Tasks of type {} are not supported'.format(task.__class__.__name__))

    # generate outputs
    for output in doc.outputs:
        if isinstance(output, Report):
            dataset_ids = []
            dataset_results = []
            dataset_shapes = set()

            for dataset in output.datasets:
                if len(dataset.data_generator.variables) != 1 or dataset.data_generator.parameters:
                    raise NotImplementedError('Data generator {} must be equal to a single variable'.format(dataset.data_generator.id))
                dataset_ids.append(dataset.id)
                var_res = variable_results[dataset.data_generator.variables[0]]
                dataset_results.append(var_res)
                dataset_shapes.add(var_res.shape)

            if len(dataset_shapes) > 1:
                raise ValueError('Data generators for report {} must have consistent shapes'.format(output.id))

            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            out_filename = os.path.join(out_dir, output.id + '.csv')

            output_df = pandas.DataFrame(numpy.array(dataset_results), index=dataset_ids)
            output_df.to_csv(out_filename, header=False)

        else:
            raise NotImplementedError('Outputs of type {} are not supported'.format(output.__class__.__name__))

    # cleanup modified models
    for modified_model_filename in modified_model_filenames:
        os.remove(modified_model_filename)
