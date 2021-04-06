""" Utilities for working with SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import Variable, Symbol, OneStepSimulation, SteadyStateSimulation, UniformTimeCourseSimulation
import libsbml
import os

__all__ = ['get_variables_for_simulation']


{
    'KISAO_0000437': {

    },
}


def get_variables_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)

    Returns:
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

    # initialize vars
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

        if algorithm_kisao_id in ['KISAO_0000437', 'KISAO_0000527', 'KISAO_0000528', 'KISAO_0000554']:
            # FBA, gFBA, pFBA
            has_flux = True

        elif algorithm_kisao_id in ['KISAO_0000526']:
            # FVA
            has_flux_bounds = True

        else:
            raise NotImplementedError('Algorithm with KiSAO id `{}` is not supported'.format(algorithm_kisao_id))

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
            s_id = species.getId()
            var = Variable(
                id=s_id,
                name=species.getName() or None,
                target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='{}']".format(s_id),
                target_namespaces=namespaces,
            )
            vars.append(var)

    else:
        namespaces = {
            'sbml': model.getURI(),
        }
        for species in model.getListOfSpecies():
            var_id = species.getId()
            var = Variable(
                id=var_id,
                name=species.getName() or None,
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='{}']".format(var_id),
                target_namespaces=namespaces,
            )
            vars.append(var)

    return vars
