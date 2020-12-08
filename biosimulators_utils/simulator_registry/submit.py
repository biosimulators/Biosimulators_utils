""" Methods for submitting simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SimulatorSubmission  # noqa: F401
import requests

GH_ISSUE_ENDPOINT = 'https://api.github.com/repos/biosimulators/Biosimulators/issues'


__all__ = ['submit_simulator_to_biosimulators_registry', 'build_gh_issue_body']


def submit_simulator_to_biosimulators_registry(simulator, gh_username, gh_access_token):
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
