""" Utilities for working with BNGL models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config  # noqa: F401
from ...sedml.data_model import (  # noqa: F401
    SedDocument, ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, UniformTimeCourseSimulation,
    Algorithm, AlgorithmParameterChange,
    Task,
    )
from ...utils.core import flatten_nested_list_of_strings
from ...warnings import warn, BioSimulatorsWarning
from .validation import validate_model
import numpy
import os
import re
import types  # noqa: F401

__all__ = ['get_parameters_variables_outputs_for_simulation']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    change_level=SedDocument, native_ids=False, native_data_types=False,
                                                    config=None):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:bngl``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
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
    if not isinstance(model_filename, str):
        raise ValueError('`{}` is not a path to a model file.'.format(model_filename))

    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist.'.format(model_filename))

    errors, _, model = validate_model(model_filename, config=config)
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
                id=el.name if native_ids else 'value_parameter_{}'.format(escaped_el_name),
                name=None if native_ids else 'Value of parameter "{}"'.format(el.name),
                target='parameters.{}.value'.format(el.name),
                new_value=parse_expression(el.expr, native_data_types=native_data_types),
            ))

    if hasattr(model, 'compartments'):
        for el in model.compartments.items.values():
            params.append(ModelAttributeChange(
                id=el.name if native_ids else 'initial_size_compartment_{}'.format(el.name),
                name=None if native_ids else 'Initial size of {}-D compartment "{}"'.format(el.dim, el.name),
                target='compartments.{}.size'.format(el.name),
                new_value=parse_expression(el.size, native_data_types=native_data_types),
            ))

    if hasattr(model, 'species'):
        for el in model.species.items.values():
            el_pattern = el.pattern.xml['@name'].replace('::', ':')
            escaped_el_pattern = escape_id(el_pattern)
            params.append(ModelAttributeChange(
                id=el_pattern if native_ids else 'initial_amount_species_{}'.format(escaped_el_pattern),
                name=None if native_ids else 'Initial amount of species "{}"'.format(el_pattern),
                target='species.{}.initialCount'.format(el_pattern),
                new_value=parse_expression(el.count, native_data_types=native_data_types),
            ))

    if hasattr(model, 'functions'):
        for el in model.functions.items.values():
            params.append(ModelAttributeChange(
                id=el.name if native_ids else 'expression_function_{}'.format(el.name),
                name=None if native_ids else 'Expression of function "{}({})"'.format(el.name, ', '.join(el.args)),
                target='functions.{}.expression'.format(el.name),
                new_value=str(el.expr),
            ))

    # simulation
    sims = []
    for i_action, action in enumerate(model.actions.items):
        args = action.args
        initial_time = float(args.get('t_start', '0.'))
        output_start_time = initial_time
        output_end_time = args.get('t_end', None)
        output_step_interval = args.get('output_step_interval', None)
        max_sim_steps = args.get('max_sim_steps', None)
        number_of_steps = int(float(args.get('n_steps', args.get('n_output_steps', '1'))))
        seed = args.get('seed', None)
        a_tol = args.get('atol', None)
        r_tol = args.get('rtol', None)
        stop_if = args.get('stop_if', None)

        if action.name == 'simulate':
            method = args.get('method', None)
            if method is None:
                raise ValueError('`simulate` action {} must define a `method` argument.'.format(i_action + 1))
            if method and method[0] == '"':
                method = method[1:-1]

        elif action.name == 'simulate_ode':
            method = 'ode'

        elif action.name == 'simulate_ssa':
            method = 'ssa'

        elif action.name == 'simulate_pla':
            method = 'pla'

        elif action.name == 'simulate_nf':
            method = 'nf'

        elif action.name == 'parameter_scan':
            msg = (
                'Parameter scan action {} was ignored because parameter scan actions are not supported.'
            ).format(i_action + 1)
            warn(msg, BioSimulatorsWarning)
            continue

        elif action.name == 'bifurcate':
            msg = (
                'Bifurcation analysis action {} was ignored because bifurcation analyses actions are not supported.'
            ).format(i_action + 1)
            warn(msg, BioSimulatorsWarning)
            continue

        else:
            continue  # pragma: no cover

        if 'sample_times' in args:
            sample_times_str = args['sample_times'][1:-1].strip()
            if not sample_times_str:
                raise ValueError((
                    'Sample times (`sample_times`) must be a non-empty array of floats '
                    'greater than or equal to the simulation start time (`t_start`).'
                ))  # pragma: no cover; caught by BioNetGen's own validation
            sample_times = sorted([float(sample_time.strip()) for sample_time in args['sample_times'][1:-1].strip().split(',')])
            output_start_time = sample_times[0]
            output_end_time = sample_times[-1]
            if len(set(numpy.diff(sample_times))) <= 1:
                number_of_steps = len(sample_times) - 1
            else:
                msg = (
                    'Non-uniformly-distributed sample times (`sample_times`) for action {} were ignored '
                    'because they cannot be translated into SED-ML.'
                ).format(i_action + 1)
                warn(msg, BioSimulatorsWarning)
        if output_end_time is None:
            raise ValueError('`Simulation end time (`t_end`) must be set for `{}` action {}.'.format(action.name, i_action + 1))

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
            initial_time=initial_time,
            output_start_time=output_start_time,
            output_end_time=float(output_end_time),
            number_of_steps=number_of_steps,
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id,
            )
        )

        if seed is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000488', new_value=int(float(seed)) if native_data_types else str(seed)))
        if a_tol is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000211', new_value=float(a_tol) if native_data_types else str(a_tol)))
        if r_tol is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000209', new_value=float(r_tol) if native_data_types else str(r_tol)))
        if output_step_interval is not None:
            msg = (
                'Output step interval (`output_step_interval`) was ignored for action {} because this cannot be '
                'encoded into a SED-ML uniform time course.'
            ).format(i_action + 1)
            warn(msg, BioSimulatorsWarning)
        if max_sim_steps is not None:
            sim.algorithm.changes.append(AlgorithmParameterChange(
                kisao_id='KISAO_0000415', new_value=int(float(max_sim_steps)) if native_data_types else str(max_sim_steps)))
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
        id=None if native_ids else 'time',
        name=None if native_ids else 'Time',
        symbol=Symbol.time,
    ))

    if hasattr(model, 'molecule_types'):
        for el in model.molecule_types.items.values():
            el_molecule = str(el)
            escaped_el_molecule = escape_id(el_molecule)

            multiple_states = False
            for component in el.molecule.components:
                if len(component.states) > 1:
                    multiple_states = True
                    break

            if not multiple_states:
                vars.append(Variable(
                    id=el_molecule if native_ids else 'amount_molecule_{}'.format(escaped_el_molecule),
                    name=None if native_ids else 'Dynamics of molecule "{}"'.format(el_molecule),
                    target='molecules.{}.count'.format(el_molecule),
                ))

    if hasattr(model, 'species'):
        for el in model.species.items.values():
            el_pattern = el.pattern.xml['@name'].replace('::', ':')
            escaped_el_pattern = escape_id(el_pattern)
            vars.append(Variable(
                id=el_pattern if native_ids else 'amount_species_{}'.format(escaped_el_pattern),
                name=None if native_ids else 'Dynamics of species "{}"'.format(el_pattern),
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
                            id=pattern if native_ids else 'amount_molecule_{}'.format(escaped_pattern),
                            name=None if native_ids else 'Dynamics of molecule "{}"'.format(pattern),
                            target='molecules.{}.count'.format(pattern),
                        ))

    return (params, sims, vars, [])


def escape_id(id):
    return re.sub(r'[^a-zA-Z0-9_]', '_', id)


def parse_expression(value, native_data_types=False):
    """ Optionally parse an expression

    Args:
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types

    Returns:
        :obj:`object`: expression or parsed expression
    """
    if native_data_types:
        try:
            return float(value)
        except ValueError:
            return str(value)
    else:
        return str(value)
