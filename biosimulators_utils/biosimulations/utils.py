""" Utility methods for working with BioSimulations

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-01-30
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""
import requests


def validate_biosimulations_api_response(response, failure_introductory_message):
    """ Validate a response from one of BioSimulation's APIs.

    Args:
        response (:obj:`requests.models.Response`): API response
        failure_introductory_message (:obj:`str`): introductory message for failures

    Raises:
        :obj:`requests.RequestException`
    """
    try:
        response.raise_for_status()

    except requests.RequestException as exception:
        error_messages = []
        for error in response.json()['error']:
            pointer = error.get('source', {}).get('pointer', None)
            error_messages.append('{} ({}):{}{}'.format(
                error['title'], error['status'],
                ' `{}` is not valid'.format(pointer) if pointer else '',
                '\n\n  ' + error['detail'].replace('\n', '\n  ') if error.get('detail', None) else '',
            ))

        error_message = '{}\n\n  - {}'.format(
            failure_introductory_message,
            '\n\n  - '.join(msg.replace('\n', '\n    ') for msg in error_messages))

        exception.args = (error_message,)

        raise
