""" Methods for processing submissions to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SimulatorSubmission
import io
import yamldown


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
