""" Core data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum

__all__ = [
    'Person',
    'Identifier',
    'OntologyTerm',
    'ValueType',
]


class Person(object):
    """ A person

    Attributes:
        given_name (:obj:`str`): given/first name
        other_name (:obj:`str`): other/middle name
        family_name (:obj:`str`): family/last name
    """

    def __init__(self, given_name=None, other_name=None, family_name=None):
        """
        Args:
            given_name (:obj:`str`, optional): given/first name
            other_name (:obj:`str`, optional): other/middle name
            family_name (:obj:`str`, optional): family/last name
        """
        self.given_name = given_name
        self.other_name = other_name
        self.family_name = family_name

    def to_tuple(self):
        """ Tuple representation of a person

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a person
        """
        return (self.family_name, self.other_name, self.given_name)

    def is_equal(self, other):
        """ Determine if two authors are equal

        Args:
            other (:obj:`Person`): another author

        Returns:
            :obj:`bool`: :obj:`True`, if two authors are equal
        """
        return self.__class__ == other.__class__ \
            and self.given_name == other.given_name \
            and self.other_name == other.other_name \
            and self.family_name == other.family_name


class Identifier(object):
    """ An identifier

    Attributes:
        namespace (:obj:`str`): namespace
        id (:obj:`str`): id
        url (:obj:`str`): URL
    """

    def __init__(self, namespace=None, id=None, url=None):
        """
        Args:
            namespace (:obj:`str`, optional): namespace
            id (:obj:`str`, optional): id
            url (:obj:`str`, optional): URL
        """
        self.namespace = namespace
        self.id = id
        self.url = url

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.namespace, self.id, self.url)

    def is_equal(self, other):
        """ Determine if identifiers are equal

        Args:
            other (:obj:`Identifier`): another identifier

        Returns:
            :obj:`bool`: :obj:`True`, if two identifiers are equal
        """
        return self.__class__ == other.__class__ \
            and self.namespace == other.namespace \
            and self.id == other.id \
            and self.url == other.url


class OntologyTerm(Identifier):
    """ Term in an ontology """
    pass


class ValueType(str, enum.Enum):
    """ A type of value (e.g., of a model attribute change or algorithm parameter change) """
    boolean = 'boolean'
    integer = 'integer'
    float = 'float'
    string = 'string'
    kisao_id = 'kisaoId'
    list = 'list'
    object = 'object'
    any = 'any'
