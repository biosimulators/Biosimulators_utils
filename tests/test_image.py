from biosimulators_utils import image
from unittest import mock
import docker
import os
import shutil
import tempfile
import unittest


class ImageTestCase(unittest.TestCase):
    def test_login_to_docker_registry(self):
        with mock.patch.object(docker.client.DockerClient, 'login', return_value=None):
            image.login_to_docker_registry(
                'docker.io',
                os.getenv("DOCKER_HUB_USERNAME"),
                os.getenv("DOCKER_HUB_TOKEN"))

    def test_get_simulator_docker_image(self):
        docker_client = docker.from_env()
        # docker_client.images.pull('hello-world')

        with mock.patch.object(docker.models.images.ImageCollection, 'get', return_value=None):
            image.get_docker_image(docker_client, 'hello-world', pull=False)

        with mock.patch.object(docker.models.images.ImageCollection, 'get', return_value=None):
            with mock.patch.object(docker.models.images.ImageCollection, 'pull', return_value=None):
                image.get_docker_image(docker_client, 'hello-world', pull=True)

        with mock.patch.object(docker.models.images.ImageCollection, 'get', side_effect=Exception('error')):
            with self.assertRaises(docker.errors.ImageNotFound):
                image.get_docker_image(docker_client, 'unknown', pull=False)

        with mock.patch.object(docker.models.images.ImageCollection, 'get', side_effect=Exception('error')):
            with mock.patch.object(docker.models.images.ImageCollection, 'pull', side_effect=Exception('error')):
                with self.assertRaises(docker.errors.ImageNotFound):
                    image.get_docker_image(docker_client, 'unknown', pull=True)

    def test_pull_docker_image(self):
        with mock.patch.object(docker.client.DockerClient, 'login', return_value=None):
            docker_client = image.login_to_docker_registry(
                'docker.io',
                os.getenv("DOCKER_HUB_USERNAME"),
                os.getenv("DOCKER_HUB_TOKEN"))
        with mock.patch.object(docker.models.images.ImageCollection, 'pull', return_value=None):
            image.pull_docker_image(docker_client, 'hello-world')

        with mock.patch.object(docker.models.images.ImageCollection, 'pull', side_effect=docker.errors.NotFound('error')):
            with self.assertRaises(docker.errors.NotFound):
                image.pull_docker_image(docker_client, 'hello-undefined')

        with mock.patch.object(docker.models.images.ImageCollection, 'pull', side_effect=Exception('error')):
            with self.assertRaises(Exception):
                image.pull_docker_image(docker_client, '---undefined---')

    def test_tag_and_push_docker_image(self):
        with mock.patch.object(docker.client.DockerClient, 'login', return_value=None):
            docker_client = image.login_to_docker_registry(
                'docker.io',
                os.getenv("DOCKER_HUB_USERNAME"),
                os.getenv("DOCKER_HUB_TOKEN"))
        with mock.patch.object(docker.models.images.ImageCollection, 'pull', return_value=mock.Mock(tag=lambda value: True)):
            img = image.pull_docker_image(docker_client, 'hello-world')

        response = '{"error": "x"}'
        docker_client = mock.Mock(images=mock.Mock(push=lambda tag: response))
        with self.assertRaisesRegex(Exception, 'Unable to push image to'):
            with mock.patch.object(docker.models.images.ImageCollection, 'push', return_value=response):
                image.tag_and_push_docker_image(docker_client, img, 'hello-world-2')

    def test_convert_docker_image_to_singularity(self):
        with mock.patch.object(docker.client.DockerClient, 'login', return_value=None):
            docker_client = image.login_to_docker_registry(
                'docker.io',
                os.getenv("DOCKER_HUB_USERNAME"),
                os.getenv("DOCKER_HUB_TOKEN"))
        with mock.patch.object(docker.models.images.ImageCollection, 'pull', return_value=None):
            image.pull_docker_image(docker_client, 'hello-world')

        def side_effect(cmd):
            with open(cmd[2], 'w'):
                pass

        with mock.patch('subprocess.check_call', side_effect=side_effect):
            filename = image.convert_docker_image_to_singularity('hello-world')
        os.remove(filename)

        tmpdir = tempfile.mkdtemp()
        singularity_filename = os.path.join(tmpdir, 'subdir-1', 'subdir-2', 'test.sif')
        with mock.patch('subprocess.check_call', side_effect=side_effect):
            image.convert_docker_image_to_singularity('hello-world', singularity_filename=singularity_filename)
        shutil.rmtree(tmpdir)
