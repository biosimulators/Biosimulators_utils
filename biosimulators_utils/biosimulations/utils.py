""" Utility methods for working with BioSimulations and runBioSimulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-01-30
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""
from ..config import get_config, Config  # noqa: F401
import json
import os
import requests

__all__ = [
    'submit_project_to_runbiosimulations',
    'validate_biosimulations_api_response',
]


def submit_project_to_runbiosimulations(name, filename_or_url,
                                        simulator, simulator_version='latest',
                                        cpus=1, memory=8, max_time=20, env_vars=None,
                                        email=None, public=False,
                                        config=None):
    """ Submit a simulation project (COMBINE/OMEX archive) to runBioSimulations and, optionally, BioSimulations

    Args:
        name (:obj:`str`): name for the simulation run
        filename_or_url (:obj:`str`): path or URL to COMBINE/OMEX archive
        simulator (:obj:`str`): BioSimulators id for simulator
        simulator_version (:obj:`str`, optional): simulator version
        cpus (:obj:`int`, optional): CPUs
        memory (:obj:`float`, optional): maximum memory in GB
        max_time (:obj:`float`, optional): maximum execution time in minutes
        env_vars (:obj:`list` of :obj:`dict`, optional): environment variables to execute the COMBINE/OMEX archive. Each
            element should have two string-valued keys ``key`` and ``value``
        email (:obj:`str`, optional): email to receive a notification upon completion of the simulation run
        public (:obj:`bool`, optional): whether to publish the simulation run to BioSimulations
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`str`: runBioSimulations id
    """
    config = config or get_config()
    endpoint = config.RUNBIOSIMULATIONS_API_ENDPOINT + 'runs'
    run = {
        "name": name,
        "simulator": simulator,
        "simulatorVersion": simulator_version,
        "cpus": cpus,
        "memory": memory,
        "maxTime": max_time,
        "envVars": env_vars or [],
        "email": email,
        "public": public,
    }
    if os.path.isfile(filename_or_url):
        with open(filename_or_url, 'rb') as file:
            response = requests.post(
                endpoint,
                data={
                    'simulationRun': json.dumps(run),
                },
                files={
                    'file': ('project.omex', file, 'application/zip'),
                },
                headers={
                    "Accept": "application/json",
                }
            )
    else:
        run['url'] = filename_or_url
        response = requests.post(
            endpoint,
            json=run,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
    response.raise_for_status()
    return response.json()['id']


def validate_biosimulations_api_response(response, failure_introductory_message):
    """ Validate a response from one of BioSimulation's APIs.

    Args:
        response (:obj:`requests.models.Response`): API response
        failure_introductory_message (:obj:`str`): introductory message for failures

    Raises:
        :obj:`requests.RequestException`
    """
    try:
        response.raise_for_status()

    except requests.RequestException as exception:
        error_messages = []
        for error in response.json()['error']:
            pointer = error.get('source', {}).get('pointer', None)
            error_messages.append('{} ({}):{}{}'.format(
                error['title'], error['status'],
                ' `{}` is invalid'.format(pointer) if pointer else '',
                '\n\n  ' + error['detail'].replace('\n', '\n  ') if error.get('detail', None) else '',
            ))

        error_message = '{}\n\n  - {}'.format(
            failure_introductory_message,
            '\n\n  - '.join(msg.replace('\n', '\n    ') for msg in error_messages))

        exception.args = (error_message,)

        raise
