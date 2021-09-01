from biosimulators_utils import image
from unittest import mock
import docker
import os
import shutil
import tempfile
import unittest


class ImageTestCase(unittest.TestCase):
    def test_login_to_docker_registry(self):
        image.login_to_docker_registry(
            'docker.io',
            os.getenv("DOCKER_HUB_USERNAME"),
            os.getenv("DOCKER_HUB_TOKEN"))

    def test_get_simulator_docker_image(self):
        docker_client = docker.from_env()
        docker_client.images.pull('hello-world')
        image.get_docker_image(docker_client, 'hello-world', pull=False)
        image.get_docker_image(docker_client, 'hello-world', pull=True)

        with self.assertRaises(docker.errors.ImageNotFound):
            image.get_docker_image(docker_client, 'unknown', pull=False)

        with self.assertRaises(docker.errors.ImageNotFound):
            image.get_docker_image(docker_client, 'unknown', pull=True)

    def test_pull_docker_image(self):
        docker_client = image.login_to_docker_registry(
            'docker.io',
            os.getenv("DOCKER_HUB_USERNAME"),
            os.getenv("DOCKER_HUB_TOKEN"))
        image.pull_docker_image(docker_client, 'hello-world')

        with self.assertRaises(docker.errors.NotFound):
            image.pull_docker_image(docker_client, 'hello-undefined')

        with self.assertRaises(Exception):
            image.pull_docker_image(docker_client, '---undefined---')

    def test_tag_and_push_docker_image(self):
        docker_client = image.login_to_docker_registry(
            'docker.io',
            os.getenv("DOCKER_HUB_USERNAME"),
            os.getenv("DOCKER_HUB_TOKEN"))
        img = image.pull_docker_image(docker_client, 'hello-world')

        response = '{"error": "x"}'
        docker_client = mock.Mock(images=mock.Mock(push=lambda tag: response))
        with mock.patch('docker.from_env', return_value=docker_client):
            with self.assertRaisesRegex(Exception, 'Unable to push image to'):
                image.tag_and_push_docker_image(docker_client, img, 'hello-world-2')

    def test_convert_docker_image_to_singularity(self):
        docker_client = image.login_to_docker_registry(
            'docker.io',
            os.getenv("DOCKER_HUB_USERNAME"),
            os.getenv("DOCKER_HUB_TOKEN"))
        image.pull_docker_image(docker_client, 'hello-world')

        filename = image.convert_docker_image_to_singularity('hello-world')
        os.remove(filename)

        tmpdir = tempfile.mkdtemp()
        singularity_filename = os.path.join(tmpdir, 'subdir-1', 'subdir-2', 'test.sif')
        image.convert_docker_image_to_singularity('hello-world', singularity_filename=singularity_filename)
        shutil.rmtree(tmpdir)
