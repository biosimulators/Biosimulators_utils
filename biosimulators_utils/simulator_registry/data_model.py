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
        specifications_patch (:obj:`dict`): superseding specifications to those at :obj:`specifications_url`
        validate_image (:obj:`bool`): if :obj:`True`, validate Docker image
        commit_simulator (:obj:`bool`): if :obj:`True`, commit simulator to database
    """

    def __init__(self, id: str = None, version: str = None, specifications_url: str = None,
                 specifications_patch: dict = None,
                 validate_image: bool = False, commit_simulator: bool = False):
        """
        Args:
            id (:obj:`str`, optional): id of simulator
            version (:obj:`str`, optional): version of simulator
            specifications_url (:obj:`str`, optional): URL for the specifications of the version of the simulator
            specifications_patch (:obj:`dict`, optional): superseding specifications to those at :obj:`specifications_url`
            validate_image (:obj:`bool`, optional): if :obj:`True`, validate Docker image
            commit_simulator (:obj:`bool`, optional): if :obj:`True`, commit simulator to database
        """
        self.id: str = id
        self.version: str = version
        self.specifications_url: str = specifications_url
        self.specifications_patch: dict = specifications_patch or {}
        self.validate_image: bool = validate_image
        self.commit_simulator: bool = commit_simulator

    def to_tuple(self):
        """ Tuple representation of a person

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a person
        """
        return (self.id, self.version, self.specifications_url, self.specifications_patch, self.validate_image, self.commit_simulator)

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
            and self.specifications_url == other.specifications_url \
            and self.specifications_patch == other.specifications_patch \
            and self.validate_image == other.validate_image \
            and self.commit_simulator == other.commit_simulator
