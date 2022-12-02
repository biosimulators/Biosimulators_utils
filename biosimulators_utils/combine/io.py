""" Utilities for reading and writing COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import (CombineArchiveBase, CombineArchive, CombineArchiveContent,  # noqa: F401
                         CombineArchiveContentFormat, CombineArchiveContentFormatPattern)
from ..archive.io import ArchiveReader
from ..config import get_config, Config  # noqa: F401
from ..utils.core import flatten_nested_list_of_strings
from ..warnings import warn, BioSimulatorsWarning
from zipfile import ZipFile as Zip
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

        # save archive to a file
        if not archive_comb.writeToFile(out_file):
            msg = 'Archive could not be saved.'
            self.errors.append([msg])
            raise Exception(msg)

        errors, warnings = get_combine_errors_warnings(archive_comb.getManifest())
        self.errors.extend(errors)
        self.warnings.extend(warnings)

        if self.warnings:
            warn('COMBINE/OMEX archive has warnings.\n  ' + flatten_nested_list_of_strings(self.warnings).replace('\n', '\n  '),
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
            msg = 'COMBINE/OMEX archive has warnings.\n  ' + flatten_nested_list_of_strings(warnings).replace('\n', '\n  ')
            warn(msg, BioSimulatorsWarning)
        if errors:
            msg = 'COMBINE/OMEX archive is invalid.\n  ' + flatten_nested_list_of_strings(errors).replace('\n', '\n  ')
            raise ValueError(msg)

        libcombine.writeOMEXToFile(manifest, filename)


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

    def run(self, in_file: str, out_dir: str, include_omex_metadata_files: bool = True, config: Config = None) -> CombineArchive:
        """ Read an archive from a file

        Args:
            in_file (:obj:`str`): path to archive
            out_dir (:obj:`str`): directory where the contents of the archive should be unpacked
            include_omex_metadata_files (:obj:`bool`, optional): whether to include the OMEX metadata
                file as part of the contents of the archive
            config (:obj:`Config`, optional): configuration

        Returns:
            :obj:`CombineArchive`: description of archive

        Raises:
            :obj:`ValueError`: archive is invalid
        """
        if config is None:
            config = get_config()

        self.errors = []
        self.warnings = []

        if not os.path.isfile(in_file):
            msg = "`{}` is not a file.".format(in_file)
            self.errors.append([msg])
            raise ValueError(msg)

        archive_comb = libcombine.CombineArchive()
        archive_initialized = archive_comb.initializeFromArchive(in_file)
        if archive_initialized:
            errors, warnings = get_combine_errors_warnings(archive_comb.getManifest())
            if config.VALIDATE_OMEX_MANIFESTS:
                self.errors.extend(errors)
                self.warnings.extend(warnings)

        if not archive_initialized or errors:
            if not config.VALIDATE_OMEX_MANIFESTS:
                try:
                    archive = CombineArchiveZipReader().run(in_file, out_dir)
                    msg = '`{}` is a plain zip archive, not a COMBINE/OMEX archive.'.format(in_file)
                    self.warnings.append([msg])
                    warn(msg, BioSimulatorsWarning)
                    return archive
                except ValueError:
                    msg = "`{}` is not a valid COMBINE/OMEX archive.".format(in_file)
                    self.errors.append([msg])
                    raise ValueError(msg)
            elif not self.errors:
                msg = "`{}` is not a valid COMBINE/OMEX archive.".format(in_file)
                self.errors.append([msg])
                raise ValueError(msg)

        # instantiate archive
        archive = CombineArchive()

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
            archive.contents.append(content)

        # extract files

        with Zip(in_file, 'r') as zip_archive:
            zip_archive.extractall(path=out_dir)

#        archive_comb.extractTo(out_dir) # libcombine incorrectly extracts files as directories.

        # read metadata files skipped by libCOMBINE
        content_locations = set(os.path.relpath(content.location, '.') for content in archive.contents)
        manifest_contents = self.read_manifest(os.path.join(out_dir, 'manifest.xml'), in_file, config=config)

        if include_omex_metadata_files:
            for manifest_content in manifest_contents:
                if (
                    manifest_content.format
                    and re.match(CombineArchiveContentFormatPattern.OMEX_METADATA.value, manifest_content.format)
                    and os.path.relpath(manifest_content.location, '.') not in content_locations
                ):
                    archive.contents.append(manifest_content)

        if config.VALIDATE_OMEX_MANIFESTS:
            manifest_includes_archive = False
            for manifest_content in manifest_contents:
                if os.path.relpath(manifest_content.location, '.') == '.':
                    if manifest_content.format:
                        if re.match(CombineArchiveContentFormatPattern.OMEX, manifest_content.format):
                            manifest_includes_archive = True
                        else:
                            msg = 'The format of the archive must be `{}`, not `{}`.'.format(
                                CombineArchiveContentFormat.OMEX, manifest_content.format)
                            self.errors.append([msg])

            if not manifest_includes_archive:
                msg = (
                    'The manifest does not include its parent COMBINE/OMEX archive. '
                    'Manifests should include their parent COMBINE/OMEX archives.'
                )
                self.warnings.append([msg])

        # raise warnings and errors
        if self.warnings:
            warn('COMBINE/OMEX archive has warnings.\n  ' + flatten_nested_list_of_strings(self.warnings).replace('\n', '\n  '),
                 BioSimulatorsWarning)
        if self.errors:
            raise ValueError('`{}` is not a valid COMBINE/OMEX archive.\n  {}'.format(
                in_file, flatten_nested_list_of_strings(self.errors).replace('\n', '\n  ')))

        # return information about archive
        return archive

    def read_manifest(self, filename, archive_filename=None, config=None):
        """ Read the contents of an OMEX manifest file

        Args:
            filename (:obj:`str`): path to OMEX manifest file
            archive_filename (:obj:`str`, option): path to COMBINE archive
            config (:obj:`Config`, optional): configuration

        Returns:
            :obj:`list` of :obj:`CombineArchiveContent`: contents of the OMEX manifest file
        """
        if config is None:
            config = get_config()

        manifest_comb = libcombine.readOMEXFromFile(filename)
        if not isinstance(manifest_comb, libcombine.CaOmexManifest):
            if config.VALIDATE_OMEX_MANIFESTS or archive_filename is None:
                self.errors(['`{}` could not be read as an OMEX manifest file.'].format(filename))
                return []
            else:
                try:
                    contents = CombineArchiveZipReader().run(archive_filename).contents
                    contents.append(CombineArchiveContent(location='.', format=CombineArchiveContentFormat.ZIP))
                    return contents
                except ValueError:
                    msg = "`{}` is not a valid zip file.".format(archive_filename)
                    self.errors.append([msg])
                    return []

        errors, warnings = get_combine_errors_warnings(manifest_comb)
        if config.VALIDATE_OMEX_MANIFESTS or archive_filename is None:
            self.errors.extend(errors)
            self.warnings.extend(warnings)
            if errors:
                return []
        else:
            if errors:
                try:
                    contents = CombineArchiveZipReader().run(archive_filename).contents
                    contents.append(CombineArchiveContent(location='.', format=CombineArchiveContentFormat.ZIP))
                    return contents
                except ValueError:
                    msg = "`{}` is not a valid zip file.".format(archive_filename)
                    self.errors.append([msg])
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


class CombineArchiveZipReader(object):
    """ Create a COMBINE/OMEX archive object from a plain zip archive. Set the format of files with
    the extension ``.sedml`` to :obj:`CombineArchiveContentFormat.SED_ML.value`.
    """
    @classmethod
    def run(cls, in_file, out_dir=None):
        """ Read an archive from a zip file

        Args:
            in_file (:obj:`str`): path to archive
            out_dir (:obj:`str`, optional): directory where the contents of the archive should be unpacked

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
