""" Utilities for working with Smoldyn models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import (ModelAttributeChange, Variable,  # noqa: F401
                                 Symbol, Simulation, UniformTimeCourseSimulation, Algorithm)
from ...utils.core import flatten_nested_list_of_strings
from .validation import validate_model
from smoldyn.biosimulators.utils import read_simulation
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
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        include_compartment_sizes_in_simulation_variables (:obj:`bool`, optional): whether to include the sizes of
            non-constant SBML compartments with assignment rules among the returned SED variables
        include_model_parameters_in_simulation_variables (:obj:`bool`, optional): whether to include the values of
            non-constant SBML parameters with assignment rules among the returned SED variables

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulation of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
    """
    # check model file exists and is valid
    if not isinstance(model_filename, str):
        raise ValueError('`{}` is not a path to a model file.'.format(model_filename))

    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist.'.format(model_filename))

    errors, _, (smoldyn_model, model_config) = validate_model(model_filename)
    if errors:
        raise ValueError('Model file `{}` is not a valid BNGL or BNGL XML file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [UniformTimeCourseSimulation]:
        raise NotImplementedError('`simulation_type` must be `OneStepSimulation` or `UniformTimeCourseSimulation`')

    # get parameters and observables
    model = read_simulation(model_filename)

    params = []
    for instruction in model.instructions:
        params.append(ModelAttributeChange(
            id=instruction.id,
            name=instruction.description,
            target=instruction.macro,
            new_value=instruction.arguments,
        ))

    sim = UniformTimeCourseSimulation(
        id='simulation',
        initial_time=smoldyn_model.start,
        output_start_time=smoldyn_model.start,
        output_end_time=smoldyn_model.stop,
        number_of_steps=int((smoldyn_model.stop - smoldyn_model.start) / smoldyn_model.dt),
        algorithm=Algorithm(
            kisao_id=algorithm_kisao_id or 'KISAO_0000057',
        ),
    )

    vars = []
    vars.append(Variable(
        id='time',
        name='Time',
        symbol=Symbol.time.value,
    ))
    for species in model.species:
        vars.append(Variable(
            id='count_species_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species)),
            name='Count of species "{}"'.format(species),
            target="molcount {}".format(species),
        ))
        for compartment in model.compartments:
            vars.append(Variable(
                id='count_species_{}_compartment_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species), compartment),
                name='Count of species "{}" in compartment "{}"'.format(species, compartment),
                target="molcountincmpt {} {}".format(species, compartment),
            ))
        for surface in model.surfaces:
            vars.append(Variable(
                id='count_species_{}_surface_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species), surface),
                name='Count of species "{}" in surface "{}"'.format(species, surface),
                target="molcountonsurf {} {}".format(species, surface),
            ))

    return (params, [sim], vars)
