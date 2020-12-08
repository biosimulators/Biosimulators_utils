""" Data model for submitting simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum


class IssueLabel(str, enum.Enum):
    validated = 'Validated'
    invalid = 'Invalid'
    approved = 'Approved'
    action_error = 'Action error'


class SimulatorSubmission(object):
    """ Submission of a simulator to the BioSimulators registry

    Attributes:
        id (:obj:`str`): id of simulator (e.g., `tellurium` or `vcell`)
        version (:obj:`str`): version of simulator (e.g., `2.1.6`)
        specifications_url (:obj:`str`): URL for the specifications of the version of the simulator
            (e.g., `https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/2.1.6/biosimulators.json`)
    """

    def __init__(self, id=None, version=None, specifications_url=None):
        """
        Args:
            id (:obj:`str`, optional): id of simulator
            version (:obj:`str`, optional): version of simulator
            specifications_url (:obj:`str`, optional): URL for the specifications of the version of the simulator
        """
        self.id = id
        self.version = version
        self.specifications_url = specifications_url

    def to_tuple(self):
        """ Tuple representation of a person

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a person
        """
        return (self.id, self.version, self.specifications_url)

    def is_equal(self, other):
        """ Determine if two submissions are equal

        Args:
            other (:obj:`SimulatorSubmission`): another submission

        Returns:
            :obj:`bool`: :obj:`True`, if two submissions are equal
        """
        return self.__class__ == other.__class__ \
            and self.id == other.id \
            and self.version == other.version \
            and self.specifications_url == other.specifications_url
