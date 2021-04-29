""" Methods for processing submissions to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SimulatorSubmission
import io
import yaml
import yamldown

__all__ = ['get_simulator_submission_from_gh_issue_body']


def get_simulator_submission_from_gh_issue_body(body):
    """ Get a simulator submission from the YAML-structured data in an issue

    Args:
       body (:obj:`str`): body of a GitHub issue for the submission of a simulator

    Returns:
        :obj:`SimulatorSubmission`: simulator submission
    """
    body_stream = io.StringIO(body.replace('\r', ''))

    # hack to make yamldown work with Python 3.9
    if not hasattr(yaml, 'FullLoader'):
        yaml.FullLoader = yaml.Loader

    data, _ = yamldown.load(body_stream)

    return get_simulator_submission_from_gh_issue_body_data(data)


def get_simulator_submission_from_gh_issue_body_data(body_data):
    """ Get a simulator submission from the YAML-structured data in an issue

    Args:
       body (:obj:`object`): data from the body of a GitHub issue for the submission of a simulator

    Returns:
        :obj:`SimulatorSubmission`: simulator submission

    Raises:
        :obj:`ValueError`: if submission is invalid (e.g., missing or extra keys)
    """
    id = body_data.get('id', None) or None
    version = body_data.get('version', None) or None
    specifications_url = body_data.get('specificationsUrl', None) or None
    specifications_patch = body_data.get('specificationsPatch', {}) or {}
    validate_image = body_data.get('validateImage', False)
    commit_simulator = body_data.get('commitSimulator', False)

    # validate properties of submission
    errors = []

    if not id:
        errors.append("Simulator submissions must provide the id for the simulator.")

    if not version:
        errors.append("Simulator submissions must provide the version for the simulator.")

    if not specifications_url:
        errors.append("Simulator submissions must provide a URL where the specifications of the simulator can be downloaded.")

    allowed_keys = set(['id', 'version', 'specificationsUrl', 'specificationsPatch', 'validateImage', 'commitSimulator'])
    extra_keys = set(body_data.keys()).difference(allowed_keys)
    if extra_keys:
        errors.append(('Simulator submissions should only use the keys '
                       '"id", "version", "specificationsUrl", "specificationsPatch", validateImage", and "commitSimulator". '
                       'The following keys are invalid:\n  - {}'.format('\n  - '.join(sorted(extra_keys)))))

    if errors:
        raise ValueError("\n\n".join(errors))

    # return submission
    return SimulatorSubmission(id=id, version=version, specifications_url=specifications_url,
                               specifications_patch=specifications_patch,
                               validate_image=validate_image, commit_simulator=commit_simulator)
