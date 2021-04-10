""" Utilities for working with SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import (  # noqa: F401
    ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, SteadyStateSimulation, UniformTimeCourseSimulation
    )
import libsbml
import os
import types  # noqa: F401

__all__ = ['get_parameters_variables_for_simulation']


def get_parameters_variables_for_simulation(model_filename, model_language, simulation_type, algorithm,
                                            include_compartment_sizes_in_simulation_variables=False,
                                            include_model_parameters_in_simulation_variables=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        include_compartment_sizes_in_simulation_variables (:obj:`bool`, optional): whether to include the sizes of
            non-constant SBML compartments with assignment rules among the returned SED variables
        include_model_parameters_in_simulation_variables (:obj:`bool`, optional): whether to include the values of
            non-constant SBML parameters with assignment rules among the returned SED variables

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
    """
    # check model file exists
    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist'.format(model_filename))

    # read model
    doc = libsbml.readSBMLFromFile(model_filename)
    model = doc.getModel()
    if not model:
        raise ValueError('{} does not contain a valid model'.format(model_filename))

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
            id='time',
            name='Time',
            symbol=Symbol.time,
        ))

    elif simulation_type in [SteadyStateSimulation]:
        pass

    else:
        raise NotImplementedError('Simulation of type `{}` are not supported'.format(simulation_type))

    # add independent variables
    if has_fbc:
        plugin = model.getPlugin('fbc')

        has_flux = False
        has_flux_bounds = False

        if algorithm in ['KISAO_0000437', 'KISAO_0000527', 'KISAO_0000528', 'KISAO_0000554']:
            # FBA, gFBA, pFBA
            has_flux = True

        elif algorithm in ['KISAO_0000526']:
            # FVA
            has_flux_bounds = True

        else:
            raise NotImplementedError('Algorithm with KiSAO id `{}` is not supported'.format(algorithm))

        namespaces = {
            'sbml': model.getURI(),
        }
        for parameter in model.getListOfParameters():
            param_id = parameter.getId()

            params.append(ModelAttributeChange(
                id=param_id,
                name=parameter.getName() or None,
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='{}']/@value".format(param_id),
                target_namespaces=namespaces,
                new_value=format_float(parameter.getValue()),
            ))

        if has_flux:
            namespaces = {
                'sbml': model.getURI(),
                'fbc': plugin.getURI(),
            }
            obj = plugin.getActiveObjective()
            obj_id = obj.getId()
            var = Variable(
                id=obj_id,
                name=obj.getName() or None,
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
                    id=rxn_id,
                    name=reaction.getName() or None,
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
                    id=rxn_id + '_min',
                    name=reaction.getName() + ' min' if reaction.getName() else None,
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@minFlux".format(rxn_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

                var = Variable(
                    id=rxn_id + '_max',
                    name=reaction.getName() + ' max' if reaction.getName() else None,
                    target="/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='{}']/@maxFlux".format(rxn_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

    elif has_qual:
        plugin = model.getPlugin('qual')
        namespaces = {
            'sbml': model.getURI(),
            'qual': plugin.getURI(),
        }
        for species in plugin.getListOfQualitativeSpecies():
            species_id = species.getId()

            if species.isSetInitialLevel():
                params.append(ModelAttributeChange(
                    id='init_{}'.format(species_id),
                    name='initial level of {}'.format(species.getName() or species_id),
                    target=(
                        "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies"
                        "/qual:qualitativeSpecies[@qual:id='{}']/@qual:initialLevel"
                    ).format(species_id),
                    target_namespaces=namespaces,
                    new_value=str(species.getInitialLevel()),
                ))

            if not species.isSetConstant() or not species.getConstant():
                var = Variable(
                    id=species_id,
                    name=species.getName() or None,
                    target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']".format(species_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        namespaces = {
            'sbml': model.getURI(),
        }
        for comp in model.getListOfCompartments():
            comp_id = comp.getId()

            if comp.isSetSize():
                params.append(ModelAttributeChange(
                    id='init_{}'.format(comp.getId()),
                    name='initial size of {}'.format(comp.getName() or comp.getId()),
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                    new_value=format_float(comp.getSize()),
                ))

            if (
                include_compartment_sizes_in_simulation_variables
                and comp.isSetConstant()
                and not comp.getConstant()
                and model.getAssignmentRuleByVariable(comp_id)
            ):
                var = Variable(
                    id=comp_id,
                    name=comp.getName() or None,
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

    else:
        namespaces = {
            'sbml': model.getURI(),
        }
        for species in model.getListOfSpecies():
            species_id = species.getId()

            if species.isSetInitialAmount():
                params.append(ModelAttributeChange(
                    id='init_{}'.format(species_id),
                    name='initial amount of {}'.format(species.getName() or species_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']/@initialAmount".format(species_id),
                    target_namespaces=namespaces,
                    new_value=format_float(species.getInitialAmount()),
                ))
            elif species.isSetInitialConcentration():
                params.append(ModelAttributeChange(
                    id='init_{}'.format(species_id),
                    name='initial concentration of {}'.format(species.getName() or species_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']/@initialConcentration".format(species_id),
                    target_namespaces=namespaces,
                    new_value=format_float(species.getInitialConcentration()),
                ))

            if not species.isSetConstant() or not species.getConstant():
                var = Variable(
                    id=species_id,
                    name=species.getName() or None,
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']".format(species_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        for comp in model.getListOfCompartments():
            comp_id = comp.getId()

            if (
                comp.isSetSize()
                and not model.getInitialAssignmentBySymbol(comp_id)
            ):
                params.append(ModelAttributeChange(
                    id='init_{}'.format(comp.getId()),
                    name='initial size of {}'.format(comp.getName() or comp.getId()),
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                    new_value=format_float(comp.getSize()),
                ))

            if (
                include_compartment_sizes_in_simulation_variables
                and comp.isSetConstant()
                and not comp.getConstant()
                and model.getAssignmentRuleByVariable(comp_id)
            ):
                var = Variable(
                    id=comp_id,
                    name=comp.getName() or None,
                    target="/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='{}']/@size".format(comp_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        for parameter in model.getListOfParameters():
            param_id = parameter.getId()

            if not model.getInitialAssignmentBySymbol(param_id):
                params.append(ModelAttributeChange(
                    id=param_id,
                    name=parameter.getName() or None,
                    target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='{}']/@value".format(param_id),
                    target_namespaces=namespaces,
                    new_value=format_float(parameter.getValue()),
                ))

            if (
                include_model_parameters_in_simulation_variables
                and parameter.isSetConstant()
                and not parameter.getConstant()
                and model.getAssignmentRuleByVariable(param_id)
            ):
                var = Variable(
                    id=param_id + '_dynamics',
                    name='dynamics of {}'.format(parameter.getName() or param_id),
                    target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='{}']/@value".format(param_id),
                    target_namespaces=namespaces,
                )
                vars.append(var)

        for reaction in model.getListOfReactions():
            reaction_id = reaction.getId()
            kinetic_law = reaction.getKineticLaw()
            if kinetic_law:
                for parameter in kinetic_law.getListOfParameters():
                    param_id = parameter.getId()

                    if not model.getInitialAssignmentBySymbol(param_id):
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

                        params.append(ModelAttributeChange(
                            id=param_id,
                            name=parameter.getName() or None,
                            target=target,
                            target_namespaces=namespaces,
                            new_value=format_float(parameter.getValue()),
                        ))

                    if (
                        include_model_parameters_in_simulation_variables
                        and parameter.isSetConstant()
                        and not parameter.getConstant()
                        and model.getAssignmentRuleByVariable(param_id)
                    ):
                        var = Variable(
                            id=param_id + '_dynamics',
                            name='dynamics of {}'.format(parameter.getName() or param_id),
                            target=target,
                            target_namespaces=namespaces,
                        )
                        vars.append(var)

    return (params, vars)


def format_float(val):
    """ Format a float in scientific notation

    Args:
        val (:obj:`float`): value

    Returns:
        :obj:`str`: value formatted as a string
    """
    if val == int(val):
        return str(int(val))

    elif abs(val) < 1e3 and abs(val) > 1e-3:
        return str(val)

    else:
        return (
            '{:e}'
            .format(val)
            .replace('e-0', 'e-')
            .replace('e+0', 'e')
            .replace('e+', 'e')
        )
