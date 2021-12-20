from biosimulators_utils.biosimulations.utils import (
    run_simulation_project, publish_simulation_project, get_published_project,
    get_authorization_for_client, validate_biosimulations_api_response,
)
from unittest import mock
import os
import requests
import simplejson.errors
import unittest


class BioSimulationsUtilsTestCase(unittest.TestCase):
    def test_run_simulation_project_by_file(self):
        name = 'test'
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex')
        simulator = 'copasi'
        with mock.patch.object(requests.Session, 'post', return_value=mock.Mock(
            raise_for_status=lambda: None,
            json=lambda: {
                'id': '*' * 30
            }
        )):
            id = run_simulation_project(name, filename, simulator, auth='aaa bbb')
        self.assertIsInstance(id, str)
        self.assertNotEqual(id, '')

    def test_run_simulation_project_by_url(self):
        name = 'test'
        url = 'https://github.com/biosimulators/Biosimulators_utils/blob/dev/tests/fixtures/Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex?raw=true'
        simulator = 'copasi'
        with mock.patch.object(requests.Session, 'post', return_value=mock.Mock(
            raise_for_status=lambda: None,
            json=lambda: {
                'id': '*' * 30
            }
        )):
            id = run_simulation_project(name, url, simulator, project_id='test', auth='aaa bbb')
        self.assertIsInstance(id, str)
        self.assertNotEqual(id, '')

    def test_publish_simulation_project(self):
        def raise_for_status():
            raise Exception('invalid')

        with mock.patch.object(requests.Session, 'get', return_value=mock.Mock(
            raise_for_status=raise_for_status,
            status_code=404,
        )):
            with mock.patch.object(requests.Session, 'post', return_value=mock.Mock(
                raise_for_status=lambda: None,
                status_code=200,
            )):
                publish_simulation_project('xxx', 'test', auth='aaa bbb')

        with mock.patch.object(requests.Session, 'get', return_value=mock.Mock(
            raise_for_status=lambda: None,
            status_code=200,
            json=lambda: {
                'id': 'test',
                'simulationRun': 'xxx',
            }
        )):
            with mock.patch.object(requests.Session, 'put', return_value=mock.Mock(
                raise_for_status=lambda: None,
                status_code=200,
            )):
                publish_simulation_project('xxx', 'test')

    def test_get_published_project(self):
        with mock.patch.object(requests.Session, 'get', return_value=mock.Mock(
            raise_for_status=lambda: None,
            status_code=200,
            json=lambda: {
                'id': 'test',
                'simulationRun': 'xxx',
            }
        )):
            project = get_published_project('test')
            self.assertEqual(project, {
                'id': 'test',
                'simulationRun': 'xxx',
            })

        def raise_for_status():
            raise Exception('invalid')

        with mock.patch.object(requests.Session, 'get', return_value=mock.Mock(
            raise_for_status=raise_for_status,
            status_code=404,
            json=lambda: {
                'id': 'test',
                'simulationRun': 'xxx',
            }
        )):
            project = get_published_project('test')
            self.assertEqual(project, None)

    def test_get_authorization_for_client(self):
        with mock.patch('requests.post', return_value=mock.Mock(
            raise_for_status=lambda: None,
            json=lambda: {
                'token_type': 'aaa',
                'access_token': 'bbb',
            }
        )):
            self.assertEqual(get_authorization_for_client('xxx', 'yyy'), 'aaa bbb')

    def test_validate_biosimulations_api_response(self):
        response = mock.Mock(
            raise_for_status=lambda: None,
            json=lambda: {
                'token_type': 'aaa',
                'access_token': 'bbb',
            }
        )
        validate_biosimulations_api_response(response, 'Summary')

        def raise_for_status():
            raise requests.RequestException('invalid')
        response = mock.Mock(
            raise_for_status=raise_for_status,
            json=lambda: {
                'error': [{
                    'status': "404",
                    'title': 'Project with id test3 not found.',
                    'detail': '"Project with id test3 not found."',
                }],
            }
        )
        with self.assertRaises(ValueError):
            validate_biosimulations_api_response(response, 'Summary', ValueError)

        with self.assertRaises(requests.RequestException):
            validate_biosimulations_api_response(response, 'Summary')

        def raise_for_status():
            raise requests.RequestException('invalid')

        def json():
            return {
            }
        response = mock.Mock(
            raise_for_status=raise_for_status,
            json=json
        )
        with self.assertRaises(requests.RequestException):
            validate_biosimulations_api_response(response, 'Summary', ValueError)
