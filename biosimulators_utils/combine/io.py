""" Utilities for reading and writing COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import (CombineArchiveBase, CombineArchive, CombineArchiveContent,  # noqa: F401
                         CombineArchiveContentFormat, CombineArchiveContentFormatPattern)
from ..archive.io import ArchiveReader
from ..data_model import Person
from ..utils.core import flatten_nested_list_of_strings
from ..warnings import warn, BioSimulatorsWarning
import dateutil.parser
import dateutil.tz
import libcombine
import os
import re
import zipfile

__all__ = [
    'CombineArchiveWriter',
    'CombineArchiveReader',
    'CombineArchiveZipReader',
]


class CombineArchiveWriter(object):
    """ Writer for COMBINE/OMEX archives

    Attributes:
        errors (nested :obj:`list` of :obj:`str`): errors
        warnings (nested :obj:`list` of :obj:`str`): warnings
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def run(self, archive, in_dir, out_file):
        """ Write an archive to a file

        Args:
            archive (:obj:`CombineArchive`): description of archive
            in_dir (:obj:`str`): directory which contains the files in the archive
            out_file (:obj:`str`): path to save archive

        Raises:
            :obj:`AssertionError`: if files could not be added to the archive or the archive could not be
                saved
        """
        self.errors = []
        self.warnings = []

        # instantiate archive
        archive_comb = libcombine.CombineArchive()

        # set metadata about archive
        self._write_metadata(archive, archive_comb, '.')

        # add files to archive
        for i_content, content in enumerate(archive.contents):
            if not archive_comb.addFile(
                os.path.join(in_dir, content.location),
                content.location,
                content.format if content.format else '',
                content.master
            ):
                content_id = '`' + content.location + '`' if content.location else str(i_content + 1)
                msg = 'Content element {} could not be added to the archive.'.format(content_id)
                self.errors.append([msg])
                raise Exception(msg)
            self._write_metadata(content, archive_comb, content.location)

        # save archive to a file
        if not archive_comb.writeToFile(out_file):
            msg = 'Archive could not be saved.'
            self.errors.append([msg])
            raise Exception(msg)

        errors, warnings = get_combine_errors_warnings(archive_comb.getManifest())
        self.errors.extend(errors)
        self.warnings.extend(warnings)

        if self.warnings:
            warn('COMBINE/OMEX archive may be invalid.\n  ' + flatten_nested_list_of_strings(self.warnings).replace('\n', '\n  '),
                 BioSimulatorsWarning)
        if self.errors:
            raise ValueError('COMBINE/OMEX archive is invalid.\n  ' + flatten_nested_list_of_strings(self.errors).replace('\n', '\n  '))

    def write_manifest(self, contents, filename):
        """ Write an OMEX manifest file

        Args:
            contents (:obj:`list` of :obj:`CombineArchiveContent`): contents of a COMBINE/OMEX archive
            filename (:obj:`str`): path to OMEX manifest file
        """
        manifest = libcombine.CaOmexManifest()
        for content in contents:
            content_comb = manifest.createContent()

            if content.location is not None:
                content_comb.setLocation(content.location)

            if content.format is not None:
                content_comb.setFormat(content.format)

            if content.master is not None:
                content_comb.setMaster(content.master)

        errors, warnings = get_combine_errors_warnings(manifest)
        if warnings:
            msg = 'COMBINE/OMEX archive may be invalid.\n  ' + flatten_nested_list_of_strings(warnings).replace('\n', '\n  ')
            warn(msg, BioSimulatorsWarning)
        if errors:
            msg = 'COMBINE/OMEX archive is invalid.\n  ' + flatten_nested_list_of_strings(errors).replace('\n', '\n  ')
            raise ValueError(msg)

        libcombine.writeOMEXToFile(manifest, filename)

    def _write_metadata(self, obj, archive_comb, filename):
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
        set_attributes = set()

        if obj.description:
            set_attributes.add('description')
            desc_comb.setDescription(obj.description)

        for author in obj.authors:
            set_attributes.add('authors')
            creator_comb = libcombine.VCard()
            if author.given_name:
                creator_comb.setGivenName(author.given_name)
            if author.family_name:
                creator_comb.setFamilyName(author.family_name)
            desc_comb.addCreator(creator_comb)

        if obj.created:
            set_attributes.add('created')
            date_comb = libcombine.Date()
            date_comb.setDateAsString(obj.created.strftime('%Y-%m-%dT%H:%M:%SZ'))
            desc_comb.setCreated(date_comb)

        if obj.updated:
            set_attributes.add('updated')
            date_comb = libcombine.Date()
            date_comb.setDateAsString(obj.updated.strftime('%Y-%m-%dT%H:%M:%SZ'))
            desc_comb.getModified().append(date_comb)

        if set_attributes:
            if desc_comb.isEmpty():
                msg = 'libCOMBINE requires additional metadata. Only the following attributes are set:\n  {}'.format(
                    '\n  '.join(sorted(set_attributes)))
                self.errors.append([msg])
                raise ValueError(msg)

            archive_comb.addMetadata(filename, desc_comb)


