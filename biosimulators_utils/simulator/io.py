""" Methods for reading specifications of simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
import requests
import simplejson.errors


def read_simulator_specs(url):
    """ Read the specifications of a simulator

    Args:
        url (:obj:`str`): URL for the specifications of a simulator

    Returns:
        :obj:`dict`: specifications of a simulator

    Raises:
        :obj:`requests.RequestException`: if the specifications could not be retrieved
        :obj:`simplejson.errors.JSONDecodeError`: if the specifications are not propertly encoded into JSON
        :obj:`ValueError`: if the specifications are not consistent with the BioSimulators schema
    """
    response = requests.get(url)

    # download specifications
    try:
        response.raise_for_status()
    except requests.RequestException as error:
        raise requests.RequestException('Simulator specifications could not be retrieved from {}.\n\n  {}'.format(
            url, str(error).replace('\n', '\n  ')))

    # check that specifications is valid JSON
    try:
        specs = response.json()
    except simplejson.errors.JSONDecodeError as error:
        raise ValueError(''.join([
            'Simulator specifications from {} could not be parsed.'.format(url),
            'Specifications must be encoded into JSON.\n\n  {}'.format(str(error).replace('\n', '\n  ')),
        ]))

    # validate specifications
    api_endpoint = get_config().BIOSIMULATORS_API_ENDPOINT
    response = requests.post('{}simulators/validate'.format(api_endpoint), json=specs)
    try:
        response.raise_for_status()
    except requests.RequestException as error:
        raise ValueError(''.join([
            'Simulator specifications from {} are not valid.'.format(url),
            'Specifications must be adhere to the BioSimulators schema. Documentation is available at {}.\n\n  {}'.format(
                api_endpoint, str(error).replace('\n', '\n  ')),
        ]))

    # return validated specifications
    return specs
