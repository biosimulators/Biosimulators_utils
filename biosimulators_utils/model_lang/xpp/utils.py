""" Utilities for working with XPP models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-08
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config  # noqa: F401
from ...sedml.data_model import (  # noqa: F401
    SedDocument, ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, UniformTimeCourseSimulation,
    Algorithm, AlgorithmParameterChange,
    DataGenerator, Plot2D, Plot3D, Curve, Surface, AxisScale,
    Task,
    )
from ...utils.core import flatten_nested_list_of_strings
from .data_model import SIMULATION_METHOD_KISAO_MAP
from .validation import validate_model
import decimal
import math
import types  # noqa: F401

__all__ = ['get_parameters_variables_outputs_for_simulation']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    set_filename=None, parameter_filename=None, initial_conditions_filename=None,
                                                    change_level=SedDocument, native_ids=False, native_data_types=False,
                                                    config=None, max_number_of_steps=None):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file or directory of XPP ODE, set, parameters, and initial conditions
            files
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:xpp``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        set_filename (:obj:`str`, optional): path to XPP set file
        parameter_filename (:obj:`str`, optional): path to XPP parameters file
        initial_conditions_filename (:obj:`str`, optional): path to XPP initial conditions file
        change_level (:obj:`types.Type`, optional): level at which model changes will be made (:obj:`SedDocument` or :obj:`Task`)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types
        config (:obj:`Config`, optional): whether to fail on missing includes
        max_number_of_steps (:obj:`int`, optional): maximum number of steps to record

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulations of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model
    """
    # check model file exists and is valid
    errors, _, model = validate_model(model_filename,
                                      set_filename=set_filename,
                                      parameter_filename=parameter_filename,
                                      initial_conditions_filename=initial_conditions_filename,
                                      config=config)

    if errors:
        raise ValueError('Model file `{}` is not a valid XPP file or directory of XPP files.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [OneStepSimulation, UniformTimeCourseSimulation]:
        raise NotImplementedError('`simulation_type` must be `OneStepSimulation` or `UniformTimeCourseSimulation`')

    # parameters
    params = []

    for key, val in (model.get('parameters', None) or {}).items():
        params.append(ModelAttributeChange(
            id=key if native_ids else 'parameter_{}'.format(key),
            name=None if native_ids else 'Value of parameter "{}"'.format(key),
            target='{}'.format(key),
            new_value=val if native_data_types else str(val),
        ))

    aux_var_ids = [key.upper() for key in (model.get('auxiliary_variables', None) or {}).keys()]
    for key, val in (model.get('initial_conditions', None) or {}).items():
        if key.upper() not in aux_var_ids:
            params.append(ModelAttributeChange(
                id=key if native_ids else 'initial_condition_{}'.format(key),
                name=None if native_ids else 'Initial condition of "{}"'.format(key),
                target='{}'.format(key),
                new_value=val if native_data_types else str(val),
            ))

    # simulation
    simulation_method = model.get('simulation_method', None) or {}
    sim_method_id = simulation_method.get('meth', 'rungekutta').lower()
    sim_method_props = SIMULATION_METHOD_KISAO_MAP[sim_method_id]
    sim_method_kisao_id = sim_method_props['kisao_id']

    sim = UniformTimeCourseSimulation(
        id='simulation',
        algorithm=Algorithm(
            kisao_id=sim_method_kisao_id,
        )
    )

    t_0 = float(simulation_method.get('t0', 0.))
    t_output_start = float(simulation_method.get('trans', t_0))
    duration = float(simulation_method.get('total', 20.))
    d_t = float(simulation_method.get('dt', 0.05))
    n_jmp = int(float(simulation_method.get('njmp', 1)))

    if 'dt' not in sim_method_props['parameters']:
        n_jmp = simulation_method['njmp'] = 1

    sim.initial_time = t_0
    sim.output_start_time = t_output_start
    sim.output_end_time = t_0 + duration
    sim.number_of_steps = (sim.output_end_time - sim.output_start_time) / (d_t * n_jmp)
    sim.number_of_steps = round(sim.number_of_steps)

    if max_number_of_steps is not None and sim.number_of_steps > max_number_of_steps:
        if 'dt' in sim_method_props['parameters']:
            new_d_t = (sim.output_end_time - sim.output_start_time) / max_number_of_steps
            n_jmp = math.ceil(new_d_t / d_t)
        else:
            n_jmp = 1
        d_t = float(
            (decimal.Decimal(sim.output_end_time) - decimal.Decimal(sim.output_start_time))
            / decimal.Decimal(max_number_of_steps) / decimal.Decimal(n_jmp)
        )
        simulation_method['dt'] = str(d_t)
        simulation_method['njmp'] = str(n_jmp)
        sim.number_of_steps = max_number_of_steps

    for key, val in simulation_method.items():
        param_kisao_id = sim_method_props['parameters'].get(key, None)
        if param_kisao_id:
            sim.algorithm.changes.append(AlgorithmParameterChange(kisao_id=param_kisao_id,
                                                                  new_value=float(val) if native_data_types else val))

    # observables
    vars = []

    time_variable = Variable(
        id=None if native_ids else 'time',
        name=None if native_ids else 'Time',
        symbol=Symbol.time,
    )
    vars.append(time_variable)

    for key in (model.get('initial_conditions', None) or {}).keys():
        var = Variable(
            id=key if native_ids else 'dynamics_{}'.format(key),
            name=None if native_ids else 'Dynamics of "{}"'.format(key),
            target=key,
        )
        vars.append(var)

    for key in (model.get('auxiliary_variables', None) or {}).keys():
        var = Variable(
            id=key if native_ids else 'dynamics_aux_{}'.format(key),
            name=None if native_ids else 'Dynamics of "{}"'.format(key),
            target=key,
        )
        vars.append(var)

    # plots
    ode_plot = model.get('plot', None) or {}
    if 'elements' in ode_plot:
        plot_type = Plot2D
        for i_element in sorted(ode_plot['elements'].keys()):
            element = ode_plot['elements'][i_element]
            if 'z' in element:
                plot_type = Plot3D
                break

        for i_element in sorted(ode_plot['elements'].keys()):
            element = ode_plot['elements'][i_element]
            if 'x' not in element:
                element['x'] = 'T'  # what XPP uses as the default

            if 'y' not in element:
                element['y'] = 'T'  # what XPP uses as the default

            if plot_type == Plot3D:
                if 'z' not in element:
                    element['z'] = 'T'  # what XPP uses as the default

        data_generators = {}
        for var in vars:
            data_generators[(var.target or 'T').upper()] = DataGenerator(
                id='data_generator_{}'.format(var.target),
                name=var.target,
                variables=[var],
                math=var.id,
            )

        plot = plot_type(id='plot')

        for i_element in sorted(ode_plot['elements'].keys()):
            element = ode_plot['elements'][i_element]

            if plot_type == Plot2D:
                plot.curves.append(Curve(
                    id='curve_{}'.format(i_element),
                    name='{} vs {}'.format(element['y'], element['x']),
                    x_data_generator=data_generators[element['x']],
                    y_data_generator=data_generators[element['y']],
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                ))

            else:
                plot.surfaces.append(Surface(
                    id='surface_{}'.format(i_element),
                    name='{} vs {} vs {}'.format(element['z'], element['y'], element['x']),
                    x_data_generator=data_generators[element['x']],
                    y_data_generator=data_generators[element['y']],
                    z_data_generator=data_generators[element['z']],
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                    z_scale=AxisScale.linear,
                ))

        outputs = [plot]
    else:
        outputs = []

    return (params, [sim], vars, outputs)
