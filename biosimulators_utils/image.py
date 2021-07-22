""" Utilities for working with Docker images

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import docker
import json
import os
import subprocess

__all__ = [
    'login_to_docker_registry',
    'get_docker_image',
    'pull_docker_image',
    'tag_and_push_docker_image',
    'convert_docker_image_to_singularity',
]


def login_to_docker_registry(registry, username, password):
    """ Login to a Docker registry

    Args:
        registry (:obj:`str`): registry (e.g., ghcr.io)
        username (:obj:`str`): user name
        password (:obj:`str`): password

    Returns:
        :obj:`docker.client.DockerClient`: Docker client
    """
    docker_client = docker.from_env()
    docker_client.login(registry=registry, username=username, password=password)
    return docker_client


def get_docker_image(docker_client, tag, pull=True):
    """ Get a Docker image for a simulator

    Args:
        docker_client (:obj:`docker.client.DockerClient`): Docker client
        tag (:obj:`str`): tag (e.g., ``biosimulators/tellurium``) or
            URL (``ghcr.io/biosimulators/tellurium``) for a Docker image of a simulator

    Returns:
        :obj:`docker.models.images.Image`: Docker image
    """
    try:
        image = docker_client.images.get(tag)
        if pull:
            try:
                image = docker_client.images.pull(tag)
            except Exception:  # pragma: no cover
                pass

    except Exception:
        if pull:
            try:
                image = docker_client.images.pull(tag)
            except Exception:
                raise docker.errors.ImageNotFound("Image '{}' for simulator could not be pulled".format(tag))
        else:
            raise docker.errors.ImageNotFound("Image '{}' for simulator is not available locally".format(tag))

    return image


def pull_docker_image(docker_client, url):
    """ Pull Docker image

    Args:
        docker_client (:obj:`docker.client.DockerClient`): Docker client
        url (:obj:`str`): URL for Docker image

    Returns:
        :obj:`docker.models.images.Image`: Docker image
    """
    try:
        return docker_client.images.pull(url)
    except docker.errors.NotFound:
        raise docker.errors.NotFound('{} is not a tag or URL for a Docker image.'.format(url))
    except Exception as error:
        raise Exception('Image {} could not be pulled.\n\n  {}'.format(
            url, str(error).replace('\n', '\n  ')))


def tag_and_push_docker_image(docker_client, image, tag):
    """ Tag and push Docker image

    Args:
        docker_client (:obj:`docker.client.DockerClient`): Docker client
        image (:obj:`docker.models.images.Image`): Docker image
        tag (:obj:`str`): tag
    """
    assert image.tag(tag)
    response = docker_client.images.push(tag)
    response = json.loads(response.rstrip().split('\n')[-1])
    if 'error' in response:
        raise Exception('Unable to push image to {}\n  {}'.format(
            tag, response.get('errorDetail', {}).get('message', response['error'])))


def convert_docker_image_to_singularity(docker_image, singularity_filename=None):
    """ Convert a Docker image to a Singularity image

    Args:
        docker_image (:obj:`str`)
        singularity_filename (:obj:`str`, optional): file name for saving Singularity image

    Returns:
        :obj:`str`: path where Singularity image was saved
    """
    cmd = ['singularity', 'pull']

    if not singularity_filename:
        singularity_filename = os.path.join(
            os.path.expanduser('~'), '.biosimulators-utils', 'singularity',
            docker_image.replace('/', '_').replace(':', '_') + '.sif')

    if not os.path.isdir(os.path.dirname(singularity_filename)):
        os.makedirs(os.path.dirname(singularity_filename))

    cmd.append(singularity_filename)

    cmd.append('docker://' + docker_image)

    if not os.path.isfile(singularity_filename):
        subprocess.check_call(cmd)

    return singularity_filename
