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
    """ Execute the tasks specified in a archive and generate the reports specified in the archive

    Args:
        archive_filename (:obj:`str`): path to a COMBINE/OMEX archive
        out_dir (:obj:`str`): directory where outputs should be saved
        simulator_command (:obj:`str`): system command for the simulator to execute

    Raises:
        :obj:`RuntimeError`: if the execution failed
    """
    try:
        subprocess.check_call([simulator_command, '-i', archive_filename, '-o', out_dir])
    except FileNotFoundError:
        raise RuntimeError("The command '{}' could not be found".format(simulator_command))
    except subprocess.CalledProcessError as exception:
        raise RuntimeError("The command '{}' could not execute the archive:\n\n  {}".format(
            simulator_command, exception.stderr.replace('\n', '\n  ')))
    except Exception as exception:
        raise RuntimeError("The command '{}' could not execute the archive:\n\n  {}".format(
            simulator_command, str(exception).replace('\n', '\n  ')))


def exec_sedml_docs_in_archive_with_containerized_simulator(archive_filename, out_dir, docker_image_url):
    """ Execute the tasks specified in a archive and generate the reports specified in the archive

    Args:
        archive_filename (:obj:`str`): path to a COMBINE/OMEX archive
        out_dir (:obj:`str`): directory where outputs should be saved
        docker_image_url (:obj:`str`): URL for Docker image of simulator

    Raises:
        :obj:`RuntimeError`: if the execution failed
    """
    if not docker:
        raise ModuleNotFoundError("No module named 'docker'")
    docker_client = docker.from_env()

    docker_client.images.pull(docker_image_url)

    container = docker_client.containers.run(
        docker_image_url,
        volumes={
            os.path.dirname(archive_filename): {
                'bind': '/root/in',
                'mode': 'ro',
            },
            out_dir: {
                'bind': '/root/out',
                'mode': 'rw',
            }
        },
        command=['-i', '/root/in/' + os.path.basename(archive_filename), '-o', '/root/out'],
        tty=True,
        detach=True)
    status = container.wait()
    if status['StatusCode'] != 0:
        raise RuntimeError(container.logs().decode().replace('\\r\\n', '\n').strip())
    container.stop()
    container.remove()
