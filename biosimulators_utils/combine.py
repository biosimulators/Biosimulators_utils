from .utils import are_lists_equal
import abc
import datetime
import dateutil.parser
import libcombine
import os

__all__ = [
    'CombineArchive',
    'CombineArchiveContent',
    'CombineArchiveAuthor',
    'CombineArchiveWriter',
    'CombineArchiveReader',
]


class CombineArchiveBase(abc.ABC):
    """ A COMBINE/OMEX archive

    Attributes:
        description (:obj:`str`): description
        authors (:obj:`list` of :obj:`Author`): authors
        created (:obj:`datetime.datetime`): created date
        updated (:obj:`datetime.datetime`): updated date
    """
    pass


class CombineArchive(CombineArchiveBase):
    """ A COMBINE/OMEX archive

    Attributes:
        contents (:obj:`list` of :obj:`CombineArchiveContent`): contents of the archive
        description (:obj:`str`): description
        authors (:obj:`list` of :obj:`Author`): authors
        created (:obj:`datetime.datetime`): created date
        updated (:obj:`datetime.datetime`): updated date
    """

    def __init__(self, contents=None, description=None, authors=None, created=None, updated=None):
        """
        Args:
            contents (:obj:`list` of :obj:`CombineArchiveContent`, optional): contents of the archive
            description (:obj:`str`, optional): description
            authors (:obj:`list` of :obj:`Author`, optional): authors
            created (:obj:`datetime.datetime`, optional): created date
            updated (:obj:`datetime.datetime`, optional): updated date
        """
        self.contents = contents or []
        self.description = description
        self.authors = authors or []
        self.created = created
        self.updated = updated

    def get_master_content(self):
        """ Get the master content of an archive

        Returns:
            :obj:`CombineArchiveContent` or :obj:`None`: master content

        Raises:
            :obj:`ValueError`: if more than one content item is marked as master
        """
        master_content = []
        for content in self.contents:
            if content.master:
                master_content.append(content)
        if not master_content:
            return None
        if len(master_content) == 1:
            return master_content[0]
        raise ValueError('Multiple content items are marked as master')

    def to_tuple(self):
        """ Tuple representation of a COMBINE/OMEX archive

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a COMBINE/OMEX archive
        """
        contents = tuple(c.to_tuple() for c in sorted(self.contents, key=CombineArchiveContent.to_tuple))
        authors = tuple(a.to_tuple() for a in sorted(self.authors, key=CombineArchiveAuthor.to_tuple))
        return (contents, self.description, authors, self.created, self.updated)

    def is_equal(self, other):
        """ Determine if two content items are equal

        Args:
            other (:obj:`CombineArchiveContent`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two archives are equal
        """
        return self.__class__ == other.__class__ \
            and are_lists_equal(self.contents, other.contents) \
            and self.description == other.description \
            and are_lists_equal(self.authors, other.authors) \
            and self.created == other.created \
            and self.updated == other.updated


class CombineArchiveContent(CombineArchiveBase):
    """ A content item (e.g., file) in a COMBINE/OMEX archive

    Attributes:
        location (:obj:`str`): path to the content
        format (:obj:`str`): URL for the specification of the format of the content
        master (:obj:`bool`): :obj:`True`, if the content is the "primary" content of the parent archive
        description (:obj:`str`): description
        authors (:obj:`list` of :obj:`Author`): authors
        created (:obj:`datetime.datetime`): created date
        updated (:obj:`datetime.datetime`): updated date
    """

    def __init__(self, location, format, master=False, description=None, authors=None, created=None, updated=None):
        """
        Args:
            location (:obj:`str`): path to the content
            format (:obj:`str`): URL for the specification of the format of the content
            master (:obj:`bool`): :obj:`True`, if the content is the "primary" content of the parent archive
            description (:obj:`str`, optional): description
            authors (:obj:`list` of :obj:`Author`, optional): authors
            created (:obj:`datetime.datetime`, optional): created date
            updated (:obj:`datetime.datetime`, optional): updated date
        """
        self.location = location
        self.format = format
        self.master = master
        self.description = description
        self.authors = authors or []
        self.created = created
        self.updated = updated

    def to_tuple(self):
        """ Tuple representation of a content item of a COMBINE/OMEX archive

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of a content item of a COMBINE/OMEX archive
        """
        authors = tuple(a.to_tuple() for a in sorted(self.authors, key=CombineArchiveAuthor.to_tuple))
        return (self.location, self.format, self.master, self.description, authors, self.created, self.updated)

    def is_equal(self, other):
        """ Determine if two content items are equal

        Args:
            other (:obj:`CombineArchiveContent`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two content items are equal
        """
        return self.__class__ == other.__class__ \
            and self.location == other.location \
            and self.format == other.format \
            and self.master == other.master \
            and self.description == other.description \
            and are_lists_equal(self.authors, other.authors) \
            and self.created == other.created \
            and self.updated == other.updated


class CombineArchiveAuthor(object):
    """ An author of a COMBINE/OMEX archive of a content item of a COMBINE/OMEX archive

    Attributes:
        given_name (:obj:`str`): given/first name
        family_name (:obj:`str`): family/last name
    """

    def __init__(self, given_name=None, family_name=None):
        """
        Args:
            given_name (:obj:`str`, optional): given/first name
            family_name (:obj:`str`, optional): family/last name
        """
        self.given_name = given_name
        self.family_name = family_name

    def is_equal(self, other):
        """ Determine if two authors are equal

        Args:
            other (:obj:`CombineArchiveAuthor`): another author

        Returns:
            :obj:`bool`: :obj:`True`, if two authors are equal
        """
        return self.__class__ == other.__class__ \
            and self.given_name == other.given_name \
            and self.family_name == other.family_name

    def to_tuple(self):
        """ Tuple representation of an author

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation of an author
        """
        return (self.family_name, self.given_name)


