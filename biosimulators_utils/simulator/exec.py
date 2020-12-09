""" Utilities for executing command-line interfaces to simulators and
containers that contain command-line interfaces to simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

try:
    import docker
except ModuleNotFoundError:
    docker = None
import os
import subprocess

__all__ = [
    'exec_sedml_docs_in_archive_with_simulator_cli',
    'exec_sedml_docs_in_archive_with_containerized_simulator',
]


def exec_sedml_docs_in_archive_with_simulator_cli(archive_filename, out_dir, simulator_command):
    """ Use a command-line interface to a simulation tool to execute the tasks specified in archive
    COMBINE/OMEX archive and generate the reports specified in the archive

    Args:
        archive_filename (:obj:`str`): path to a COMBINE/OMEX archive
        out_dir (:obj:`str`): directory where outputs should be saved
        simulator_command (:obj:`str`): system command for the simulator to execute

    Raises:
        :obj:`RuntimeError`: if the execution failed
    """
    try:
        subprocess.check_call([simulator_command] + build_cli_args(archive_filename, out_dir))

    except FileNotFoundError:
        raise RuntimeError("The command '{}' could not be found".format(simulator_command))

    except subprocess.CalledProcessError as exception:
        raise RuntimeError("The command '{}' could not execute the archive:\n\n  {}".format(
            simulator_command, exception.stderr.replace('\n', '\n  ')))

    except Exception as exception:
        raise RuntimeError("The command '{}' could not execute the archive:\n\n  {}".format(
            simulator_command, str(exception).replace('\n', '\n  ')))


def exec_sedml_docs_in_archive_with_containerized_simulator(archive_filename, out_dir, docker_image,
                                                            docker_image_temp_dir='/tmp', docker_image_path_sep='/',
                                                            environment=None, pull_docker_image=True):
    """ Use a containerized simulator tool to execute the tasks specified in a
    COMBINE/OMEX archive and generate the reports specified in the archive

    Args:
        archive_filename (:obj:`str`): path to a COMBINE/OMEX archive
        out_dir (:obj:`str`): directory where outputs should be saved
        docker_image (:obj:`str`): tag (e.g., ``biosimulators/tellurium``) or
            URL (``ghcr.io/biosimulators/tellurium`) for a Docker image of a simulator
        docker_image_temp_dir (:obj:`str`, optional): Path to the temporary directory within the Docker image
            (e.g., ``/tmp`` for Linux images, ``C:\\Users\\{ user }\\AppData\\Local\\Temp`` for Windows images).
            The path can either be an absolute path or a path relative to the working directory of the image.
        docker_image_path_sep (:obj:`str`, optional): Path separator for the image (e.g., ``/`` for
            Linux, Mac OS, Unix images; ``\\`` for Windows images)
        environment (:obj:`dict`, optional): environment variables for executing the Docker image
        pull_docker_image (:obj:`bool`, optional): if :obj:`True`, pull the Docker image (if the image isn't
            available locally, this will cause the image to be downloaded; this will cause the image to be updated)

    Raises:
        :obj:`RuntimeError`: if the execution failed
    """
    if not docker:
        raise ModuleNotFoundError("No module named 'docker'")

    # pull image
    get_simulator_docker_image(docker_image, pull=pull_docker_image)

    # run image
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    image_in_dir = docker_image_path_sep.join((docker_image_temp_dir, 'in'))
    image_out_dir = docker_image_path_sep.join((docker_image_temp_dir, 'out'))
    try:
        subprocess.check_call(
            [
                'docker',
                'run',
                '-t',
                '--rm',
                '--mount', 'type=bind,source={},target={},readonly'.format(
                    os.path.abspath(os.path.dirname(archive_filename)), image_in_dir),
                '--mount', 'type=bind,source={},target={}'.format(
                    os.path.abspath(out_dir), image_out_dir),
                '--user', str(os.getuid()),
                docker_image,
            ] +
            build_cli_args(
                docker_image_path_sep.join((image_in_dir, os.path.basename(archive_filename))),
                image_out_dir,
            ),
        )

    except FileNotFoundError:
        raise RuntimeError("Docker could not be found")

    except subprocess.CalledProcessError as exception:
        raise RuntimeError("The image '{}' could not execute the archive:\n\n  {}".format(
            docker_image, (exception.stderr or 'Unknown error').replace('\n', '\n  ')))

    except Exception as exception:
        raise RuntimeError("The image '{}' could not execute the archive:\n\n  {}".format(
            docker_image, str(exception).replace('\n', '\n  ')))


def build_cli_args(archive_filename, out_dir):
    """ Build the arguments to use a command-line interface to a simulator to execute a COMBINE/OMEX archive

    Args:
        archive_filename (:obj:`str`): path to a COMBINE/OMEX archive
        out_dir (:obj:`str`): directory where outputs should be saved

    Returns:
        :obj:`list` of :obj:`str`: command-line arguments to execute a COMBINE/OMEX archive
    """
    return [
        '-i', archive_filename,
        '-o', out_dir,
    ]


def get_simulator_docker_image(tag, pull=True):
    """ Get a Docker image for a simulator

    Args:
        tag (:obj:`str`): tag (e.g., ``biosimulators/tellurium``) or
            URL (``ghcr.io/biosimulators/tellurium`) for a Docker image of a simulator
    Returns:
        :obj:`docker.models.images.Image`: Docker image
    """
    docker_client = docker.from_env()

    try:
        image = docker_client.images.get(tag)
        if pull:
            try:
                image = docker_client.images.pull(tag)
            except:  # pragma: no cover
                pass

    except:
        if pull:
            try:
                image = docker_client.images.pull(tag)
            except:
                raise docker.errors.ImageNotFound("Image '{}' for simulator could not be pulled".format(tag))
        else:
            raise docker.errors.ImageNotFound("Image '{}' for simulator is not available locally".format(tag))

    return image
