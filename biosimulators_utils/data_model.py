__all__ = [
    'Person',
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
