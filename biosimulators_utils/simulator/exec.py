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
from ..image import get_docker_image
import os
import shutil
import subprocess
import tempfile

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


def exec_sedml_docs_in_archive_with_containerized_simulator(
        archive_filename, out_dir, docker_image,
        docker_image_temp_dir='/tmp', docker_image_path_sep='/',
        environment=None, pull_docker_image=True,
        user_to_exec_within_container='_CURRENT_USER_', allocate_tty=True, remove_docker_container=True):
    """ Use a containerized simulator tool to execute the tasks specified in a
    COMBINE/OMEX archive and generate the reports specified in the archive

    Args:
        archive_filename (:obj:`str`): path to a COMBINE/OMEX archive
        out_dir (:obj:`str`): directory where outputs should be saved
        docker_image (:obj:`str`): tag (e.g., ``biosimulators/tellurium``) or
            URL (``ghcr.io/biosimulators/tellurium``) for a Docker image of a simulator
        docker_image_temp_dir (:obj:`str`, optional): Path to the temporary directory within the Docker image
            (e.g., ``/tmp`` for Linux images, ``C:\\Users\\{ user }\\AppData\\Local\\Temp`` for Windows images).
            The path can either be an absolute path or a path relative to the working directory of the image.
        docker_image_path_sep (:obj:`str`, optional): Path separator for the image (e.g., ``/`` for
            Linux, Mac OS, Unix images; ``\\`` for Windows images)
        environment (:obj:`dict`, optional): environment variables for executing the Docker image
        pull_docker_image (:obj:`bool`, optional): if :obj:`True`, pull the Docker image (if the image isn't
            available locally, this will cause the image to be downloaded; this will cause the image to be updated)
        user_to_exec_within_container (:obj:`str`, optional): username or user id to execute commands within the Docker container

            * Use ``_CURRENT_USER_`` to indicate that the Docker container should execute commands as the current user (``os.getuid()``)
            * Use the format ``<name|uid>[:<group|gid>]`` to indicate any other user/group that the Docker container should use to
              execute commands

        allocate_tty (:obj:`bool`, optional): if :obj:`True`, allocate a pseudo-TTY
        remove_docker_container (:obj:`bool`, optional): if :obj:`True`, automatically remove the container when it exits

    Raises:
        :obj:`RuntimeError`: if the execution failed
    """
    if not docker:
        raise ModuleNotFoundError("No module named 'docker'. Docker and the Python Docker package must be installed.")

    # get/pull image
    docker_client = docker.from_env()
    get_docker_image(docker_client, docker_image, pull=pull_docker_image)

    # run image
    in_dir = tempfile.mkdtemp()
    if os.path.isfile(archive_filename):
        shutil.copyfile(archive_filename, os.path.join(in_dir, os.path.basename(archive_filename)))

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    image_in_dir = docker_image_path_sep.join((docker_image_temp_dir, 'in'))
    image_out_dir = docker_image_path_sep.join((docker_image_temp_dir, 'out'))

    # setup Docker run arguments
    args = ['docker', 'run']

    args.extend(['--mount', 'type=bind,source={},target={},readonly'.format(in_dir, image_in_dir)])
    args.extend(['--mount', 'type=bind,source={},target={}'.format(os.path.abspath(out_dir), image_out_dir)])

    if environment:
        for key, val in environment.items():
            args.extend(['--env', '{}={}'.format(key, val)])

    if user_to_exec_within_container:
        if user_to_exec_within_container == '_CURRENT_USER_':
            if os.name == 'posix':
                args.extend(['--user', str(os.getuid())])
            else:
                raise NotImplementedError('The current user id can only be retrieved for POSIX OSes')
        elif user_to_exec_within_container == '_SUDO_':
            args.insert(0, 'sudo')
        else:
            args.extend(['--user', user_to_exec_within_container])

    if allocate_tty:
        args.append('--tty')

    if remove_docker_container:
        args.append('--rm')

    args.append(docker_image)
    args.extend(build_cli_args(
        docker_image_path_sep.join((image_in_dir, os.path.basename(archive_filename))),
        image_out_dir,
    ))

    # run image
    try:
        subprocess.check_call(args)

    except FileNotFoundError:
        raise RuntimeError("Docker could not be found")

    except subprocess.CalledProcessError as exception:
        raise RuntimeError("The image '{}' could not execute the archive:\n\n  {}".format(
            docker_image, (exception.stderr or 'Unknown error').replace('\n', '\n  ')))

    except Exception as exception:
        raise RuntimeError("The image '{}' could not execute the archive:\n\n  {}".format(
            docker_image, str(exception).replace('\n', '\n  ')))

    finally:
        shutil.rmtree(in_dir)


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
