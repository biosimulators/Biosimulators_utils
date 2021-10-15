""" Utilities for working with SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import (  # noqa: F401
    SedDocument, ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, SteadyStateSimulation, UniformTimeCourseSimulation,
    Algorithm, Task,
    )
from ...utils.core import format_float, flatten_nested_list_of_strings
from .validation import validate_model
import os
import re
import types  # noqa: F401
import typing

__all__ = ['get_parameters_variables_outputs_for_simulation', 'get_package_namespace']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    change_level=SedDocument,
                                                    native_ids=False, native_data_types=False,
                                                    include_local_parameters_in_task_level_simulation_parameters=False,
                                                    include_model_parameters_in_simulation_variables=False,
                                                    include_compartment_sizes_in_simulation_variables=False,
                                                    include_reaction_fluxes_in_kinetic_simulation_variables=False,
                                                    validate=True, validate_consistency=True):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        change_level (:obj:`types.Type`, optional): level at which model changes will be made (:obj:`SedDocument` or :obj:`Task`)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return ``new_value`` in their native data types
        include_local_parameters_in_task_level_simulation_parameters (:obj:`bool`, optional): whether to include the local parameters
            among the returned SED model changes for SED tasks
        include_model_parameters_in_simulation_variables (:obj:`bool`, optional): whether to include the values of
            non-constant SBML parameters with assignment rules among the returned SED variables
        include_compartment_sizes_in_simulation_variables (:obj:`bool`, optional): whether to include the sizes of
            non-constant SBML compartments with assignment rules among the returned SED variables
        include_reaction_fluxes_in_kinetic_simulation_variables (:obj:`bool`, optional): whether to include reaction fluxes
            among the returned SED variables for kinetic simulations
        validate (:obj:`str`, optional): whether to validate the model
        validate_consistency (:obj:`str`, optional): whether to check the consistency of the model

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulation of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model
    """
    # check model file exists
    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist'.format(model_filename))

    # check change level
    if change_level not in [SedDocument, Task]:
        msg = 'Change level {} is not supported. Changes can only made at the SED document or task level.'.format(change_level)
        raise NotImplementedError(msg)

    # read model
    errors, _, doc = validate_model(model_filename, validate_consistency=validate and validate_consistency)
    if not doc or (validate and errors):
        raise ValueError('Model file `{}` is not a valid SBML file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))
    model = doc.getModel()

    # determine plugin usage
    has_fbc = False
    has_qual = False
    has_other = False

    plugin_names = []
    for i_plugin in range(model.getNumPlugins()):
        plugin = model.getPlugin(i_plugin)
        plugin_name = plugin.getPackageName()
        plugin_names.append(plugin_name)
        if plugin_name == 'fbc':
            has_fbc = True
        elif plugin_name == 'qual':
            has_qual = True
        elif plugin_name not in ['layout', 'math', 'render', 'spatial', 'annot', 'req']:
            has_other = True

    if has_other or (has_fbc and has_qual):
        raise NotImplementedError('Unable to get the observable variables for a model that uses these plugins:\n  {}'.format(
            '\n  '.join(sorted(plugin_names))))

    # initialize dependent parameters and independent variables
    params = []
    vars = []

    # add time to vars
    if simulation_type in [OneStepSimulation, UniformTimeCourseSimulation]:
        if has_fbc:
            raise NotImplementedError('One step and time course simulations are not supported for FBC models')

        vars.append(Variable(
            id=None if native_ids else 'time',
            name=None if native_ids else 'Time',
            symbol=Symbol.time,
        ))

    elif simulation_type in [SteadyStateSimulation]:
        pass

    else:
        raise NotImplementedError('Simulation of type `{}` are not supported'.format(simulation_type))

    # add independent variables
    if has_fbc:
        sim = SteadyStateSimulation(
            id='simulation',
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id or 'KISAO_0000437',
            ),
        )

        plugin = model.getPlugin('fbc')

        has_flux = False
        has_flux_bounds = False

        if sim.algorithm.kisao_id in ['KISAO_0000437', 'KISAO_0000527', 'KISAO_0000528', 'KISAO_0000554']:
            # FBA, gFBA, pFBA
            has_flux = True

        elif sim.algorithm.kisao_id in ['KISAO_0000526']:
            # FVA
            has_flux_bounds = True

        else:
            raise NotImplementedError('Algorithm with KiSAO id `{}` is not supported'.format(algorithm_kisao_id))

        if change_level == SedDocument:
            namespaces = {
                'sbml': model.getURI(),
            }
            for parameter in model.getListOfParameters():
                param_id = parameter.getId()

                if not model.getInitialAssignmentBySymbol(param_id) and not model.getAssignmentRuleByVariable(param_id):
                    params.append(ModelAttributeChange(
                        id=param_id if native_ids else 'value_parameter_' + param_id,
                        name=(
                            parameter.getName() or None
                            if native_ids else
                            'Value of parameter "{}"'.format(parameter.getName() or param_id)
                        ),
                        target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='{}']/@value".format(param_id),
                        target_namespaces=namespaces,
                        new_value=parameter.getValue() if native_data_types else format_float(parameter.getValue()),
                    ))

        elif change_level == Task:
            namespaces = {
                'sbml': model.getURI(),
                'fbc': plugin.getURI(),
            }
            for reaction in model.getListOfReactions():
                reaction_fbc = reaction.getPlugin('fbc')
                lower_flux_bound = reaction_fbc.getLowerFluxBound()
                upper_flux_bound = reaction_fbc.getUpperFluxBound()
                lower_flux_bound_param = model.getParameter(lower_flux_bound)
                upper_flux_bound_param = model.getParameter(upper_flux_bound)
                lower_flux_bound = lower_flux_bound_param.getValue()
                upper_flux_bound = upper_flux_bound_param.getValue()
                if not native_data_types:
                    lower_flux_bound = str(lower_flux_bound)
                    upper_flux_bound = str(upper_flux_bound)

                rxn_id = reaction.getId()
                if (
                    not model.getInitialAssignmentBySymbol(lower_flux_bound_param.getId())
                    and not model.getAssignmentRuleByVariable(lower_flux_bound_param.getId())
                ):
                    params.append(ModelAttributeChange(
                        id=rxn_id if native_ids else 'lower_bound_reaction_' + rxn_id,
                        name=(
                            reaction.getName() or None
                            if native_ids else
                            'Lower bound of reaction "{}"'.format(reaction.getName() or rxn_id)
                        ),
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@fbc:lowerFluxBound".format(rxn_id),
                        target_namespaces=namespaces,
                        new_value=lower_flux_bound,
                    ))
                if (
                    not model.getInitialAssignmentBySymbol(upper_flux_bound_param.getId())
                    and not model.getAssignmentRuleByVariable(upper_flux_bound_param.getId())
                ):
                    params.append(ModelAttributeChange(
                        id=rxn_id if native_ids else 'upper_bound_reaction_' + rxn_id,
                        name=(
                            reaction.getName() or None
                            if native_ids else
                            'Upper bound of reaction "{}"'.format(reaction.getName() or rxn_id)
                        ),
                        target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@fbc:upperFluxBound".format(rxn_id),
                        target_namespaces=namespaces,
                        new_value=upper_flux_bound,
                    ))

        if has_flux:
            namespaces = {
                'sbml': model.getURI(),
                'fbc': plugin.getURI(),
            }
            obj = plugin.getActiveObjective()
            obj_id = obj.getId()
            var = Variable(
                id=obj_id if native_ids else 'value_objective_' + obj_id,
                name=obj.getName() or None if native_ids else 'Value of objective "{}"'.format(obj.getName() or obj_id),
                target="/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='{}']/@value".format(obj_id),
                target_namespaces=namespaces,
            )
            vars.append(var)

            namespaces = {
                'sbml': model.getURI(),
            }
            for reaction in model.getListOfReactions():
                rxn_id = reaction.getId()
                var = Variable(
                    id=rxn_id if native_ids else 'flux_reaction_' + rxn_id,
                    name=reaction.getName() or None if native_ids else 'Flux of reaction "{}"'.format(reaction.getName() or rxn_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@flux".format(rxn_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        if has_flux_bounds:
            namespaces = {
                'sbml': model.getURI(),
            }

            for reaction in model.getListOfReactions():
                rxn_id = reaction.getId()

                var = Variable(
                    id=rxn_id if native_ids else 'min_flux_reaction_' + rxn_id,
                    name=reaction.getName() or None if native_ids else 'Minimum flux of reaction "{}"'.format(reaction.getName() or rxn_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@minFlux".format(rxn_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

                var = Variable(
                    id=rxn_id if native_ids else 'max_flux_reaction_' + rxn_id,
                    name=reaction.getName() or None if native_ids else 'Maximum flux of reaction "{}"'.format(reaction.getName() or rxn_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@maxFlux".format(rxn_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

    elif has_qual:
        if simulation_type == OneStepSimulation:
            sim = OneStepSimulation(
                step=1.,
                algorithm=Algorithm(
                    kisao_id=algorithm_kisao_id or 'KISAO_0000449',
                ),
            )
        elif simulation_type == SteadyStateSimulation:
            sim = SteadyStateSimulation(
                id='simulation',
                algorithm=Algorithm(
                    kisao_id=algorithm_kisao_id or 'KISAO_0000659',
                ),
            )
        else:
            sim = UniformTimeCourseSimulation(
                id='simulation',
                initial_time=0.,
                output_start_time=0.,
                output_end_time=10.,
                number_of_steps=10,
                algorithm=Algorithm(
                    kisao_id=algorithm_kisao_id or 'KISAO_0000449',
                ),
            )

        plugin = model.getPlugin('qual')
        namespaces = {
            'sbml': model.getURI(),
            'qual': plugin.getURI(),
        }
        for species in plugin.getListOfQualitativeSpecies():
            species_id = species.getId()

            if species.isSetInitialLevel():
                if not model.getInitialAssignmentBySymbol(species_id) and not model.getAssignmentRuleByVariable(species_id):
                    params.append(ModelAttributeChange(
                        id=species_id if native_ids else 'init_level_species_{}'.format(species_id),
                        name=(
                            species.getName() or None
                            if native_ids else
                            'Initial level of species "{}"'.format(species.getName() or species_id)
                        ),
                        target=(
                            "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies"
                            "/qual:qualitativeSpecies[@qual:id='{}']/@qual:initialLevel"
                        ).format(species_id),
                        target_namespaces=namespaces,
                        new_value=species.getInitialLevel() if native_data_types else str(species.getInitialLevel()),
                    ))

            if not species.isSetConstant() or not species.getConstant():
                var = Variable(
                    id=species_id if native_ids else 'level_species_' + species_id,
                    name=species.getName() or None if native_ids else 'Level of species "{}"'.format(species.getName() or species_id),
                    target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']".format(species_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        namespaces = {
            'sbml': model.getURI(),
        }
        for comp in model.getListOfCompartments():
            comp_id = comp.getId()

            if comp.isSetSize() and (not model.getInitialAssignmentBySymbol(comp_id) and not model.getAssignmentRuleByVariable(comp_id)):
                params.append(ModelAttributeChange(
                    id=comp.getId() if native_ids else 'init_size_compartment_{}'.format(comp.getId()),
                    name=(
                        comp.getName() or None
                        if native_ids else
                        'Initial size of compartment "{}"'.format(comp.getName() or comp.getId())
                    ),
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                    new_value=comp.getSize() if native_data_types else format_float(comp.getSize()),
                ))

            if (
                include_compartment_sizes_in_simulation_variables
                and comp.isSetConstant()
                and not comp.getConstant()
                and model.getAssignmentRuleByVariable(comp_id)
            ):
                var = Variable(
                    id=comp_id if native_ids else 'size_compartment_' + comp_id,
                    name=comp.getName() or None if native_ids else 'Size of compartment "{}"'.format(comp.getName() or comp_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

    else:
        if simulation_type == OneStepSimulation:
            sim = OneStepSimulation(
                id='simulation',
                step=1.,
                algorithm=Algorithm(
                    kisao_id=algorithm_kisao_id or 'KISAO_0000019',
                ),
            )
        elif simulation_type == SteadyStateSimulation:
            sim = SteadyStateSimulation(
                id='simulation',
                algorithm=Algorithm(
                    kisao_id=algorithm_kisao_id or 'KISAO_0000408',
                ),
            )
        else:
            sim = UniformTimeCourseSimulation(
                id='simulation',
                initial_time=0.,
                output_start_time=0.,
                output_end_time=1.,
                number_of_steps=10,
                algorithm=Algorithm(
                    kisao_id=algorithm_kisao_id or 'KISAO_0000019',
                ),
            )

        namespaces = {
            'sbml': model.getURI(),
        }
        for species in model.getListOfSpecies():
            species_id = species.getId()

            if not model.getInitialAssignmentBySymbol(species_id) and not model.getAssignmentRuleByVariable(species_id):
                if species.isSetInitialAmount():
                    params.append(ModelAttributeChange(
                        id=species_id if native_ids else 'init_amount_species_{}'.format(species_id),
                        name=(
                            species.getName() or None
                            if native_ids else
                            'Initial amount of species "{}"'.format(species.getName() or species_id)
                        ),
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']/@initialAmount".format(species_id),
                        target_namespaces=namespaces,
                        new_value=species.getInitialAmount() if native_data_types else format_float(species.getInitialAmount()),
                    ))
                elif species.isSetInitialConcentration():
                    params.append(ModelAttributeChange(
                        id=species_id if native_ids else 'init_conc_species_{}'.format(species_id),
                        name=(
                            species.getName() or None
                            if native_ids else
                            'Initial concentration of species "{}"'.format(species.getName() or species_id)
                        ),
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']/@initialConcentration".format(species_id),
                        target_namespaces=namespaces,
                        new_value=(
                            species.getInitialConcentration()
                            if native_data_types else
                            format_float(species.getInitialConcentration())
                        ),
                    ))

            if not species.isSetConstant() or not species.getConstant():
                var = Variable(
                    id=species_id if native_ids else 'dynamics_species_' + species_id,
                    name=species.getName() or None if native_ids else 'Dynamics of species "{}"'.format(species.getName() or species_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']".format(species_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        for comp in model.getListOfCompartments():
            comp_id = comp.getId()

            if (
                comp.isSetSize()
                and not model.getInitialAssignmentBySymbol(comp_id)
                and not model.getAssignmentRuleByVariable(comp_id)
            ):
                params.append(ModelAttributeChange(
                    id=(
                        comp.getId()
                        if native_ids else
                        'init_size_compartment_{}'.format(comp.getId())
                    ),
                    name=(
                        comp.getName() or None
                        if native_ids else
                        'Initial size of compartment "{}"'.format(comp.getName() or comp.getId())
                    ),
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                    new_value=comp.getSize() if native_data_types else format_float(comp.getSize()),
                ))

            if (
                include_compartment_sizes_in_simulation_variables
                and comp.isSetConstant()
                and not comp.getConstant()
                and model.getAssignmentRuleByVariable(comp_id)
            ):
                var = Variable(
                    id=comp_id if native_ids else 'size_compartment_' + comp_id,
                    name=comp.getName() or None if native_ids else 'Size of compartment "{}"'.format(comp.getName() or comp_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        for parameter in model.getListOfParameters():
            param_id = parameter.getId()

            if not model.getInitialAssignmentBySymbol(param_id) and not model.getAssignmentRuleByVariable(param_id):
                params.append(ModelAttributeChange(
                    id=param_id if native_ids else 'value_parameter_' + param_id,
                    name=parameter.getName() or None if native_ids else 'Value of parameter "{}"'.format(parameter.getName() or param_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='{}']/@value".format(param_id),
                    target_namespaces=namespaces,
                    new_value=parameter.getValue() if native_data_types else format_float(parameter.getValue()),
                ))

            if (
                include_model_parameters_in_simulation_variables
                and parameter.isSetConstant()
                and not parameter.getConstant()
                and model.getAssignmentRuleByVariable(param_id)
            ):
                var = Variable(
                    id=param_id if native_ids else 'value_parameter_' + param_id,
                    name=parameter.getName() or None if native_ids else 'Value of parameter "{}"'.format(parameter.getName() or param_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='{}']/@value".format(param_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        for reaction in model.getListOfReactions():
            reaction_id = reaction.getId()
            kinetic_law = reaction.getKineticLaw()
            if kinetic_law and (change_level == SedDocument or include_local_parameters_in_task_level_simulation_parameters):
                for parameter in kinetic_law.getListOfParameters():
                    param_id = parameter.getId()

                    if model.getLevel() >= 3:
                        target = (
                            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/sbml:kineticLaw"
                            "/sbml:listOfLocalParameters/sbml:localParameter[@id='{}']/@value"
                        ).format(reaction_id, param_id)
                    else:
                        target = (
                            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/sbml:kineticLaw"
                            "/sbml:listOfParameters/sbml:parameter[@id='{}']/@value"
                        ).format(reaction_id, param_id)

                    if not model.getInitialAssignmentBySymbol(param_id) and not model.getAssignmentRuleByVariable(param_id):
                        params.append(ModelAttributeChange(
                            id=param_id if native_ids else 'value_parameter_' + param_id,
                            name=parameter.getName() or None if native_ids else 'Value of parameter "{}" of reaction "{}"'.format(
                                parameter.getName() or param_id, reaction.getName() or reaction_id),
                            target=target,
                            target_namespaces=namespaces,
                            new_value=parameter.getValue() if native_data_types else format_float(parameter.getValue()),
                        ))

                    if (
                        include_model_parameters_in_simulation_variables
                        and parameter.isSetConstant()
                        and not parameter.getConstant()
                        and model.getAssignmentRuleByVariable(param_id)
                    ):
                        var = Variable(
                            id=param_id if native_ids else 'value_parameter_' + param_id,
                            name=parameter.getName() or None if native_ids else 'Value of parameter "{}" of reaction "{}"'.format(
                                parameter.getName() or param_id, reaction.getName() or reaction_id),
                            target=target,
                            target_namespaces=namespaces,
                        )
                        vars.append(var)

            if include_reaction_fluxes_in_kinetic_simulation_variables:
                var = Variable(
                    id=(
                        reaction_id
                        if native_ids else
                        'flux_reaction_' + reaction_id
                    ),
                    name=(
                        reaction.getName() or None
                        if native_ids else
                        'Flux of reaction "{}"'.format(reaction.getName() or reaction_id)
                    ),
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']".format(reaction_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

    return (params, [sim], vars, [])


def get_package_namespace(package: str, namespaces: typing.Dict[typing.Union[str, None], str]) -> typing.Tuple[str, str]:
    """ Get the prefix and URI for the namespace of an SBML package

    Args:
        package (:obj:`str`): SBML package id (e.g., ``fbc``, ``qual``)
        namespaces (:obj:`dict`): dictionary that maps namespace prefixes to URIs

    Returns:
        :obj:`tuple`:

            * :obj:`str`: prefix
            * :obj:`str`: URI
    """
    sbml_fbc_prefixes = set()
    sbml_fbc_uris = set()
    for prefix, uri in namespaces.items():
        if uri and re.match(r'^http://www.sbml.org/sbml/level\d+/version\d+/{}/version\d+$'.format(package), uri):
            sbml_fbc_prefixes.add(prefix)
            sbml_fbc_uris.add(uri)
    if len(sbml_fbc_uris) != 1:
        raise ValueError('Namespaces must include 1 SBML {} namespace.'.format(package))
    return list(sbml_fbc_prefixes)[0], list(sbml_fbc_uris)[0]
