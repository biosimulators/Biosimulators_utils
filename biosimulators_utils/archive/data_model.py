""" Data model for archives (e.g., zip files)

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..utils.core import are_lists_equal, none_sorted

__all__ = [
    'Archive',
    'ArchiveFile',
]


class Archive(object):
    """ An archive (e.g., zip file)

    Attributes:
        files (:obj:`list` of :obj:`ArchiveFile`): files
    """

    def __init__(self, files=None):
        """
        Args:
            files (:obj:`list` of :obj:`ArchiveFile`, optional): files
        """
        self.files = files or []

    def to_tuple(self):
        """ Tuple representation of an archive

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of an archive
        """
        return (
            tuple(none_sorted(file.to_tuple() for file in self.files)),
        )

    def is_equal(self, other):
        """ Determine if two archives are equal

        Args:
            other (:obj:`ArchiveFile`): another archive

        Returns:
            :obj:`bool`: :obj:`True`, if two archives are equal
        """
        return self.__class__ == other.__class__ \
            and are_lists_equal(self.files, other.files)


class ArchiveFile(object):
    """ A file in a archive (e.g., zip file)

    Attributes:
        local_path (:obj:`str`): path within local filesytem
        archive_path (:obj:`str`): archive_path
    """

    def __init__(self, local_path=None, archive_path=None):
        """
        Args:
            local_path (:obj:`str`, optional): path within local filesytem
            archive_path (:obj:`str`, optional): archive_path
        """
        self.local_path = local_path
        self.archive_path = archive_path

    def to_tuple(self):
        """ Tuple representation of a file

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a file
        """
        return (self.local_path, self.archive_path)

    def is_equal(self, other):
        """ Determine if two files are equal

        Args:
            other (:obj:`ArchiveFile`): another file

        Returns:
            :obj:`bool`: :obj:`True`, if two files are equal
        """
        return self.__class__ == other.__class__ \
            and self.local_path == other.local_path \
            and self.archive_path == other.archive_path
