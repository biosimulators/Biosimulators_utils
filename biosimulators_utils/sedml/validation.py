""" Methods for validating SED objects

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import (Task, ModelLanguage, ModelChange, ModelAttributeChange,  # noqa: F401
                         Simulation, UniformTimeCourseSimulation, DataGeneratorVariable,
                         Report, Plot2D, Plot3D)
from .utils import append_all_nested_children_to_doc
import copy
import math
import os
import re

__all__ = [
    'validate_doc',
    'validate_reference',
    'validate_task',
    'validate_model_language',
    'validate_model_change_types',
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

        # validate that model attribute changes have targets
        for model in doc.models:
            for change in model.changes:
                if isinstance(change, ModelAttributeChange):
                    if not change.target:
                        raise ValueError('Model change attributes must define a target')

        for sim in doc.simulations:
            if sim.algorithm:
                if not sim.algorithm.kisao_id or not re.match(r'^KISAO_\d{7}$', sim.algorithm.kisao_id):
                    raise ValueError('Algorithm of simulation {} has an invalid KiSAO id: {}'.format(sim.id, sim.algorithm.kisao_id))
                for change in sim.algorithm.changes:
                    if not change.kisao_id or not re.match(r'^KISAO_\d{7}$', change.kisao_id):
                        raise ValueError('Algorithm of simulation {} has an invalid KiSAO id: {}'.format(sim.id, sim.algorithm.kisao_id))

        for task in doc.tasks:
            if isinstance(task, Task):
                validate_reference(task, 'Task {}'.format(task.id), 'model', 'model')
                validate_reference(task, 'Task {}'.format(task.id), 'simulation', 'simulation')

        for data_gen in doc.data_generators:
            for var in data_gen.variables:
                if not var.id:
                    raise ValueError('Variables must have ids')
                if (not var.target and not var.symbol) or (var.target and var.symbol):
                    raise ValueError('Variables must define a target or symbol')
                validate_reference(var, 'Variable {} of data generator "{}"'.format(var.id, data_gen.id), 'task', 'task')
                validate_reference(var, 'Variable {} of data generator "{}"'.format(var.id, data_gen.id), 'model', 'model')

                if var.model and var.task and var.task.model and var.task.model != var.model:
                    raise ValueError('Model of variable {} of data generator "{}" and model of task must be consistent'.format(
                        var.id, data_gen.id))
            if not data_gen.math:
                raise ValueError('Data generators must have math')

        for output in doc.outputs:
            if isinstance(output, Report):
                for dataset in output.datasets:
                    if not dataset.id:
                        raise ValueError('Datasets must have ids')
                    if not dataset.label:
                        raise ValueError('Datasets must have labels')
                    validate_reference(dataset, 'Dataset {} of report "{}"'.format(
                        dataset.id, output.id), 'data_generator', 'data data generator')

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


def validate_model_change_types(changes, types):
    """ Check that model changes are valid

    Args:
        changes (:obj:`list` of :obj:`ModelChange`): model changes
        types (:obj:`tuple` of :obj:`type`): valid model change types

    Raises:
        :obj:`NotImplementedError`: if the model uses different types of changes
    """
    for change in changes:
        if not isinstance(change, types):
            raise NotImplementedError("".join([
                'Model changes of type {} are not supported. ',
                'Model changes must be instances of one of of the following types:\n  - {}'.format(
                    change.__class__.__name__, '\n  - '.join(type.__name__ for type in types)),

            ]))

        if isinstance(change, ModelAttributeChange):
            if not change.target:
                raise ValueError('Model change attributes must define a target')


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

        if math.floor(simulation.number_of_points) != simulation.number_of_points:
            raise ValueError('Number of points must be an integer.'.format(
                simulation.output_start_time, simulation.initial_time))


def validate_data_generator_variables(variables):
    """ Check variables have a symbol or target

    Args:
        variables (:obj:`list` of :obj:`DataGeneratorVariable`): variables

    Raises:
        :obj:`ValidateError`: if a variable is invalid
    """
    for variable in variables:
        if (variable.symbol and variable.target) or (not variable.symbol and not variable.target):
            raise ValueError('Variable must define a symbol or target')
