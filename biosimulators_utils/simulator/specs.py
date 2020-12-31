""" Utilities for reading the specifications of a simulator

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import Algorithm, AlgorithmParameterChange
from .data_model import SoftwareInterface
import json


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
