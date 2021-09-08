""" Data model for references (e.g., journal articles, books)

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-09-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc
import dataclasses
import typing

__all__ = ['Reference', 'JournalArticle', 'PubMedCentralOpenAccesGraphic']


class Reference(abc.ABC):
    @abc.abstractmethod
    def get_citation(self):
        """ Get a human-readable citation for a reference

        Returns:
            :obj:`str`: human-readable citation
        """
        pass  # pragma: no cover


@dataclasses.dataclass
class JournalArticle(Reference):
    """ Journal article

    Attributes:
        pubmed_id (:obj:`str`): PubMed id
        pubmed_central_id (:obj:`str`): PubMed Central id
        doi (:obj:`str`): DOI
        authors (:obj:`list` of :obj:`str`): authors
        title (:obj:`str`): title
        journal (:obj:`str`): journal
        volume (:obj:`str`): volume
        issue (:obj:`str`): issue
        pages (:obj:`str`): pages
        year (:obj:`str`): year
        date (:obj:`str`): publication date
    """
    pubmed_id: str = None
    pubmed_central_id: str = None
    doi: str = None
    authors: typing.List[str] = dataclasses.field(default_factory=lambda: [])
    title: str = None
    journal: str = None
    volume: str = None
    issue: str = None
    pages: str = None
    year: int = None
    date: str = None

    def get_citation(self):
        """ Format a citation for a reference (e.g., "Authors. Title. Journal volume, issue: pages (year)".).

        Returns:
            :obj:`str`: formatted citation for a reference
        """

        if len(self.authors) > 1:
            authors = '{} & {}'.format(', '.join(self.authors[0:-1]), self.authors[-1])
        elif self.authors:
            authors = self.authors[0]
        else:
            authors = None

        citation = []

        if authors:
            citation.append(authors)

        if self.title:
            if citation:
                citation.append('. ')
            citation.append(self.title)
            if self.title[-1] in '.?':
                sep = ' '
            else:
                sep = '. '
        else:
            sep = ''

        if self.journal:
            citation.append(sep)
            citation.append(self.journal)

        if self.volume is not None:
            if citation:
                citation.append(' ')
            citation.append(self.volume)

        if self.issue:
            if citation:
                citation.append(', ')
            citation.append(self.issue)

        if self.pages:
            if citation:
                citation.append(': ')
            citation.append(self.pages)

        if self.year:
            if citation:
                citation.append(' ')
            citation.append('(' + str(self.year) + ')')

        citation = ''.join(citation)
        if citation:
            if citation[-1] in '.?':
                return citation
            else:
                return citation + '.'
        else:
            return None


@dataclasses.dataclass
class PubMedCentralOpenAccesGraphic(object):
    """ A PubMed Central open access graphic

    Attributes:
        id (:obj:`str`): PubMed Central id
        label (:obj:`str`): label (e.g., ``Figure 1``)
        caption (:obj:`str`): caption
        filename (:obj:`str`): local path to JPEG file for graphic
    """
    id: str = None
    label: str = None
    caption: str = None
    filename: str = None