class CombineArchiveWriter(object):
    """ Writer for COMBINE/OMEX archives """

    @classmethod
    def run(cls, archive, in_dir, out_file):
        """ Write an archive to a file

        Args:
            archive (:obj:`CombineArchive`): description of archive
            in_dir (:obj:`str`): directory which contains the files in the archive
            out_file (:obj:`str`): path to save archive

        Raises:
            :obj:`AssertionError`: if files could not be added to the archive or the archive could not be
                saved
        """
        # instantiate archive
        archive_comb = libcombine.CombineArchive()

        # set metadata about archive
        cls._write_metadata(archive, archive_comb, '.')

        # add files to archive
        for content in archive.contents:
            assert archive_comb.addFile(
                os.path.join(in_dir, content.location),
                content.location,
                content.format if content.format else '',
                content.master
            )
            cls._write_metadata(content, archive_comb, content.location)

        # save archive to a file
        assert archive_comb.writeToFile(out_file)

    @classmethod
    def _write_metadata(cls, obj, archive_comb, filename):
        """ Write metadata about an archive or a file in an archive
        
        Args:
            obj (:obj:`CombineArchiveBase`): archive or file in an archive
            archive_comb (:obj:`libcombine.CombineArchive`): archive
            filename (:obj:`str`): path of object with archive
        
        Raises:
            :obj:`NotImplementedError`: of the updated date is not defined
        """
        desc_comb = libcombine.OmexDescription()
        desc_comb.setAbout(filename)
        if obj.description:
            desc_comb.setDescription(obj.description)
        for author in obj.authors:
            creator_comb = libcombine.VCard()
            if author.given_name:
                creator_comb.setGivenName(author.given_name)
            if author.family_name:
                creator_comb.setFamilyName(author.family_name)
            desc_comb.addCreator(creator_comb)
        if obj.created:
            date_comb = libcombine.Date()
            date_comb.setDateAsString(obj.created.strftime('%Y-%m-%dT%H:%M:%SZ'))
            desc_comb.setCreated(date_comb)
        if not obj.updated:
            raise NotImplementedError('libcombine does not support undefined updated dates')
        if obj.updated:
            date_comb = libcombine.Date()
            date_comb.setDateAsString(obj.updated.strftime('%Y-%m-%dT%H:%M:%SZ'))
            desc_comb.getModified().append(date_comb)
        archive_comb.addMetadata(filename, desc_comb)


class CombineArchiveReader(object):
    """ Reader for COMBINE/OMEX archives """

    NONE_DATETIME = '2000-01-01T00:00:00Z'

    @classmethod
    def run(cls, in_file, out_dir):
        """ Read an archive from a file

        Args:
            in_file (:obj:`str`): path to save archive
            out_dir (:obj:`str`): directory which contains the files in the archive

        Returns:
            :obj:`CombineArchive`: description of archive

        Raises:
            :obj:`ArchiveIoError`: archive is invalid
        """
        archive_comb = libcombine.CombineArchive()
        if not archive_comb.initializeFromArchive(in_file):
            raise ValueError("Invalid COMBINE archive")

        # instantiate archive
        archive = CombineArchive()

        # read metadata
        cls._read_metadata(archive_comb, '.', archive)

        # read files
        for location in archive_comb.getAllLocations():
            location = location.c_str()
            file_comb = archive_comb.getEntryByLocation(location)

            if file_comb.isSetFormat():
                format = file_comb.getFormat()
            else:
                format = None

            content = CombineArchiveContent(
                location=location,
                format=format,
            )
            cls._read_metadata(archive_comb, location, content)
            archive.contents.append(content)

        file_comb = archive_comb.getMasterFile()
        if file_comb:
            location = file_comb.getLocation()
            master_content = next((content for content in archive.contents if content.location == location), None)
            if master_content:
                master_content.master = True

        # extract files
        archive_comb.extractTo(out_dir)

        # return information about archive
        return archive

    @classmethod
    def _read_metadata(cls, archive_comb, filename, obj):
        """ Read metadata about an archive or a file in an archive

        Args:
            archive_comb (:obj:`libcombine.CombineArchive`): archive
            filename (:obj:`str`): path to object within archive
            obj (:obj:`CombineArchiveBase`): object to add metadata to
        """
        desc_comb = archive_comb.getMetadataForLocation(filename)
        if not desc_comb.isEmpty():
            obj.description = desc_comb.getDescription() or None

            for creator_comb in desc_comb.getCreators():
                obj.authors.append(CombineArchiveAuthor(
                    given_name=creator_comb.getGivenName() or None,
                    family_name=creator_comb.getFamilyName() or None,
                ))

            created_comb = desc_comb.getCreated().getDateAsString()
            if created_comb == cls.NONE_DATETIME:
                obj.created = None
            else:
                obj.created = dateutil.parser.parse(created_comb)

            obj.updated = None
            for modified_comb in desc_comb.getModified():
                updated = dateutil.parser.parse(modified_comb.getDateAsString())
                if obj.updated:
                    obj.updated = max(obj.updated, updated)
                else:
                    obj.updated = updated
