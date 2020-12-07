""" Data model for BioSimulations metadata

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import Person, Identifier, OntologyTerm  # noqa: F401
from ..utils.core import are_lists_equal, none_sorted
import datetime  # noqa: F401

__all__ = [
    'Metadata',
    'ExternalReferences',
    'Citation',
]


class Metadata(object):
    """ Metadata about an object

    Attributes:
        description (:obj:`str`): description
        tags (:obj:`list` of :obj:`str`): tags
        authors (:obj:`list` of :obj:`Person`): authors
        references (:obj:`ExternalReferences`): identifiers and citations
        license (:obj:`OntologyTerm`): license
        created (:obj:`datetime.datetime`): created date-time
        updated (:obj:`datetime.datetime`): updated date-time
    """

    def __init__(self, description=None, tags=None, authors=None, references=None, license=None, created=None, updated=None):
        """
        Args:
            description (:obj:`str`, optional): description
            tags (:obj:`list` of :obj:`str`, optional): tags
            authors (:obj:`list` of :obj:`Person`, optional): authors
            references (:obj:`ExternalReferences`, optional): identifiers and citations
            license (:obj:`OntologyTerm`, optional): license
            created (:obj:`datetime.datetime`, optional): created date-time
            updated (:obj:`datetime.datetime`, optional): updated date-time
        """
        self.description = description
        self.tags = tags or []
        self.authors = authors or []
        self.references = references
        self.license = license
        self.created = created
        self.updated = updated

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.description, tuple(self.tags),
                tuple(none_sorted(author.to_tuple() for author in self.authors)),
                self.references.to_tuple() if self.references else None,
                self.license.to_tuple() if self.license else None,
                self.created,
                self.updated,
                )

    def is_equal(self, other):
        """ Determine if metadata are equal

        Args:
            other (:obj:`Metadata`): another metadata

        Returns:
            :obj:`bool`: :obj:`True`, if two metadata are equal
        """
        return self.__class__ == other.__class__ \
            and self.description == other.description \
            and none_sorted(self.tags) == none_sorted(other.tags) \
            and are_lists_equal(self.authors, other.authors) \
            and ((self.references is None and self.references == other.references)
                 or (self.references is not None and self.references.is_equal(other.references))) \
            and ((self.license is None and self.license == other.license)
                 or (self.license is not None and self.license.is_equal(other.license))) \
            and self.created == other.created \
            and self.updated == other.updated


class ExternalReferences(object):
    """ Identifiers and citations of an object

    Attributes:
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
        citations (:obj:`list` of :obj:`Citation`): citations
    """

    def __init__(self, identifiers=None, citations=None):
        """
        Args:
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
            citations (:obj:`list` of :obj:`Citation`, optional): citations
        """
        self.identifiers = identifiers or []
        self.citations = citations or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (
            tuple(none_sorted(identifier.to_tuple() for identifier in self.identifiers)),
            tuple(none_sorted(citation.to_tuple() for citation in self.citations)),
        )

    def is_equal(self, other):
        """ Determine if collections of external references are equal

        Args:
            other (:obj:`ExternalReferences`): another collection of external referencse

        Returns:
            :obj:`bool`: :obj:`True`, if two collections of external references are equal
        """
        return self.__class__ == other.__class__ \
            and are_lists_equal(self.identifiers, other.identifiers) \
            and are_lists_equal(self.citations, other.citations)


class Citation(object):
    """ A citation

    Attributes:
        title (:obj:`str`): title
        authors (:obj:`str`): authors
        journal (:obj:`str`): journal
        volume (:obj:`str`): volume
        issue (:obj:`str`): issue
        pages (:obj:`str`): pages
        year (:obj:`int`): year
        identifiers (:obj:`list` of :obj:`Identifier`): identifiers
    """

    def __init__(self, title=None, authors=None, journal=None, volume=None, issue=None, pages=None, year=None, identifiers=None):
        """
        Args:
            title (:obj:`str`, optional): title
            authors (:obj:`str`, optional): authors
            journal (:obj:`str`, optional): journal
            volume (:obj:`str`, optional): volume
            issue (:obj:`str`, optional): issue
            pages (:obj:`str`, optional): pages
            year (:obj:`int`, optional): year
            identifiers (:obj:`list` of :obj:`Identifier`, optional): identifiers
        """
        self.title = title
        self.authors = authors
        self.journal = journal
        self.volume = volume
        self.issue = issue
        self.pages = pages
        self.year = year
        self.identifiers = identifiers or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (
            self.title,
            self.authors,
            self.journal,
            self.volume,
            self.issue,
            self.pages,
            self.year,
            tuple(none_sorted(identifier.to_tuple() for identifier in self.identifiers)),
        )

    def is_equal(self, other):
        """ Determine if citations are equal

        Args:
            other (:obj:`Citation`): another citation

        Returns:
            :obj:`bool`: :obj:`True`, if two citations are equal
        """
        return self.__class__ == other.__class__ \
            and self.title == other.title \
            and self.authors == other.authors \
            and self.journal == other.journal \
            and self.volume == other.volume \
            and self.issue == other.issue \
            and self.pages == other.pages \
            and self.year == other.year \
            and are_lists_equal(self.identifiers, other.identifiers)
