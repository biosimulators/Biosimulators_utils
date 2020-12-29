""" Data model for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum

__all__ = [
    'SoftwareInterface',
    'AlgorithmSubstitutionPolicy',
]


class SoftwareInterface(str, enum.Enum):
    """ Software interface """
    library = 'library'
    command_line = 'command-line application'
    desktop_application = 'desktop application'
    mobile_application = 'mobile application'
    web_service = 'web service'
    web_application = 'web application'
    biosimulators_docker_image = 'BioSimulators Docker image'


class AlgorithmSubstitutionPolicy(str, enum.Enum):
    """ Algorithm substitution policy """

    NONE = 'NONE'
    # algorithms should not be substituted

    SAME_MATH = 'SAME_MATH'
    # algorithms can be substituted with mathematically-equivalent algorithms (e.g. SSA, NRM)

    SAME_FRAMEWORK = 'SAME_FRAMEWORK'
    # any algorithms of the same framework can be substituted (e.g., CVODE, LSODA)
