""" Utilities for working with BNGL models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import (  # noqa: F401
    ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, UniformTimeCourseSimulation,
    Algorithm,
    )
from ...utils.core import flatten_nested_list_of_strings
from .validation import validate_model
import os
import re
import types  # noqa: F401

__all__ = ['get_parameters_variables_for_simulation']


def get_parameters_variables_for_simulation(model_filename, model_language, simulation_type, algorithm=None,
                                            include_compartment_sizes_in_simulation_variables=False,
                                            include_model_parameters_in_simulation_variables=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:bngl``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        include_compartment_sizes_in_simulation_variables (:obj:`bool`, optional): whether to include the sizes of
            non-constant SBML compartments with assignment rules among the returned SED variables
        include_model_parameters_in_simulation_variables (:obj:`bool`, optional): whether to include the values of
            non-constant SBML parameters with assignment rules among the returned SED variables

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`Simulation`: simulation of the model
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
    if simulation_type == OneStepSimulation:
        sim = OneStepSimulation(
            id='simulation',
            step=1.,
            algorithm=algorithm or Algorithm(
                kisao_id='KISAO_0000019',
            )
        )
    else:
        sim = UniformTimeCourseSimulation(
            id='simulation',
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1.,
            number_of_steps=10,
            algorithm=algorithm or Algorithm(
                kisao_id='KISAO_0000019',
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

    return (params, sim, vars)


def escape_id(id):
    return re.sub(r'[^a-zA-Z0-9_]', '_', id)
