""" Utilities for working with XPP models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-08
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import (  # noqa: F401
    ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, UniformTimeCourseSimulation,
    Algorithm, AlgorithmParameterChange,
    )
from ...utils.core import flatten_nested_list_of_strings
from .data_model import SIMULATION_METHOD_KISAO_MAP
from .validation import validate_model
import types  # noqa: F401

__all__ = ['get_parameters_variables_for_simulation']


def get_parameters_variables_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                            include_compartment_sizes_in_simulation_variables=False,
                                            include_model_parameters_in_simulation_variables=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:xpp``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        include_compartment_sizes_in_simulation_variables (:obj:`bool`, optional): whether to include the sizes of
            non-constant SBML compartments with assignment rules among the returned SED variables
        include_model_parameters_in_simulation_variables (:obj:`bool`, optional): whether to include the values of
            non-constant SBML parameters with assignment rules among the returned SED variables

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulations of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
    """
    # check model file exists and is valid
    errors, _, model = validate_model(model_filename)
    if errors:
        raise ValueError('Model file `{}` is not a valid XPP file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [OneStepSimulation, UniformTimeCourseSimulation]:
        raise NotImplementedError('`simulation_type` must be `OneStepSimulation` or `UniformTimeCourseSimulation`')

    # parameters
    params = []

    for key, val in model['parameters'].items():
        params.append(ModelAttributeChange(
            id='parameter_{}'.format(key),
            name='Value of parameter "{}"'.format(key),
            target='parameters.{}'.format(key),
            new_value=str(val),
        ))

    for key, val in model['initial_conditions'].items():
        params.append(ModelAttributeChange(
            id='initial_condition_{}'.format(key),
            name='Initial condition of "{}"'.format(key),
            target='initialConditions.{}'.format(key),
            new_value=str(val),
        ))

    # simulation
    sim_method_id = model['simulation_method'].get('meth', 'rungekutta').lower()
    sim_method_props = SIMULATION_METHOD_KISAO_MAP[sim_method_id]
    sim_method_kisao_id = sim_method_props['kisao_id']

    sim = UniformTimeCourseSimulation(
        id='simulation',
        algorithm=Algorithm(
            kisao_id=sim_method_kisao_id,
        )
    )

    t_0 = float(model['simulation_method'].get('t0', 0.))
    duration = float(model['simulation_method'].get('total', 20.))
    d_t = float(model['simulation_method'].get('dt', 0.05))
    n_jmp = float(model['simulation_method'].get('njmp', 1))

    sim.initial_time = t_0
    sim.output_start_time = t_0
    sim.output_end_time = sim.initial_time + duration
    sim.number_of_steps = duration / (d_t * n_jmp)
    sim.number_of_steps = round(sim.number_of_steps)

    for key, val in model['simulation_method'].items():
        param_kisao_id = sim_method_props['parameters'].get(key, None)
        if param_kisao_id:
            sim.algorithm.changes.append(AlgorithmParameterChange(kisao_id=param_kisao_id, new_value=val))

    # observables
    vars = []

    vars.append(Variable(
        id='time',
        name='Time',
        symbol=Symbol.time,
    ))

    for key in model['initial_conditions'].keys():
        vars.append(Variable(
            id='dynamics_{}'.format(key),
            name='Dynamics of "{}"'.format(key),
            target=key,
        ))

    return (params, [sim], vars)
