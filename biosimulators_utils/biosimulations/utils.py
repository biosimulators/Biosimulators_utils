""" Utility methods for working with BioSimulations and runBioSimulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-01-30
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""
from ..config import get_config, Config  # noqa: F401
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import os
import requests
import simplejson.errors

__all__ = [
    'run_simulation_project',
    'publish_simulation_project',
    'get_published_project',
    'get_authorization_for_client',
    'get_api_session',
    'validate_biosimulations_api_response',
    'get_formats',
    'get_file_extension_combine_uri_map',
    'get_ontology_terms',
]


def run_simulation_project(name, filename_or_url,
                           simulator, simulator_version='latest',
                           cpus=1, memory=8, max_time=20, env_vars=None,
                           purpose='other',
                           email=None,
                           project_id=None,
                           auth=None,
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
        purpose (:obj:`str`, optional): purpose (``academic`` or ``other``)
        email (:obj:`str`, optional): email to receive a notification upon completion of the simulation run
        project_id (:obj:`str`, optional): id to publish the run as to BioSimulations
        auth (obj:`str`, optional): authorization for the BioSimulations; needed to claim edit the published project in
            the future
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`str`: runBioSimulations id
    """
    config = config or get_config()
    session = get_api_session(config=config)
    endpoint = config.BIOSIMULATIONS_API_ENDPOINT + 'runs'
    run = {
        "name": name,
        "simulator": simulator,
        "simulatorVersion": simulator_version,
        "cpus": cpus,
        "memory": memory,
        "maxTime": max_time,
        "envVars": env_vars or [],
        "purpose": purpose,
        "email": email,
    }
    if project_id:
        run["projectId"] = project_id

    if os.path.isfile(filename_or_url):
        with open(filename_or_url, 'rb') as file:
            headers = {
                "Accept": "application/json",
            }
            if auth:
                headers['Authorization'] = auth
            response = session.post(
                endpoint,
                data={
                    'simulationRun': json.dumps(run),
                },
                files={
                    'file': ('project.omex', file, 'application/zip'),
                },
                headers=headers,
            )
    else:
        run['url'] = filename_or_url
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if auth:
            headers['Authorization'] = auth
        response = session.post(
            endpoint,
            json=run,
            headers=headers,
        )

    validate_biosimulations_api_response(response, 'Run could not be submitted.', RuntimeError)

    return response.json()['id']


def publish_simulation_project(run_id, project_id, overwrite=True, auth=None, config=None):
    """ Publish a project to BioSimulations

    Args:
        run_id (:obj:`str`): id of the simulation run to publish
        project_id (:obj:`str`): desired id for the published project
        auth (obj:`str`, optional): authorization for the BioSimulations; needed to claim edit the published project in
            the future
        config (:obj:`Config`, optional): configuration
    """
    config = config or get_config()
    endpoint = config.BIOSIMULATIONS_API_ENDPOINT + 'projects/{}'.format(project_id)
    session = get_api_session(config=config)

    headers = {}
    if auth:
        headers['Authorization'] = auth

    method = session.post
    if overwrite:
        project = get_published_project(project_id)
        if project:
            method = session.put

    response = method(
        endpoint,
        json={
            'id': project_id,
            'simulationRun': run_id,
        },
        headers=headers,
    )
    validate_biosimulations_api_response(response,
                                         'Project `{}` for run `{}` could not be published.'.format(project_id, run_id),
                                         ValueError)


def get_published_project(project_id, config=None):
    """ Publish a project to BioSimulations

    Args:
        project_id (:obj:`str`): desired id for the published project
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`dict`: in schema ``Project`` or :obj:`None` if the project doesn't exist
    """
    config = config or get_config()
    endpoint = config.BIOSIMULATIONS_API_ENDPOINT + 'projects/{}'.format(project_id)
    session = get_api_session(config=config)
    response = session.get(endpoint)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_authorization_for_client(id, secret, config=None):
    """ Get the authorization for a client of the BioSimulations API

    Args:
        id (:obj:`str`): id of the API client
        secret (:obj:`str`): secret for API client
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`str`: authorization for the client
    """
    config = config or get_config()

    response = requests.post(config.BIOSIMULATIONS_API_AUTH_ENDPOINT,
                             json={
                                 'client_id': id,
                                 'client_secret': secret,
                                 'audience': config.BIOSIMULATIONS_API_AUDIENCE,
                                 "grant_type": "client_credentials",
                             })
    response.raise_for_status()
    response_data = response.json()
    return response_data['token_type'] + ' ' + response_data['access_token']


def get_api_session(num_retries=10, backoff_factor=0.25, config=None):
    """ Get a session for the BioSimulations API with retrying

    Args:
        num_retries (:obj:`int`): number of times to retry each query
        backoff_factor (:obj:`float`): initial delay between retries
        config (:obj:`Config`, optional): configuration

    returns:
        :obj:`requests.Session`: session
    """
    config = config or get_config()

    retry_strategy = Retry(
        total=num_retries,
        backoff_factor=backoff_factor,
        allowed_methods=['GET', 'PUT', 'POST'],
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount(config.BIOSIMULATIONS_API_ENDPOINT, adapter)
    return session


def validate_biosimulations_api_response(response, failure_introductory_message, exception_type=None):
    """ Validate a response from one of BioSimulation's APIs.

    Args:
        response (:obj:`requests.models.Response`): API response
        failure_introductory_message (:obj:`str`): introductory message for failures
        exception_type (:obj:`type`, optional): type of exception to throw

    Raises:
        :obj:`requests.RequestException`
    """
    try:
        response.raise_for_status()

    except requests.RequestException as exception:
        try:
            errors = response.json()['error']
        except (simplejson.errors.JSONDecodeError, KeyError):
            raise exception

        error_messages = []
        for error in errors:
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

        if exception_type:
            raise exception_type(error_message)
        else:
            raise


def get_formats(config=None):
    """ Get information about the file formats used by BioSimulations

    Args:
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`list` of :obj:`dict`: information about the file formats used by BioSimulations
    """
    return get_ontology_terms('EDAM', config=config)


def get_file_extension_combine_uri_map(config=None):
    """ Get a map from file extensions to URIs for use with manifests of COMBINE/OMEX archives

    Args:
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`dict`: which maps extensions to lists of associated URIs
    """
    formats = get_formats(config=config)
    map = {}
    for format in formats:
        for extension in format['fileExtensions']:
            if extension not in map:
                map[extension] = set()
            for uri in format.get('biosimulationsMetadata', {}).get('omexManifestUris', []):
                map[extension].add(uri)
            for media_type in format['mediaTypes']:
                map[extension].add('http://purl.org/NET/mediatypes/' + media_type)

    return map


def get_ontology_terms(ontology, config=None):
    """ Get the terms of an ontology used by BioSimulations

    Args:
        ontology (:obj:`str`): ontology such as ``EDAM``, ``KISAO``, ``Linguist``, ``SBO``, ``SIO``, or ``SPDX``
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`list` of :obj:`dict`: ontology terms
    """
    config = config or get_config()
    response = requests.get(config.BIOSIMULATIONS_API_ENDPOINT + 'ontologies/' + ontology)
    response.raise_for_status()
    return response.json()
