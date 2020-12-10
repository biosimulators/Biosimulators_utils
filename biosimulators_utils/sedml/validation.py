""" Methods for validating SED objects

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Task, ModelLanguage, ModelChange, Simulation, UniformTimeCourseSimulation, DataGeneratorVariable  # noqa: F401
import os
import re

__all__ = [
    'validate_task',
    'validate_model_language',
    'validate_model_change_types',
    'validate_simulation_type',
    'validate_uniform_time_course_simulation',
    'validate_data_generator_variables',
]


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
