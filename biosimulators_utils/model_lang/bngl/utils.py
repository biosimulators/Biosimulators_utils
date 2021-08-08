""" Utilities for working with BNGL models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import (  # noqa: F401
    ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, UniformTimeCourseSimulation,
    Algorithm, AlgorithmParameterChange,
    )
from ...utils.core import flatten_nested_list_of_strings
from ...warnings import warn, BioSimulatorsWarning
from .validation import validate_model
import os
import re
import types  # noqa: F401

__all__ = ['get_parameters_variables_for_simulation']


def get_parameters_variables_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                            include_compartment_sizes_in_simulation_variables=False,
                                            include_model_parameters_in_simulation_variables=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:bngl``)
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
    if not isinstance(model_filename, str):
        raise ValueError('`{}` is not a path to a model file.'.format(model_filename))

    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist.'.format(model_filename))

    errors, _, model = validate_model(model_filename)
    if errors:
        raise ValueError('Model file `{}` is not a valid BNGL or BNGL XML file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [OneStepSimulation, UniformTimeCourseSimulation]:
        raise NotImplementedError('`simulation_type` must be `OneStepSimulation` or `UniformTimeCourseSimulation`')

    # parameters
    params = []

    if hasattr(model, 'parameters'):
        for el in model.parameters.items.values():
            escaped_el_name = escape_id(el.name)
            params.append(ModelAttributeChange(
                id='value_parameter_{}'.format(escaped_el_name),
                name='Value of parameter "{}"'.format(el.name),
                target='parameters.{}.value'.format(el.name),
                new_value=el.expr,
            ))

    if hasattr(model, 'compartments'):
        for el in model.compartments.items.values():
            params.append(ModelAttributeChange(
                id='initial_size_compartment_{}'.format(el.name),
                name='Initial size of {}-D compartment "{}"'.format(el.dim, el.name),
                target='compartments.{}.size'.format(el.name),
                new_value=el.size,
            ))

    if hasattr(model, 'species'):
        for el in model.species.items.values():
            el_pattern = el.pattern.xml['@name'].replace('::', ':')
            escaped_el_pattern = escape_id(el_pattern)
            params.append(ModelAttributeChange(
                id='initial_amount_species_{}'.format(escaped_el_pattern),
                name='Initial amount of species "{}"'.format(el_pattern),
                target='species.{}.initialCount'.format(el_pattern),
                new_value=el.count,
            ))

    if hasattr(model, 'functions'):
        for el in model.functions.items.values():
            params.append(ModelAttributeChange(
                id='expression_function_{}'.format(el.name),
                name='Expression of function "{}({})"'.format(el.name, ', '.join(el.args)),
                target='functions.{}.expression'.format(el.name),
                new_value=str(el.expr),
            ))

    # simulation
    sims = []
    for i_action, action in enumerate(model.actions.items.values()):
        args = {key: val for key, val in action.args}

        initial_time = args.get('t_start', '0.')
        output_end_time = args.get('t_end', None)
        number_of_steps = args.get('n_steps', args.get('n_output_steps', '1'))
        seed = args.get('seed', None)
        a_tol = args.get('atol', None)
        r_tol = args.get('rtol', None)
        stop_if = args.get('stop_if', None)

        if action.name == 'simulate':
            method = args.get('method', None)
            if method[0] == '"' and method[-1] == '"':
                method = method[1:-1]

        elif action.name == 'simulate_ode':
            method = 'ode'

        elif action.name == 'simulate_ssa':
            method = 'ssa'

        elif action.name == 'simulate_pla':
            method = 'pla'

        elif action.name == 'simulate_nf':
            method = 'nf'

        # elif action.name == 'parameter_scan':
        # elif action.name == 'bifurcate':

        else:
            continue

        warnings = []
        if 'sample_times' in args:
            warnings.append('Sample times cannot be translated into SED-ML.')
        if 'output_step_interval' in args:
            warnings.append('Output step interval cannot be translated into SED-ML.')
        if 'max_sim_steps' in args:
            warnings.append('Maximum simulation steps cannot be translated into SED-ML.')
        if output_end_time is None:
            warnings.append('Output end time must be set.')
        if warnings:
            warn('Skipping action {}:\n  {}'.format(i_action + 1, '\n  '.join(warnings)), BioSimulatorsWarning)
            continue

        if method == 'ode':
            algorithm_kisao_id = 'KISAO_0000019'
        elif method == 'ssa':
            algorithm_kisao_id = 'KISAO_0000029'
        elif method == 'pla':
            algorithm_kisao_id = 'KISAO_0000524'
        elif method == 'nf':
            algorithm_kisao_id = 'KISAO_0000263'

        sim = UniformTimeCourseSimulation(
            id='simulation_{}'.format(i_action),
            initial_time=float(initial_time),
            output_start_time=float(initial_time),
            output_end_time=float(output_end_time),
            number_of_steps=int(number_of_steps),
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id,
            )
        )

        if seed is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000488', new_value=seed))
        if a_tol is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000211', new_value=a_tol))
        if r_tol is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000209', new_value=r_tol))
        if stop_if is not None:
            if stop_if[0] == '"' and stop_if[-1] == '"':
                stop_if = stop_if[1:-1]
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000525', new_value=stop_if))

        sims.append(sim)

    if len(sims) == 0:
        if simulation_type == OneStepSimulation:
            sims.append(
                OneStepSimulation(
                    id='simulation',
                    step=1.,
                    algorithm=Algorithm(
                        kisao_id=algorithm_kisao_id or 'KISAO_0000019',
                    )
                )
            )
        else:
            sims.append(
                UniformTimeCourseSimulation(
                    id='simulation',
                    initial_time=0.,
                    output_start_time=0.,
                    output_end_time=1.,
                    number_of_steps=10,
                    algorithm=Algorithm(
                        kisao_id=algorithm_kisao_id or 'KISAO_0000019',
                    )
                )
            )

    # observables
    vars = []

    vars.append(Variable(
        id='time',
        name='Time',
        symbol=Symbol.time,
    ))

    if hasattr(model, 'molecule_types'):
        for el in model.molecule_types.items.values():
            el_molecule = str(el)
            escaped_el_molecule = escape_id(el_molecule)
            vars.append(Variable(
                id='amount_molecule_{}'.format(escaped_el_molecule),
                name='Dynamics of molecule "{}"'.format(el_molecule),
                target='molecules.{}.count'.format(el_molecule),
            ))

    if hasattr(model, 'species'):
        for el in model.species.items.values():
            el_pattern = el.pattern.xml['@name'].replace('::', ':')
            escaped_el_pattern = escape_id(el_pattern)
            vars.append(Variable(
                id='amount_species_{}'.format(escaped_el_pattern),
                name='Dynamics of species "{}"'.format(el_pattern),
                target='species.{}.count'.format(el_pattern),
            ))

    if hasattr(model, 'observables'):
        molecule_types = list(str(el.molecule) for el in model.molecule_types.items.values())
        for el in model.observables.items.values():
            if el.type == 'Molecules':
                for pattern in el.patterns:
                    pattern = str(pattern)
                    if pattern not in molecule_types:
                        escaped_pattern = escape_id(pattern)
                        vars.append(Variable(
                            id='amount_molecule_{}'.format(escaped_pattern),
                            name='Dynamics of molecule "{}"'.format(pattern),
                            target='molecules.{}.count'.format(pattern),
                        ))

    return (params, sims, vars)


def escape_id(id):
    return re.sub(r'[^a-zA-Z0-9_]', '_', id)
