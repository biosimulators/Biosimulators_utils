""" Utilities for working with RBA models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config  # noqa: F401
from ...sedml.data_model import (  # noqa: F401
    SedDocument, ModelAttributeChange, Variable,
    Simulation, SteadyStateSimulation,
    Algorithm,
    Task,
    )
from ...utils.core import flatten_nested_list_of_strings
from .validation import validate_model
import rba
import types  # noqa: F401

__all__ = ['get_parameters_variables_outputs_for_simulation']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    change_level=SedDocument, native_ids=False, native_data_types=False,
                                                    config=None):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:rba``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000669``
            for RBA)
        change_level (:obj:`types.Type`, optional): level at which model changes will be made (:obj:`SedDocument` or :obj:`Task`)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types
        config (:obj:`Config`, optional): whether to fail on missing includes

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulations of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model
    """
    # check model file exists and is valid
    errors, _, model = validate_model(model_filename, config=config)
    if errors:
        raise ValueError('Model file `{}` is not a valid RBA file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [SteadyStateSimulation]:
        raise NotImplementedError('`simulation_type` must be `SteadyStateSimulation`')

    # parameters
    params = []
    for function in model.parameters.functions:
        for parameter in function.parameters:
            params.append(ModelAttributeChange(
                id='{}.{}'.format(function.id, parameter.id) if native_ids else 'parameter_{}_{}'.format(function.id, parameter.id),
                name=None if native_ids else 'Value of parameter "{}" of function "{}"'.format(parameter.id, function.id),
                target='parameters.functions.{}.parameters.{}'.format(function.id, parameter.id),
                new_value=parameter.value if native_data_types else str(parameter.value),
            ))

    # simulation
    sim = SteadyStateSimulation(
        id='simulation',
        algorithm=Algorithm(
            kisao_id='KISAO_0000669',
        )
    )

    # observables
    vars = []

    vars.append(Variable(
        id=None if native_ids else 'objective',
        name=None if native_ids else 'Value of objective',
        target='objective',
    ))

    constraint_matrix = rba.ConstraintMatrix(model)

    if set(constraint_matrix.col_names).intersection(set(constraint_matrix.row_names)):
        variable_prefix = 'primal_'
        constraint_prefix = 'dual_'
    else:
        variable_prefix = ''
        constraint_prefix = ''

    for name in constraint_matrix.col_names:
        vars.append(Variable(
            id=name if native_ids else variable_prefix + name,
            name=None if native_ids else 'Primal of variable "{}"'.format(name),
            target='variables.{}'.format(name),
        ))

    for name in constraint_matrix.row_names:
        vars.append(Variable(
            id=name if native_ids else constraint_prefix + name,
            name=None if native_ids else 'Dual of constraint "{}"'.format(name),
            target='constraints.{}'.format(name),
        ))

    return (params, [sim], vars, [])
