from biosimulators_utils import image
from unittest import mock
import docker
import os
import shutil
import tempfile
import unittest


class ImageTestCase(unittest.TestCase):
    def test_login_to_docker_registry(self):
        image.login_to_docker_registry('ghcr.io', os.getenv("GHCR_USERNAME"), os.getenv("GHCR_TOKEN"))

    def test_pull_docker_image(self):
        image.pull_docker_image('hello-world')

        with self.assertRaises(docker.errors.NotFound):
            image.pull_docker_image('hello-undefined')

        with self.assertRaises(Exception):
            image.pull_docker_image('---undefined---')

    def test_tag_and_push_docker_image(self):
        img = image.pull_docker_image('hello-world')

        response = '{"error": "x"}'
        docker_client = mock.Mock(images=mock.Mock(push=lambda tag: response))
        with mock.patch('docker.from_env', return_value=docker_client):
            with self.assertRaises(Exception):
                image.tag_and_push_docker_image(img, 'hello-world-2')

    def test_convert_docker_image_to_singularity(self):
        filename = image.convert_docker_image_to_singularity('hello-world')
        os.remove(filename)

        tmpdir = tempfile.mkdtemp()
        singularity_filename = os.path.join(tmpdir, 'subdir-1', 'subdir-2', 'test.sif')
        image.convert_docker_image_to_singularity('hello-world', singularity_filename=singularity_filename)
        shutil.rmtree(tmpdir)
