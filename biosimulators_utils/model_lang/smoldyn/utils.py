""" Utilities for working with Smoldyn models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import (SedDocument, ModelAttributeChange, Variable,  # noqa: F401
                                 Symbol, Simulation, UniformTimeCourseSimulation, Algorithm,
                                 Task)
from ...utils.core import flatten_nested_list_of_strings
from .validation import validate_model
from smoldyn.biosimulators.utils import read_simulation
import os
import re
import types  # noqa: F401

__all__ = ['get_parameters_variables_outputs_for_simulation']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    change_level=SedDocument, native_ids=False, native_data_types=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        change_level (:obj:`types.Type`, optional): level at which model changes will be made (:obj:`SedDocument` or :obj:`Task`)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types

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
        raise ValueError('Model file `{}` is not a valid Smoldyn file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [UniformTimeCourseSimulation]:
        raise NotImplementedError('`simulation_type` must be `OneStepSimulation` or `UniformTimeCourseSimulation`')

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

    # get parameters and observables
    model = read_simulation(model_filename)

    params = []
    for instruction in model.instructions:
        if not (
            instruction.macro.startswith('define ')
            # or instruction.macro.startswith('define_global ')
            or instruction.macro.startswith('difc ')
            or instruction.macro.startswith('difc_rule ')
            or instruction.macro.startswith('difm ')
            or instruction.macro.startswith('difm_rule ')
            or instruction.macro.startswith('drift ')
            or instruction.macro.startswith('drift_rule ')
            or instruction.macro.startswith('surface_drift ')
            or instruction.macro.startswith('surface_drift_rule ')
        ):
            continue

        if native_data_types:
            id = instruction.macro.partition(' ')[2]
        else:
            id = re.sub(r'[^a-zA-Z0-9_]', '_', instruction.macro)

        if native_data_types:
            if (
                instruction.macro.startswith('define ')
                # or instruction.macro.startswith('define_global ')
                or instruction.macro.startswith('difc ')
                or instruction.macro.startswith('difc_rule ')
            ):
                new_value = float(instruction.arguments)
            elif (
                instruction.macro.startswith('difm ')
                or instruction.macro.startswith('difm_rule ')
                or instruction.macro.startswith('drift ')
                or instruction.macro.startswith('drift_rule ')
                or instruction.macro.startswith('surface_drift ')
                or instruction.macro.startswith('surface_drift_rule ')
            ):
                new_value = [float(val) for val in instruction.arguments.split(' ')]
        else:
            new_value = instruction.arguments

        if instruction.macro.partition(' ')[2] != 'all':
            params.append(ModelAttributeChange(
                id=id,
                name=None if native_ids else instruction.description,
                target=instruction.macro,
                new_value=new_value,
            ))

    smoldyn_model.addOutputData('counts')
    smoldyn_model.addCommand(cmd='molcount counts', cmd_type='E')
    for compartment in model.compartments:
        data_id = 'counts_cmpt_' + compartment
        smoldyn_model.addOutputData(data_id)
        smoldyn_model.addCommand(cmd='molcountincmpt ' + compartment + ' ' + data_id, cmd_type='E')
    for surface in model.surfaces:
        data_id = 'counts_surf_' + surface
        smoldyn_model.addOutputData(data_id)
        smoldyn_model.addCommand(cmd='molcountonsurf ' + surface + ' ' + data_id, cmd_type='E')

    smoldyn_model.run(stop=1e-12, dt=1., overwrite=True, display=False, quit_at_end=False)

    data_id = 'counts'
    species_counts = smoldyn_model.getOutputData(data_id, True)[0][1:]
    for species, count in zip(model.species, species_counts):
        params.append(ModelAttributeChange(
            id=species if native_ids else 'initial_count_species_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species)),
            name=None if native_ids else 'Initial count of species "{}"'.format(species),
            target="fixmolcount {}".format(species),
            new_value=count if native_data_types else str(count),
        ))

    for compartment in model.compartments:
        data_id = 'counts_cmpt_' + compartment
        species_counts = smoldyn_model.getOutputData(data_id, True)[0][1:]
        for species, count in zip(model.species, species_counts):
            params.append(ModelAttributeChange(
                id="{}.{}".format(species, compartment) if native_ids else 'initial_count_species_{}_compartment_{}'.format(
                    re.sub('[^a-zA-Z0-9_]', '_', species), compartment),
                name=None if native_ids else 'Initial count of species "{}" in compartment "{}"'.format(species, compartment),
                target="fixmolcountincmpt {} {}".format(species, compartment),
                new_value=new_value,
            ))

    for surface in model.surfaces:
        data_id = 'counts_surf_' + surface
        species_counts = smoldyn_model.getOutputData(data_id, True)[0][1:]
        for species, count in zip(model.species, species_counts):
            params.append(ModelAttributeChange(
                id="{}.{}".format(species, surface) if native_ids else 'initial_count_species_{}_surface_{}'.format(
                    re.sub('[^a-zA-Z0-9_]', '_', species), surface),
                name=None if native_ids else 'Initial count of species "{}" in surface "{}"'.format(species, surface),
                target="fixmolcountonsurf {} {}".format(species, surface),
                new_value=new_value,
            ))

    vars = []
    vars.append(Variable(
        id=None if native_ids else 'time',
        name=None if native_ids else 'Time',
        symbol=Symbol.time.value,
    ))
    for species in model.species:
        vars.append(Variable(
            id=species if native_ids else 'count_species_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species)),
            name=None if native_ids else 'Count of species "{}"'.format(species),
            target="molcount {}".format(species),
        ))
        for compartment in model.compartments:
            vars.append(Variable(
                id="{}.{}".format(species, compartment) if native_ids else 'count_species_{}_compartment_{}'.format(
                    re.sub('[^a-zA-Z0-9_]', '_', species), compartment),
                name=None if native_ids else 'Count of species "{}" in compartment "{}"'.format(species, compartment),
                target="molcountincmpt {} {}".format(species, compartment),
            ))
        for surface in model.surfaces:
            vars.append(Variable(
                id="{}.{}".format(species, surface) if native_ids else 'count_species_{}_surface_{}'.format(
                    re.sub('[^a-zA-Z0-9_]', '_', species), surface),
                name=None if native_ids else 'Count of species "{}" in surface "{}"'.format(species, surface),
                target="molcountonsurf {} {}".format(species, surface),
            ))

    return (params, [sim], vars, [])