class CombineArchiveReader(object):
    """ Reader for COMBINE/OMEX archives

    Attributes:
        errors (nested :obj:`list` of :obj:`str`): errors
        warnings (nested :obj:`list` of :obj:`str`): warnings
    """

    NONE_DATETIME = '2000-01-01T00:00:00Z'

    def __init__(self):
        self.errors = []
        self.warnings = []

    def run(self, in_file, out_dir, include_omex_metadata_files=True, try_reading_as_plain_zip_archive=True):
        """ Read an archive from a file

        Args:
            in_file (:obj:`str`): path to archive
            out_dir (:obj:`str`): directory where the contents of the archive should be unpacked
            include_omex_metadata_files (:obj:`bool`, optional): whether to include the OMEX metadata
                file as part of the contents of the archive
            try_reading_as_plain_zip_archive (:obj:`bool`, optional): whether to try reading the
                file as a plain zip archive

        Returns:
            :obj:`CombineArchive`: description of archive

        Raises:
            :obj:`ValueError`: archive is invalid
        """
        self.errors = []
        self.warnings = []

        if not os.path.isfile(in_file):
            msg = "`{}` is not a file.".format(in_file)
            self.errors.append([msg])
            raise ValueError(msg)

        archive_comb = libcombine.CombineArchive()
        if archive_comb.initializeFromArchive(in_file):
            errors, warnings = get_combine_errors_warnings(archive_comb.getManifest())
            self.errors.extend(errors)
            self.warnings.extend(warnings)

        else:
            if try_reading_as_plain_zip_archive:
                try:
                    archive = CombineArchiveZipReader().run(in_file, out_dir)
                    msg = '`{}` is a plain zip archive, not a COMBINE/OMEX archive.'.format(in_file)
                    warn(msg, BioSimulatorsWarning)
                    return archive
                except ValueError:
                    msg = "`{}` is not a valid COMBINE/OMEX archive.".format(in_file)
                    self.errors.append([msg])
                    raise ValueError(msg)
            else:
                msg = "`{}` is not a valid COMBINE/OMEX archive.".format(in_file)
                self.errors.append([msg])
                raise ValueError(msg)

        # instantiate archive
        archive = CombineArchive()

        # read metadata
        self._read_metadata(archive_comb, '.', archive)

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
                master=file_comb.isSetMaster() and file_comb.getMaster(),
            )
            self._read_metadata(archive_comb, location, content)
            archive.contents.append(content)

        # extract files
        archive_comb.extractTo(out_dir)

        # read metadata files skipped by libCOMBINE
        content_locations = set(os.path.relpath(content.location, '.') for content in archive.contents)
        if include_omex_metadata_files:
            for manifest_content in self.read_manifest(os.path.join(out_dir, 'manifest.xml')):
                if (
                    manifest_content.format
                    and re.match(CombineArchiveContentFormatPattern.OMEX_METADATA.value, manifest_content.format)
                    and os.path.relpath(manifest_content.location, '.') not in content_locations
                ):
                    archive.contents.append(manifest_content)

        # raise warnings and errors
        if self.warnings:
            warn('COMBINE/OMEX archive may be invalid.\n  ' + flatten_nested_list_of_strings(self.warnings).replace('\n', '\n  '),
                 BioSimulatorsWarning)
        if self.errors:
            raise ValueError('COMBINE/OMEX archive is invalid.\n  ' + flatten_nested_list_of_strings(self.errors).replace('\n', '\n  '))

        # return information about archive
        return archive

    def read_manifest(self, filename):
        """ Read the contents of an OMEX manifest file

        Args:
            filename (:obj:`str`): path to OMEX manifest file

        Returns:
            :obj:`list` of :obj:`CombineArchiveContent`: contents of the OMEX manifest file
        """
        manifest_comb = libcombine.readOMEXFromFile(filename)
        if not isinstance(manifest_comb, libcombine.CaOmexManifest):
            self.errors(['`{}` could not be read as an OMEX manifest file.'].format(filename))
            return []

        errors, warnings = get_combine_errors_warnings(manifest_comb)
        self.errors.extend(errors)
        self.warnings.extend(warnings)
        if errors:
            return []

        contents = []
        for content_comb in manifest_comb.getListOfContents():
            content = CombineArchiveContent()

            if content_comb.isSetLocation():
                content.location = content_comb.getLocation()

            if content_comb.isSetFormat():
                content.format = content_comb.getFormat()

            if content_comb.isSetMaster():
                content.master = content_comb.getMaster()

            contents.append(content)
        return contents

    def _read_metadata(self, archive_comb, filename, obj):
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
                obj.authors.append(Person(
                    given_name=creator_comb.getGivenName() or None,
                    family_name=creator_comb.getFamilyName() or None,
                ))

            created_comb = desc_comb.getCreated().getDateAsString()
            if created_comb == self.NONE_DATETIME:
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


