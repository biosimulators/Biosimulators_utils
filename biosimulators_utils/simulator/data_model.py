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
    'ALGORITHM_SUBSTITUTION_POLICY_LEVELS',
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

    NONE = 'None'
    # Algorithms should not be substituted.

    SAME_METHOD = 'SAME_METHOD'
    """ Algorithms can be substituted with different realizations of the same method.

    Examples:

    * GLPK Simplex method <=> SciPy Simplex method
    """

    SAME_MATH = 'SAME_MATH'
    """ Algorithms can be substituted with mathematically-equivalent algorithms.

    Examples:

    * SSA <=> Next Reaction Method
    * Simplex method <=> interior point method
    """

    SIMILAR_APPROXIMATIONS = 'SIMILAR_APPROXIMATIONS'
    """ Algorithms can be substituted with others that make similar approximations
    to the same math.

    Examples:

    * CVODE <=> LSODA <=> RK-45
    * tau leaping <=> partitioned tau leaping
    """

    DISTINCT_APPROXIMATIONS = 'DISTINCT_APPROXIMATIONS'
    """ Algorithms can be substituted with others that make distinct approximations
    to the same math.

    Examples:

    * SSA <=> tau leaping <=> Pahle hybrid method
    """

    DISTINCT_SCALES = 'DISTINCT_SCALES'
    """ Algorithms can be substituted with others that make distinct approximations
    to the same math that substantially differ in their scale.

    Examples:

    * SSA <=> CVODE
    """

    SAME_VARIABLES = 'SAME_VARIABLES'
    """ Algorithms that predict the same dependent variables can be substituted.

    Examples:

    * FBA <=> parsimonious FBA
    """

    SIMILAR_VARIABLES = 'SIMILAR_VARIABLES'
    """ Algorithms that predict similar dependent variables can be substituted.

    This is the recommended default value.

    Examples:

    * FBA <=> geometric FBA
    """

    SAME_FRAMEWORK = 'SAME_FRAMEWORK'
    """ Any algorithm of the same framework can be substituted (e.g., CVODE, LSODA).

    Examples:

    * FBA <=> FVA
    """

    ANY = 'ANY'
    # any algorithm can be substituted. Note, using any other algorithm can substantively
    # change the interpretation of a simulation. For example, switching SSA to CVODE loses
    # all information about the variance in the simulated system.


ALGORITHM_SUBSTITUTION_POLICY_LEVELS = {
    AlgorithmSubstitutionPolicy.NONE: 0,
    AlgorithmSubstitutionPolicy.SAME_METHOD: 1,
    AlgorithmSubstitutionPolicy.SAME_MATH: 2,
    AlgorithmSubstitutionPolicy.SIMILAR_APPROXIMATIONS: 3,
    AlgorithmSubstitutionPolicy.DISTINCT_APPROXIMATIONS: 4,
    AlgorithmSubstitutionPolicy.DISTINCT_SCALES: 5,
    AlgorithmSubstitutionPolicy.SAME_VARIABLES: 6,
    AlgorithmSubstitutionPolicy.SIMILAR_VARIABLES: 7,
    AlgorithmSubstitutionPolicy.SAME_FRAMEWORK: 8,
    AlgorithmSubstitutionPolicy.ANY: 9,
}


class EnvironmentVariable(object):
    """ Environment variable supported by a simulator

    Attributes:
        name(: obj: `str`): name
        description(: obj: `str`): description
        options(: obj: `type`): enumeration of options
        default(: obj: `str`): default
        more_info_url(: obj: `str`): URL with more information about the variable
    """

    def __init__(self, name=None, description=None, options=None, default=None, more_info_url=None):
        """
        Args:
            name(: obj: `str`, optional): name
            description(: obj: `str`, optional): description
            options(: obj: `type`, optional): enumeration of options
            default(: obj: `str`, optional): default
            more_info_url(: obj: `str`, optional): URL with more information about the variable
        """
        self.name = name
        self.description = description
        self.options = options
        self.default = default
        self.more_info_url = more_info_url
