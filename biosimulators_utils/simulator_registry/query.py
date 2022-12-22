""" Methods for querying the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..biosimulations.utils import validate_biosimulations_api_response
from ..config import get_config, Config  # noqa: F401
from ..globals import JSONType
import requests


__all__ = ['get_simulator_version_specs']


def get_simulator_version_specs(id: str, config: Config = None):
    """ Get the specifications of the versions of a simulator in the BioSimulators registry

    Args:
        id (:obj:`str`): simulator id
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`list` of :obj:`dict`: specifications of the registered versions of the simulator
    """

    if config is None:
        config = get_config()

    endpoint: str = config.BIOSIMULATORS_API_ENDPOINT
    response: requests.Response = requests.get('{}simulators/{}'.format(endpoint, id))

    try:
        intro_failure_msg: str = "The specifications of the versions of `{}` could not be retrieved from the BioSimulators registry.".format(id)
        validate_biosimulations_api_response(response, intro_failure_msg, ValueError)
        version_specs: JSONType = response.json()
    except ValueError:
        if response.status_code != 404:
            raise
        version_specs = []
    return version_specs