class CombineArchiveZipReader(object):
    """ Create a COMBINE/OMEX archive object from a plain zip archive. Set the format of files with
    the extension ``.sedml`` to :obj:`CombineArchiveContentFormat.SED_ML.value`.
    """
    @classmethod
    def run(cls, in_file, out_dir):
        """ Read an archive from a zip file

        Args:
            in_file (:obj:`str`): path to archive
            out_dir (:obj:`str`): directory where the contents of the archive should be unpacked

        Returns:
            :obj:`CombineArchive`: description of the archive

        Raises:
            :obj:`ValueError`: archive is invalid
        """
        try:
            zip_archive = ArchiveReader().run(in_file, out_dir)
        except (FileNotFoundError, zipfile.BadZipFile):
            msg = '`{}` is not a valid zip archive.'.format(in_file)
            raise ValueError(msg)

        combine_archive = CombineArchive()
        for file in zip_archive.files:
            combine_archive.contents.append(
                CombineArchiveContent(
                    location=file.archive_path,
                    format=(CombineArchiveContentFormat.SED_ML.value
                            if os.path.splitext(file.archive_path)[1] == '.sedml' else None),
                ),
            )

        return combine_archive


def get_combine_errors_warnings(manifest):
    """ Get the errors and warnings of an OMEX manifest

    Args:
        manifest (:obj:`libcombine.CaOmexManifest`): manifest

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: errors
            * nested :obj:`list` of :obj:`str`: warnings
    """
    errors = []
    warnings = []

    log = manifest.getErrorLog()
    for i_error in range(log.getNumErrors()):
        error = log.getError(i_error)
        if error.isError() or error.isFatal():
            errors.append([error.getMessage()])
        else:
            warnings.append([error.getMessage()])

    return (errors, warnings)
