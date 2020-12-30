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
    'EnvironmentVariable',
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


class EnvironmentVariable(object):
    """ Environment variable supported by a simulator

    Attributes:
        name (:obj:`str`): name
        description (:obj:`str`): description
        options (:obj:`type`): enumeration of options
        default (:obj:`str`): default
        more_info_url (:obj:`str`): URL with more information about the variable
    """

    def __init__(self, name=None, description=None, options=None, default=None, more_info_url=None):
        """
        Args:
            name (:obj:`str`, optional): name
            description (:obj:`str`, optional): description
            options (:obj:`type`, optional): enumeration of options
            default (:obj:`str`, optional): default
            more_info_url (:obj:`str`, optional): URL with more information about the variable
        """
        self.name = name
        self.description = description
        self.options = options
        self.default = default
        self.more_info_url = more_info_url
