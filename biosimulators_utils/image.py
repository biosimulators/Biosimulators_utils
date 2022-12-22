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
from docker.models.images import Image

__all__ = [
    'login_to_docker_registry',
    'get_docker_image',
    'pull_docker_image',
    'tag_and_push_docker_image',
    'convert_docker_image_to_singularity',
]


def login_to_docker_registry(registry: str, username: str, password: str):
    """ Login to a Docker registry

    Args:
        registry (:obj:`str`): registry (e.g., ghcr.io)
        username (:obj:`str`): user name
        password (:obj:`str`): password

    Returns:
        :obj:`docker.client.DockerClient`: Docker client
    """
    docker_client: docker.client.DockerClient = docker.from_env()
    docker_client.login(registry=registry, username=username, password=password)
    return docker_client


def get_docker_image(docker_client: docker.client.DockerClient, tag: str, pull: bool = True) -> Image:
    """ Get a Docker image for a simulator

    Args:
        docker_client (:obj:`docker.client.DockerClient`): Docker client
        tag (:obj:`str`): tag (e.g., ``biosimulators/tellurium``) or
            URL (``ghcr.io/biosimulators/tellurium``) for a Docker image of a simulator

    Returns:
        :obj:`docker.models.images.Image`: Docker image
    """
    image: Image
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
        msg = 'Image {} could not be pulled.\n\n  {}'.format(
            url, str(error).replace('\n', '\n  '))
        raise Exception(msg)


def tag_and_push_docker_image(docker_client, image, tag):
    """ Tag and push Docker image

    Args:
        docker_client (:obj:`docker.client.DockerClient`): Docker client
        image (:obj:`docker.models.images.Image`): Docker image
        tag (:obj:`str`): tag
    """
    assert image.tag(tag)
    response = docker_client.images.push(tag)
    print(response)
    response = json.loads(response.rstrip().split('\n')[-1])
    if 'error' in response:
        raise Exception('Unable to push image to {}\n  {}'.format(
            tag, response.get('errorDetail', {}).get('message', response['error'])))


def convert_docker_image_to_singularity(docker_image_url: str, singularity_filename: str = None):
    """ Convert a locally cached Docker image to a Singularity image.

    Remotely published Docker images (e.g., images published to Docker Hub, GitHub Container Registry, etc.)
    should first be pulled (e.g., using :obj:`pull_docker_image` or ``docker pull {image}``).

    Args:
        docker_image_url (:obj:`str`)
        singularity_filename (:obj:`str`, optional): file name for saving Singularity image

    Returns:
        :obj:`str`: path where Singularity image was saved
    """
    cmd: list[str] = ['singularity', 'build']

    if ':' not in docker_image_url:
        docker_image_url += ':latest'

    if not singularity_filename:
        singularity_filename: str = os.path.join(
            os.path.expanduser('~'), '.biosimulators-utils', 'singularity',
            docker_image_url.replace('/', '_').replace(':', '_') + '.sif')

    if not os.path.isdir(os.path.dirname(singularity_filename)):
        os.makedirs(os.path.dirname(singularity_filename))

    cmd.append(singularity_filename)

    cmd.append('docker-daemon://' + docker_image_url)

    if not os.path.isfile(singularity_filename):
        subprocess.check_call(cmd)

    return singularity_filename
