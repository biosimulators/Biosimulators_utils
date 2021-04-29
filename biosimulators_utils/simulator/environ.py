""" Common environment variables for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import EnvironmentVariable
from kisao import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS

__all__ = [
    'ENVIRONMENT_VARIABLES',
]

ENVIRONMENT_VARIABLES = {
    AlgorithmSubstitutionPolicy: EnvironmentVariable(
        name='ALGORITHM_SUBSTITUTION_POLICY',
        description='Policy for substituting alternative algorithms.',
        options=[policy.value for policy, _ in sorted(ALGORITHM_SUBSTITUTION_POLICY_LEVELS.items(),
                                                      key=lambda policy_level: policy_level[1])],
        default=AlgorithmSubstitutionPolicy.SIMILAR_VARIABLES,
        more_info_url='https://biosimulators.org/conventions/simulator-interfaces',
    )
}
