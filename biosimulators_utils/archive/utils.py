""" Utilities for creating archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Archive, ArchiveFile
import glob
import os

__all__ = ['build_archive_from_paths']


def build_archive_from_paths(path_patterns, rel_path=None, recursive=True):
    """ Build an archive from a list of glob path patterns

    Args:
        path_patterns (:obj:`list` of :obj:`str`): glob path patterns for files to bundle into an archive
        rel_path (:obj:`str`, optional): if provided, set the archive file names to their path relative to this path
        recursive (:obj:`bool`, optional): if :obj:`True`, match the path patterns recursively

    Returns:
        :obj:`Archive`: archive
    """
    archive = Archive()
    for path_pattern in path_patterns:
        for local_path in glob.glob(path_pattern, recursive=recursive):
            if os.path.isfile(local_path):
                if rel_path:
                    archive_path = os.path.relpath(local_path, rel_path)
                else:
                    archive_path = local_path

                archive.files.append(ArchiveFile(
                    local_path=local_path,
                    archive_path=archive_path,
                ))
    return archive
