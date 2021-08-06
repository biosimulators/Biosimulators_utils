""" Utilities for reading the specifications of a simulator

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import (SedDocument, Task, ModelLanguagePattern, ModelLanguageEdamId,  # noqa: F401
                                SteadyStateSimulation, UniformTimeCourseSimulation, Algorithm, AlgorithmParameterChange)
from .data_model import SoftwareInterface
from kisao import Kisao
from kisao.data_model import AlgorithmSubstitutionPolicy
from kisao.utils import get_substitutable_algorithms_for_policy
import json
import natsort
import re
import requests

__all__ = [
    'BIOSIMULATORS_API_ENDPOINT',
    'get_simulator_specs',
    'does_simulator_have_capabilities_to_execute_sed_document',
    'does_simulator_have_capabilities_to_execute_sed_task',
    'does_algorithm_implementation_have_capabilities_to_execute_sed_task',
    'does_algorithm_implementation_have_capabilities_to_execute_sed_model_language',
    'does_algorithm_implementation_have_capabilities_to_execute_parameter',
    'gen_algorithms_from_specs',
]


BIOSIMULATORS_API_ENDPOINT = 'https://api.biosimulators.org/simulators'


def get_simulator_specs(id, version='latest'):
    """ Get the specifications of a simulation tool from the BioSimulators registry

    Args:
        id (:obj:`str`): id
        version (:obj:`str`, optional): version

    Returns:
        :obj:`dict` with schema ``https://api.biosimulators.org/openapi.json#/components/schemas/Simulator``: specifications
    """
    if version == 'latest':
        url = BIOSIMULATORS_API_ENDPOINT + '/' + id
        response = requests.get(url)
        response.raise_for_status()
        version_specs = natsort.natsorted(response.json(), key=lambda version_spec: version_spec['version'])
        return version_specs[-1]
    else:
        url = BIOSIMULATORS_API_ENDPOINT + '/' + id + '/' + version
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


def does_simulator_have_capabilities_to_execute_sed_document(sed_doc, simulator_specs,
                                                             alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_VARIABLES):
    """ Determine if a simulator has the capabilities to execute a SED document

    Args:
        sed_doc (:obj:`SedDocument`): SED document
        simulator_specs (:obj:`dict` with schema ``https://api.biosimulators.org/openapi.json#/components/schemas/Simulator``):
            specifications of a simulation tool
        alg_substitution_policy (:obj:`AlgorithmSubstitutionPolicy`, optional): algorithm substitution policy

    Returns:
        :obj:`bool`: whether the simulator has the capabilities to execute the SED document
    """
    for task in sed_doc.tasks:
        if not does_simulator_have_capabilities_to_execute_sed_task(task, simulator_specs, alg_substitution_policy=alg_substitution_policy):
            return False
    return True


def does_simulator_have_capabilities_to_execute_sed_task(task, simulator_specs,
                                                         alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_VARIABLES):
    """ Determine if a simulator has the capabilities to execute a SED task

    Args:
        task (:obj:`Task`): SED task
        simulator_specs (:obj:`dict` with schema ``https://api.biosimulators.org/openapi.json#/components/schemas/Simulator``):
            specifications of a simulation tool
        alg_substitution_policy (:obj:`AlgorithmSubstitutionPolicy`, optional): algorithm substitution policy

    Returns:
        :obj:`bool`: whether the simulator has the capabilities to execute the SED task
    """
    if isinstance(task, Task):
        if not isinstance(task.simulation, (SteadyStateSimulation, UniformTimeCourseSimulation)):
            return False

        for alg_specs in simulator_specs['algorithms']:
            if does_algorithm_implementation_have_capabilities_to_execute_sed_task(task, alg_specs,
                                                                                   alg_substitution_policy=alg_substitution_policy):
                return True

        return False

    else:
        for sub_task in task.sub_tasks:
            if not does_simulator_have_capabilities_to_execute_sed_task(sub_task.task, simulator_specs,
                                                                        alg_substitution_policy=alg_substitution_policy):
                return False
        return True


def does_algorithm_implementation_have_capabilities_to_execute_sed_task(task, algorithm_specs,
                                                                        alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_VARIABLES):
    """ Determine if an implementation of an algorithm has the capabilities to execute a SED task

    Args:
        task (:obj:`Task`): SED task
        algorithm_specs (:obj:`dict` with schema ``https://api.biosimulators.org/openapi.json#/components/schemas/Algorithm``):
            specifications of the implementation of an algorithm
        alg_substitution_policy (:obj:`AlgorithmSubstitutionPolicy`, optional): algorithm substitution policy

    Returns:
        :obj:`bool`: whether the implementation of the algorithm has the capabilities to execute the SED task
    """
    model = task.model
    simulation = task.simulation
    algorithm = simulation.algorithm

    kisao = Kisao()
    alg_term = kisao.get_term(algorithm.kisao_id)
    alt_algs = get_substitutable_algorithms_for_policy(alg_term, substitution_policy=alg_substitution_policy)
    alt_alg_ids = kisao.get_term_ids(alt_algs)

    if algorithm_specs['kisaoId']['id'] in alt_alg_ids:
        # check if the implementation supports the model language
        if not does_algorithm_implementation_have_capabilities_to_execute_sed_model_language(model.language, algorithm_specs):
            return False

        # check if implementation supports the parameters of the algorithm
        supports_parameters = True
        if algorithm_specs['kisaoId']['id'] == algorithm.kisao_id:
            for change in algorithm.changes:
                if not does_algorithm_implementation_have_capabilities_to_execute_parameter(change.kisao_id, algorithm_specs):
                    supports_parameters = False
                    break

        if not supports_parameters:
            return False

        return True

    return False


def does_algorithm_implementation_have_capabilities_to_execute_sed_model_language(model_language, algorithm_specs):
    """ Determine if an implementation of an algorithm has the capabilities to execute a model langugae

    Args:
        model_language (:obj:`str`): SED URN for model language
        algorithm_specs (:obj:`dict` with schema ``https://api.biosimulators.org/openapi.json#/components/schemas/Algorithm``):
            specifications of the implementation of an algorithm

    Returns:
        :obj:`bool`: whether the implementation of the algorithm has the capabilities to execute the SED model language
    """
    model_language_edam_id = None
    for model_language_pattern in ModelLanguagePattern.__members__.values():
        if model_language and re.match(model_language_pattern.value, model_language):
            model_language_edam_id = ModelLanguageEdamId[model_language_pattern.name].value
            break
    if not model_language_edam_id:
        return False

    for model_format_specs in algorithm_specs['modelFormats']:
        if model_format_specs['id'] == model_language_edam_id:
            return True
    return False


def does_algorithm_implementation_have_capabilities_to_execute_parameter(parameter_kisao_id, algorithm_specs):
    """ Determine if an implementation of an algorithm has the capabilities to execute a model langugae

    Args:
        parameter_kisao_id (:obj:`str`): KiSAO id for an algorithm parameter
        algorithm_specs (:obj:`dict` with schema ``https://api.biosimulators.org/openapi.json#/components/schemas/Algorithm``):
            specifications of the implementation of an algorithm

    Returns:
        :obj:`bool`: whether the implementation of the algorithm has the capabilities to execute the SED parameter
    """
    for parameter_specs in algorithm_specs['parameters']:
        if parameter_specs['kisaoId']['id'] == parameter_kisao_id:
            return True
    return False


def gen_algorithms_from_specs(specifications):
    """ Generate a list of algorithms and their parameters from the specifications of a simulator

    Args:
        specifications (:obj:`dict` or :obj:`str`): specifications or path to specifications

    Returns:
        :obj:`dict` of :obj:`str` to :obj:`Algorithm`: dictionary that maps KiSAO ids to algorithms and their parameters
    """
    if isinstance(specifications, str):
        with open(specifications, 'rb') as file:
            specifications = json.load(file)

    algs = {}
    for alg_spec in specifications.get('algorithms', []):
        if SoftwareInterface.biosimulators_docker_image.value in alg_spec['availableSoftwareInterfaceTypes']:

            alg = Algorithm()
            alg.kisao_id = alg_spec.get('kisaoId', {}).get('id', None)
            algs[alg.kisao_id] = alg

            param_specs = alg_spec.get('parameters', None)
            if param_specs:
                for param_spec in param_specs:
                    if SoftwareInterface.biosimulators_docker_image.value in param_spec['availableSoftwareInterfaceTypes']:
                        alg.changes.append(AlgorithmParameterChange(
                            kisao_id=param_spec.get('kisaoId', {}).get('id', None),
                            new_value=param_spec.get('value', None),
                        ))

    return algs
