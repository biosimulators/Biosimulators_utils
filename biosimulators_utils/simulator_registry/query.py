""" Methods for querying the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..biosimulations.utils import validate_biosimulations_api_response
from ..config import get_config
import requests


__all__ = ['get_simulator_version_specs']


def get_simulator_version_specs(id):
    """ Get the specifications of the versions of a simulator in the BioSimulators registry

    Args:
        id (:obj:`str`): simulator id

    Returns:
        :obj:`list` of :obj:`dict`: specifications of the registered versions of the simulator
    """

    endpoint = get_config().BIOSIMULATORS_API_ENDPOINT
    response = requests.get('{}simulators/{}'.format(endpoint, id))

    try:
        intro_failure_msg = "The specifications of the versions of `{}` could not be retrieved from the BioSimulators registry.".format(id)
        validate_biosimulations_api_response(response, intro_failure_msg)
        version_specs = response.json()
    except requests.exceptions.HTTPError:
        if response.status_code != 404:
            raise
        version_specs = []
    return version_specs
