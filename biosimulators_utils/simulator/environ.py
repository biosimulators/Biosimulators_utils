""" Common environment variables for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import EnvironmentVariable, AlgorithmSubstitutionPolicy

__all__ = [
    'ENVIRONMENT_VARIABLES',
]

ENVIRONMENT_VARIABLES = {
    AlgorithmSubstitutionPolicy: EnvironmentVariable(
        name='ALGORITHM_SUBSTITUTION_POLICY',
        description='Policy for substituting alternative algorithms.',
        options=AlgorithmSubstitutionPolicy,
        default=AlgorithmSubstitutionPolicy.SAME_FRAMEWORK,
        more_info_url='https://biosimulators.org/standards/simulator-interfaces',
    )
}
