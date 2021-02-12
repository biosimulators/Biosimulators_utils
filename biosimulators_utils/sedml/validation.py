""" Methods for validating SED objects

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import warn
from ..xml.utils import validate_xpaths_ref_to_unique_objects
from .data_model import (AbstractTask, Task, RepeatedTask, ModelLanguage, ModelChange, ComputeModelChange,  # noqa: F401
                         Simulation, UniformTimeCourseSimulation, Variable,
                         Range, FunctionalRange,
                         Report, Plot2D, Plot3D)
from .utils import append_all_nested_children_to_doc, get_range_len
from .warnings import IllogicalSedmlWarning
import collections
import copy
import math
import networkx
import os
import re

__all__ = [
    'validate_doc',
    'validate_reference',
    'validate_task',
    'validate_model_language',
    'validate_model_change_types',
    'validate_model_changes',
    'validate_simulation_type',
    'validate_uniform_time_course_simulation',
    'validate_data_generator_variables',
]


def validate_doc(doc, validate_semantics=True):
    """ Validate a SED document

    Args:
        doc (:obj:`SedDocument`): SED document
        validate_semantics (:obj:`bool`, optional): if :obj:`True`, check that SED-ML is semantically valid

    Raises:
        :obj:`ValueError`: if document is invalid (e.g., required ids missing or ids not unique)
    """
    # validate that required ids exist and are unique
    for child_type in ('models', 'simulations', 'data_generators', 'tasks', 'outputs'):
        children = getattr(doc, child_type)

        missing_ids = next((True for child in children if not getattr(child, 'id', None)), False)
        if missing_ids:
            raise ValueError('{} must have ids'.format(child_type))

        if validate_semantics:
            repeated_ids = len(set(getattr(child, 'id', None) for child in children)) < len(children)
            if repeated_ids:
                raise ValueError('{} must have unique ids'.format(child_type))

    if validate_semantics:
        # validate the models, simulations, tasks, data generators are children of the SED document
        doc_copy = copy.deepcopy(doc)
        append_all_nested_children_to_doc(doc_copy)

        for child_type in ('models', 'simulations', 'tasks', 'data_generators'):
            if len(getattr(doc, child_type)) != len(getattr(doc_copy, child_type)):
                raise ValueError('{} must be direct children of SED document'.format(child_type))

        # internal model sources are defined
        model_ids = [model.id for model in doc.models]
        for model in doc.models:
            if model.source.startswith('#'):
                if model.source[1:] not in model_ids:
                    raise ValueError('Source `{}` of model `{}` is not defined.'.format(model.source, model.id))

        # model sources are acyclic
        model_source_graph = networkx.DiGraph()

        for model in doc.models:
            model_source_graph.add_node(model.id)

        for model in doc.models:
            if model.source.startswith('#'):
                model_source_graph.add_edge(model.id, model.source[1:])

        try:
            networkx.algorithms.cycles.find_cycle(model_source_graph)
            raise ValueError('The sources of the models are defined cyclically. The sources of models must be acyclic.')
        except networkx.NetworkXNoCycle:
            pass

        # validate that model changes have targets
        for model in doc.models:
            for i_change, change in enumerate(model.changes):
                if not change.target:
                    raise ValueError('Model change attributes must define a target')

                if isinstance(change, ComputeModelChange):
                    for param in change.parameters:
                        if not param.id:
                            raise ValueError('Parameters must have ids')

                    for var in change.variables:
                        if not var.id:
                            raise ValueError('Variables must have ids')
                        if not var.target:
                            raise ValueError('Compute change variables must define a target')
                        if var.symbol:
                            raise ValueError('Compute change variables must define a target, not a symbol')
                        # task reference not validated because its optional in this context
                        validate_reference(var, 'Variable {} of model change "{}"'.format(var.id, i_change + 1), 'model', 'model')

                        if var.task:
                            raise ValueError('Task of variable "{}" of model change "{}" should be null.'.format(
                                var.id, i_change + 1))
                    if not change.math:
                        raise ValueError('Compute model changes must have math')

        # validate the compute model changes are acyclic
        model_change_graph = networkx.DiGraph()

        for model in doc.models:
            model_change_graph.add_node(model.id)

        for model in doc.models:
            for change in model.changes:
                if isinstance(change, ComputeModelChange):
                    for variable in change.variables:
                        if variable.model != model:
                            model_change_graph.add_edge(model.id, variable.model.id)

        try:
            networkx.algorithms.cycles.find_cycle(model_change_graph)
            raise ValueError('The compute changes of the models are defined cyclically. The changes must be acyclic.')
        except networkx.NetworkXNoCycle:
            pass

        # algorithms and parameters are described with valid ids of KiSAO terms
        for sim in doc.simulations:
            if sim.algorithm:
                if not sim.algorithm.kisao_id or not re.match(r'^KISAO_\d{7}$', sim.algorithm.kisao_id):
                    raise ValueError('Algorithm of simulation {} has an invalid KiSAO id: {}'.format(sim.id, sim.algorithm.kisao_id))
                for change in sim.algorithm.changes:
                    if not change.kisao_id or not re.match(r'^KISAO_\d{7}$', change.kisao_id):
                        raise ValueError('Algorithm of simulation {} has an invalid KiSAO id: {}'.format(sim.id, sim.algorithm.kisao_id))

        # basic tasks reference a model and a simulation
        for task in doc.tasks:
            if isinstance(task, Task):
                validate_reference(task, 'Task {}'.format(task.id), 'model', 'model')
                validate_reference(task, 'Task {}'.format(task.id), 'simulation', 'simulation')

        # sub tasks of repeated tasks reference tasks and have unique orders
        sub_task_graph = networkx.DiGraph()
        for task in doc.tasks:
            sub_task_graph.add_node(task.id)

            if isinstance(task, RepeatedTask):
                if not task.sub_tasks:
                    msg = 'Repeated tasks must have at least one sub-task. Repeated task `{}` has no sub-tasks.'.format(task.id)
                    raise ValueError(msg)

                for i_sub_task, sub_task in enumerate(task.sub_tasks):
                    if not isinstance(sub_task.task, AbstractTask):
                        msg = ('Sub-tasks must reference tasks. '
                               'Sub-task {} of repeated task {} does not reference a task.').format(
                            i_sub_task + 1, task.id)
                        raise ValueError(msg)

                    sub_task_graph.add_edge(task.id, sub_task.task.id)

                duplicate_orders = [item for item, count in collections.Counter(
                    sub_task.order for sub_task in task.sub_tasks).items() if count > 1]
                if duplicate_orders:
                    msg = ('The `order` of each sub-task should be distinct within a repeated task. '
                           'Multiple sub-tasks of repeated task `{}` have the following orders:\n  - {}').format(
                        task.id, '\n  - '.join([str(order) for order in sorted(duplicate_orders)]))
                    raise ValueError(msg)

        try:
            networkx.algorithms.cycles.find_cycle(sub_task_graph)
            raise ValueError('The subtasks are defined cyclically. The graph of subtasks must be acyclic.')
        except networkx.NetworkXNoCycle:
            pass

        # ranges of repeated tasks have unique ids
        range_ids = []
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                for i_range, range in enumerate(task.ranges):
                    if not isinstance(range, Range):
                        raise NotImplementedError('Ranges of type `{}` are not supported.'.format(range.__class__.__name__))

                    if not range.id:
                        raise ValueError('Ranges must have ids. Range {} of task `{}` does not have an id.'.format(i_range + 1, task.id))
                    range_ids.append(range.id)

        duplicate_range_ids = [item for item, count in collections.Counter(range_ids).items() if count > 1]
        if duplicate_range_ids:
            msg = ('Ranges must have unique ids. The following range ids are repeated:\n  - {}').format(
                '\n  - '.join(sorted(duplicate_range_ids)))
            raise ValueError(msg)

        # Functional ranges of repeated tasks
        # - Functional ranges reference other ranges
        # - Parameters of functional ranges
        #   - Have ids
        # - Variables of functional ranges
        #   - Have ids
        #   - Reference models
        #   - Have symbols or targets
        # - Functional ranges have math
        # - Functional range graph is acyclic
        functional_range_graph = networkx.DiGraph()
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                for range in task.ranges:
                    if isinstance(range, FunctionalRange):
                        if not range.range:
                            msg = ('Functional ranges must reference another range. '
                                   'Functional range `{}` does not reference another range.').format(range.id)
                            raise ValueError(msg)

                        for param in range.parameters:
                            if not param.id:
                                raise ValueError('Parameters must have ids')

                        for variable in range.variables:
                            if not variable.id:
                                raise ValueError('Variables must have ids')

                            if not variable.model:
                                raise ValueError('Variables of functional ranges must reference models')
                            if variable.task:
                                raise ValueError('Variables of functional ranges should not reference tasks')

                            if not variable.symbol and not variable.target:
                                raise ValueError('Variables of functional ranges should define a symbol or target')
                            if variable.symbol and variable.target:
                                raise ValueError('Variables of functional ranges should define a symbol or target, not both')

                        if not range.math:
                            msg = 'Functional ranges must have math. Functional range `{}` does not have math.'.format(range.id)
                            raise ValueError(msg)

                        functional_range_graph.add_node(range.id)
                        functional_range_graph.add_edge(range.id, range.range.id)

        try:
            networkx.algorithms.cycles.find_cycle(functional_range_graph)
            raise ValueError('The functional ranges are defined cyclically. The graph of functional ranges must be acyclic.')
        except networkx.NetworkXNoCycle:
            pass

        # ranges of repeated tasks
        # - are of a supported type (error)
        # - are at least as long as the main range (error)
        # - the same lengths (warnings)
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                if not isinstance(task.range, Range):
                    raise ValueError('Repeated tasks must have main ranges. Repeated task `{}` does not have a main range.'.format(task.id))
                main_range_len = get_range_len(task.range)

                for range in task.ranges:
                    range_len = get_range_len(range)
                    if range_len < main_range_len:
                        msg = (
                            'The child ranges of repeated tasks must be at least as long as the main range of their parent repeated tasks. '
                            'Range `{}` of repeated task `{}` is shorter than its main range, {} < {}.'
                        ).format(range.id, task.id, range_len, main_range_len)
                        raise ValueError(msg)
                    elif range_len > main_range_len:
                        msg = ('Child range `{}` of repeated task `{}` is longer than its main range ({} > {}). '
                               'The tail elements of the range will be ignored.').format(range.id, task.id, range_len, main_range_len)
                        warn(msg, IllogicalSedmlWarning)

                for i_change, change in enumerate(task.changes):
                    if change.range:
                        range_len = get_range_len(change.range)
                        if range_len < main_range_len:
                            msg = (
                                'The child ranges of repeated tasks must be '
                                'at least as long as the main range of their parent repeated tasks. '
                                'Range `{}` of repeated task `{}` is shorter than its main range, {} < {}.'
                            ).format(change.range.id, task.id, range_len, main_range_len)
                            raise ValueError(msg)
                        elif range_len > main_range_len:
                            msg = (
                                'Child range `{}` of repeated task `{}` is longer than its main range ({} > {}). '
                                'The tail elements of the range will be ignored.'
                            ).format(change.range.id, task.id, range_len, main_range_len)
                            warn(msg, IllogicalSedmlWarning)

        # Set value changes of repeated tasks
        # - Changes reference models
        # - Changes reference a symbol or target
        # - Parameters
        #   - Have ids
        # - Variables
        #   - Have ids
        #   - Reference a model, not a task
        #   - Define a target, not a symbol
        # - Changes have math
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                for i_change, change in enumerate(task.changes):
                    if not change.model:
                        msg = ('Set value changes must reference models. '
                               'Change {} of task `{}` does not reference a model.').format(
                            i_change + 1, task.id)
                        raise ValueError(msg)

                    if not change.target:
                        msg = ('Set value changes must define a target. '
                               'Change {} of task `{}` does not define a target.').format(
                            i_change + 1, task.id)
                        raise ValueError(msg)

                    if change.symbol:
                        msg = ('Set value changes should not define a symbol. '
                               'Change {} of task `{}` defines a symbol.').format(
                            i_change + 1, task.id)
                        raise ValueError(msg)

                    for parameter in change.parameters:
                        if not parameter.id:
                            raise ValueError('Parameters must have ids')

                    for variable in change.variables:
                        if not variable.id:
                            raise ValueError('Variables must have ids')

                        if not variable.model:
                            raise ValueError('Set value variables must reference a model')
                        if variable.task:
                            raise ValueError('Set value variables should not reference a task')

                        if not variable.target and not variable.symbol:
                            raise ValueError('Set value variables must define a target or a symbol')
                        if variable.target and variable.symbol:
                            raise ValueError('Set value variables must define a target or a symbol, not both')

                    if not change.math:
                        msg = 'Set value changes must have math. Change {} of task `{}` does not have math.'.format(
                            i_change + 1, task.id)
                        raise ValueError(msg)

        # variables of data generators
        # - have ids
        # - have target OR symbol
        # - don't have model references
        # - have math
        for data_gen in doc.data_generators:
            for param in data_gen.parameters:
                if not param.id:
                    raise ValueError('Parameters must have ids')

            for var in data_gen.variables:
                if not var.id:
                    raise ValueError('Variables must have ids')
                if (not var.target and not var.symbol) or (var.target and var.symbol):
                    raise ValueError('Data generator variables must define a target or symbol')
                validate_reference(var, 'Variable {} of data generator "{}"'.format(var.id, data_gen.id), 'task', 'task')
                # model reference not validated because its optional in this context

                if var.model:
                    raise ValueError('Model of variable {} of data generator "{}" should be null.'.format(
                        var.id, data_gen.id))
            if not data_gen.math:
                raise ValueError('Data generators must have math')

        # validate outputs
        # - reports
        #   - data sets have ids and labels
        #   - data sets reference data generators
        # - plots
        #   - curves and surfaces have ids
        #   - x, y, z attributes reference data generators
        for output in doc.outputs:
            if isinstance(output, Report):
                for data_set in output.data_sets:
                    if not data_set.id:
                        raise ValueError('Data sets must have ids')
                    if not data_set.label:
                        raise ValueError('Data sets must have labels')
                    validate_reference(data_set, 'Data set {} of report "{}"'.format(
                        data_set.id, output.id), 'data_generator', 'data data generator')

            elif isinstance(output, Plot2D):
                for curve in output.curves:
                    if not curve.id:
                        raise ValueError('Curves must have ids')
                    validate_reference(curve, 'Curve {} of 2D plot "{}"'.format(
                        curve.id, output.id), 'x_data_generator', 'x data data generator')
                    validate_reference(curve, 'Curve {} of 2D plot "{}"'.format(
                        curve.id, output.id), 'y_data_generator', 'y data data generator')

            elif isinstance(output, Plot3D):
                for surface in output.surfaces:
                    if not surface.id:
                        raise ValueError('Surfaces must have ids')
                    validate_reference(surface, 'Surface {} of 3D plot "{}"'.format(
                        surface.id, output.id), 'x_data_generator', 'x data data generator')
                    validate_reference(surface, 'Surface {} of 3D plot "{}"'.format(
                        surface.id, output.id), 'y_data_generator', 'y data data generator')
                    validate_reference(surface, 'Surface {} of 3D plot "{}"'.format(
                        surface.id, output.id), 'z_data_generator', 'z data data generator')


def validate_reference(obj, obj_label, attr_name, attr_label):
    if not getattr(obj, attr_name):
        raise ValueError('{} must have a {}'.format(obj_label, attr_label))


def validate_task(task):
    """ Validate a simulation task

    Args:
        task (:obj:`Task`): task

    Raises:
        :obj:`ValueError`: if task is invalid
        :obj:`FileNotFoundError`: if model file doesn't exist
    """
    # check that task is an instance of Task
    if not isinstance(task, Task):
        raise ValueError('Task type {} is not supported'.format(task.__class__.__name__))

    # check that task has model
    if not task.model:
        raise ValueError('Task must have a model')

    # check that model file exists
    if not task.model.source or not os.path.isfile(task.model.source):
        # todo: allow references to other other models, URLs and identifiers.org ids
        raise FileNotFoundError("Model source '{}' must be a file".format(task.model.source or ''))

    # check that task has model
    simulation = task.simulation
    if not simulation:
        raise ValueError('Task must have a simulation')

    if not simulation.algorithm:
        raise ValueError('Simulation must have an algorithm')

    if not simulation.algorithm.kisao_id or not re.match(r'^KISAO_\d{7}$', simulation.algorithm.kisao_id):
        raise ValueError('Algorithm must have a valid KiSAO id')

    for change in simulation.algorithm.changes:
        if not change.kisao_id or not re.match(r'^KISAO_\d{7}$', change.kisao_id):
            raise ValueError('Algorithm change must have a valid KiSAO id')


def validate_model_language(language, valid_language):
    """ Check that model is encoded in a specific language

    Args:
        language (:obj:`ModelLanguage`): model language
        valid_language (:obj:`ModelLanguage`): valid model language

    Raises:
        :obj:`NotImplementedError`: if the model uses a different language
    """
    if not language or not re.match('^{}($|:)'.format(valid_language.value), language):
        raise NotImplementedError("Model language {} is not supported. Model language must be '{}'.".format(
            language, valid_language.value))


def validate_model_change_types(changes, types=(ModelChange, )):
    """ Check that model changes are valid

    Args:
        changes (:obj:`list` of :obj:`ModelChange`): model changes
        types (:obj:`type` or :obj:`tuple` of :obj:`type`, optional): valid type(s) of model changes

    Raises:
        :obj:`NotImplementedError`: if the model uses different types of changes
    """
    for change in changes:
        if not isinstance(change, types):
            raise NotImplementedError("".join([
                'Model changes of type {} are not supported. '.format(change.__class__.__name__),
                'Model changes must be instances of one of the following types:\n  - {}'.format(
                    '\n  - '.join(type.__name__ for type in types)),

            ]))


def validate_model_changes(changes):
    """ Check that model changes are semantically valid

    * Check that the variables of compute model changes are valid

    Args:
        changes (:obj:`list` of :obj:`ModelChange`): model changes

    Raises:
        :obj:`ValueError`: if a model change is invalid
    """
    for change in changes:
        if not change.target:
            raise ValueError('Model change attributes must define a target')

        if isinstance(change, ComputeModelChange):
            for parameter in change.parameters:
                if not parameter.id:
                    raise ValueError('Parameters must have ids')

            for variable in change.variables:
                if not variable.id:
                    raise ValueError('Variables must have ids')

                if not variable.model:
                    raise ValueError('Compute model change variables must reference a model')
                if variable.task:
                    raise ValueError('Compute model change variables should not reference a task')

                if not variable.target:
                    raise ValueError('Compute model change variables must define a target')
                if variable.symbol:
                    raise ValueError('Compute model change variables must define a target, not a symbol')


def validate_simulation_type(simulation, types):
    """ Check that simulation is a time course simulation

    Args:
        simulation (:obj:`Simulation`): simulation
        types (:obj:`type`): valid simulation types

    Raises:
        :obj:`NotImplementedError`: if the simulation is a different type
    """
    if not isinstance(simulation, types):
        raise NotImplementedError(
            'Simulation type {} is not supported. Simulation must be an instance of one of the following:\n  - {}'.format(
                simulation.__class__.__name__, '\n  - '.join(type.__name__ for type in types)))


def validate_uniform_time_course_simulation(simulation):
    """ Check that simulation is a valid uniform time course simulation

    Args:
        simulation (:obj:`Simulation`): simulation

    Raises:
        :obj:`ValueErorr`: if the simulation is invalid
    """
    if isinstance(simulation, UniformTimeCourseSimulation):
        if simulation.output_start_time < simulation.initial_time:
            raise ValueError('Output start time {} must be at least the initial time {}.'.format(
                simulation.output_start_time, simulation.initial_time))

        if simulation.output_end_time < simulation.output_start_time:
            raise ValueError('Output end time {} must be at least the output start time {}.'.format(
                simulation.output_end_time, simulation.output_start_time))

        if math.floor(simulation.number_of_steps) != simulation.number_of_steps:
            raise ValueError('Number of points must be an integer.')


def validate_data_generator_variables(variables):
    """ Check variables have a symbol or target

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables

    Raises:
        :obj:`ValueError`: if a variable is invalid
    """
    for variable in variables:
        if variable.model:
            raise ValueError('Variable should not reference a model')
        if not variable.task:
            raise ValueError('Variable must reference a task')

        if (variable.symbol and variable.target) or (not variable.symbol and not variable.target):
            raise ValueError('Variable must define a symbol or target')


def validate_variable_xpaths(variables, model_source, attr='id'):
    """ Validate that the target of each variable matches one object in
    an XML-encoded model

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables
        model_source (:obj:`str`): path to XML model file
        attr (:obj:`str`, optional): attribute to get values of

    Returns:
        :obj:`dict` of :obj:`str` to :obj:`str`: dictionary that maps each XPath to the
            value of the attribute of the object in the XML file that matches the XPath
    """
    x_path_attrs = {}
    for variable in variables:
        if variable.target:
            x_path = variable.target
            if '/@' in x_path:
                x_path, _, _ = x_path.rpartition('/@')
            x_path_attrs[variable.target] = validate_xpaths_ref_to_unique_objects(
                model_source, [x_path], variable.target_namespaces, attr=attr)[x_path]
    return x_path_attrs
