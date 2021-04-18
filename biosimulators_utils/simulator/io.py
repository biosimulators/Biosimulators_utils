""" Methods for reading specifications of simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..biosimulations.utils import validate_biosimulations_api_response
from ..config import get_config
from ..utils.core import patch_dict
import json
import os
import requests
import simplejson.errors


def read_simulator_specs(path_or_url, patch=None):
    """ Read the specifications of a simulator

    Args:
        path_or_url (:obj:`str`): file path or URL for the specifications of a simulator
        patch (:obj:`dict`, optional): values of properties to supersede those in :obj:`path_or_url`

    Returns:
        :obj:`dict`: specifications of a simulator

    Raises:
        :obj:`requests.RequestException`: if the specifications could not be retrieved
        :obj:`simplejson.errors.JSONDecodeError`: if the specifications are not propertly encoded into JSON
        :obj:`ValueError`: if the specifications are not consistent with the BioSimulators schema
    """
    if os.path.isfile(path_or_url):
        with open(path_or_url, 'r') as file:
            try:
                specs = json.load(file)
            except json.JSONDecodeError as error:
                raise ValueError(''.join([
                    'Simulator specifications from {} could not be parsed. '.format(path_or_url),
                    'Specifications must be encoded into JSON.\n\n  {}'.format(str(error).replace('\n', '\n  ')),
                ]))

    else:
        # download specifications
        response = requests.get(path_or_url)
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            raise requests.RequestException('Simulator specifications could not be retrieved from {}.\n\n  {}'.format(
                path_or_url, str(error).replace('\n', '\n  ')))

        # check that specifications is valid JSON
        try:
            specs = response.json()
        except simplejson.errors.JSONDecodeError as error:
            raise ValueError(''.join([
                'Simulator specifications from {} could not be parsed. '.format(path_or_url),
                'Specifications must be encoded into JSON.\n\n  {}'.format(str(error).replace('\n', '\n  ')),
            ]))

    # apply patch
    if patch:
        patch_dict(specs, patch)

    # validate specifications
    api_endpoint = get_config().BIOSIMULATORS_API_ENDPOINT
    response = requests.post('{}simulators/validate'.format(api_endpoint), json=specs)
    intro_failure_msg = ''.join([
        "The simulator specifications from `{}` are invalid. ".format(path_or_url),
        "The specifications of simulation tools must adhere to BioSimulators' schema. ",
        "BioSimulators' schema is available in both JSON Schema and Open API Specifications formats. ",
        "Documentation is available at {}.".format(api_endpoint)
    ])
    validate_biosimulations_api_response(response, intro_failure_msg)

    # return validated specifications
    return specs
