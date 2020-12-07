""" Methods for submitting simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SimulatorSubmission
import io
import requests
import yamldown

GH_ISSUE_ENDPOINT = 'https://api.github.com/repos/biosimulators/Biosimulators/issues'


def register_simulator_with_biosimulators(simulator, gh_username, gh_access_token):
    """ Submit a version of a simulation tool for review for inclusion in the BioSimulators registry. 
    This will create a GitHub issue which the BioSimulators Team will use to review your submission.

    This method requires a GitHub access and personal access token. This access token must have the `public_repo` scope.
    Instructions for creating an access token are available in the
    `GitHub documentation <https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token`>_.

    Args:
        simulator (:obj:`SimulatorSubmission`): simulator        
        gh_username (:obj:`str`): GitHub username (e.g., `jonrkarr`)
        gh_access_token (:obj:`str`): GitHub personal access token.

    Raises:
        :obj:`requests.exceptions.HTTPError`: if the simulator is not successfully submitted for review
    """

    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }

    data = {
        "labels": ["Submit simulator"],
        "title": "Submit {} {}".format(simulator.id, simulator.version),
        "body": build_gh_issue_body(simulator),
    }

    response = requests.post(GH_ISSUE_ENDPOINT,
                             headers=headers,
                             auth=(gh_username, gh_access_token),
                             json=data)
    response.raise_for_status()


def build_gh_issue_body(simulator):
    """ Build the body of a GitHub issue for the submission of a simulator

    Args:
        simulator (:obj:`SimulatorSubmission`): simulator

    Returns:
        :obj:`str`: body for a GitHub issue for the submission of a simulator
    """
    return "\n".join([
        "---",
        "id: {}".format(simulator.id),
        "version: {}".format(simulator.version),
        "specificationsUrl: {}".format(simulator.specifications_url),
        "",
        "---",
    ])


def parse_gh_issue_body(body):
    """ Get the YAML-structured data in an issue

    Args:
       body (:obj:`str`): body of a GitHub issue for the submission of a simulator

    Returns:
        :obj:`SimulatorSubmission`: simulator
    """
    body = io.StringIO(body.replace('\r', ''))
    data, _ = yamldown.load(body)
    return SimulatorSubmission(
        id=data.get('id', None) or None,
        version=data.get('version', None) or None,
        specifications_url=data.get('specificationsUrl', None) or None,
    )
