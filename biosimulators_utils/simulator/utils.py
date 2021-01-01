""" Utilities for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-30
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
from .data_model import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS


def get_algorithm_substitution_policy():
    """ Get the current algorithm substitution policy based on the value of the ``ALGORITHM_SUBSTITUTION_POLICY``
    environment variable.

    Returns:
        :obj:`AlgorithmSubstitutionPolicy`: policy

    Raises:
        :obj:`ValueError`: if the value of ``ALGORITHM_SUBSTITUTION_POLICY`` is not the name of a recognized policy
    """
    policy_name = get_config().ALGORITHM_SUBSTITUTION_POLICY
    policy = AlgorithmSubstitutionPolicy.__members__.get(policy_name, None)
    if policy is None:
        msg = (
            '`{}` is not a valid value of `ALGORITHM_SUBSTITUTION_POLICY`. '
            '`ALGORITHM_SUBSTITUTION_POLICY` must have one of the following values:\n  - {}'
        ).format(policy_name or '',
                 '\n  - '.join('`' + policy.value + '`' for policy, _ in
                               sorted(ALGORITHM_SUBSTITUTION_POLICY_LEVELS.items(), key=lambda policy_level: policy_level[1])))
        raise ValueError(msg)
    return policy
