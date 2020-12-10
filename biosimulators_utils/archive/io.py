""" Utilities for creating zip archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Archive, ArchiveFile
import os
import zipfile


__all__ = ['ArchiveWriter', 'ArchiveReader']


class ArchiveWriter(object):
    """ Class for writing zip archives """

    def run(self, archive, archive_filename):
        """ Bundle a list of files into a zip archive

        Args:
            archive (:obj:`Archive`): files to bundle into a zip archive
            archive_filename (:obj:`str`): path to save zip file
        """
        with zipfile.ZipFile(archive_filename, mode='w', compression=zipfile.ZIP_LZMA) as zip_file:
            for file in archive.files:
                zip_file.write(file.local_path, arcname=file.archive_path)


class ArchiveReader(object):
    """ Class for reading zip archives """

    def run(self, archive_filename, out_dir=None):
        """ Unpack the files in a zip archive

        Args:
            archive_filename (:obj:`str`): path to zip file
            out_dir (:obj:`str`, optional): path to unpack files

        Returns:
            archive (:obj:`Archive`): files unbundled from zip archive
        """
        archive = Archive()
        with zipfile.ZipFile(archive_filename, mode='r') as zip_file:
            for member in zip_file.namelist():
                archive.files.append(ArchiveFile(
                    archive_path=member,
                    local_path=os.path.join(out_dir, member) if out_dir else None,
                ))
            if out_dir:
                zip_file.extractall(out_dir)
        return archive
