""" Methods for generating OMEX metdata files for models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-19
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import OmexMetadataOutputFormat
import os
import pyomexmeta
import subprocess
import sys

__all__ = ['build_omex_meta_file_for_model', 'get_local_combine_archive_content_uri', 'get_global_combine_archive_content_uri']


def build_omex_meta_file_for_model(model_filename,
                                   metadata_filename,
                                   metadata_format=OmexMetadataOutputFormat.rdfxml_abbrev,
                                   encoding='utf-8', archive_uri=None):
    """ Create an OMEX metadata file for a model encoded in CellML or SBML. Also
    add missing metadata ids to the model file.

    Args:
        model_filename (:obj:`str`): path to model to extract metadata about
        metadata_filename (:obj:`str`): path to save metadata
        metadata_format (:obj:`OmexMetadataOutputFormat`, optional): format for :obj:`metadata_filename`
        encoding (:obj:`str`, optional): encoding (e.g., ``utf-8``)
    """
    # uses subprocess because pyomexmeta has insufficient error handling
    if not isinstance(model_filename, str) or not os.path.isfile(model_filename):
        raise FileNotFoundError('`{}` is not a file.'.format(model_filename))

    if not isinstance(metadata_filename, str) or not os.path.isdir(os.path.dirname(metadata_filename)):
        raise FileNotFoundError('The parent directory for `{}` does not exist.'.format(metadata_filename))

    if not isinstance(metadata_format, OmexMetadataOutputFormat):
        raise NotImplementedError('Output format `{}` is not supported.'.format(metadata_format))

    # TODO: uncomment and delete below once pyomexmeta has better error handling
    # _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format.value, encoding, archive_uri)

    if archive_uri:
        process = subprocess.run(
            [
                sys.executable, '-c',
                'from {} import {}; {}("{}", "{}", "{}", "{}", "{}")'.format(
                    _build_omex_meta_file_for_model_error_wrapper.__module__,
                    _build_omex_meta_file_for_model_error_wrapper.__name__,
                    _build_omex_meta_file_for_model_error_wrapper.__name__,
                    model_filename.replace('"', '\\"'),
                    metadata_filename.replace('"', '\\"'),
                    metadata_format.value.replace('"', '\\"'),
                    encoding.replace('"', '\\"'),
                    archive_uri.replace('"', '\\"'),
                )
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True)
        if process.returncode != 0:
            raise RuntimeError(process.stderr or 'Model `{}` could not be read'.format(model_filename))
    else:
        process = subprocess.run(
            [
                sys.executable, '-c',
                'from {} import {}; {}("{}", "{}", "{}", "{}")'.format(
                    _build_omex_meta_file_for_model_error_wrapper.__module__,
                    _build_omex_meta_file_for_model_error_wrapper.__name__,
                    _build_omex_meta_file_for_model_error_wrapper.__name__,
                    model_filename.replace('"', '\\"'),
                    metadata_filename.replace('"', '\\"'),
                    metadata_format.value.replace('"', '\\"'),
                    encoding.replace('"', '\\"'),
                )
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True)
        if process.returncode != 0:
            raise RuntimeError(process.stderr or 'Model `{}` could not be read'.format(model_filename))


def _build_omex_meta_file_for_model_error_wrapper(model_filename, metadata_filename,
                                                  metadata_format=OmexMetadataOutputFormat.rdfxml_abbrev.value,
                                                  encoding='utf-8', archive_uri=None):
    """ Wrapper for ``_build_omex_meta_file_for_model``

    Args:
        model_filename (:obj:`str`): path to model to extract metadata about
        metadata_filename (:obj:`str`): path to save metadata
        metadata_format (:obj:`str`, optional): format for :obj:`metadata_filename`
        encoding (:obj:`str`, optional): encoding (e.g., ``utf-8``)
    """
    try:
        _build_omex_meta_file_for_model(model_filename, metadata_filename, metadata_format, encoding, archive_uri)
    except (ValueError, RuntimeError) as exception:
        raise SystemExit(str(exception))


def _build_omex_meta_file_for_model(model_filename, metadata_filename,
                                    metadata_format=OmexMetadataOutputFormat.rdfxml_abbrev.value,
                                    encoding='utf-8', archive_uri=None,):
    """ Create an OMEX metadata file for a model encoded in CellML or SBML. Also
    add missing metadata ids to the model file.

    Args:
        model_filename (:obj:`str`): path to model to extract metadata about
        metadata_filename (:obj:`str`): path to save metadata
        metadata_format (:obj:`str`, optional): format for :obj:`metadata_filename`
        encoding (:obj:`str`, optional): encoding (e.g., ``utf-8``)
    """
    metadata_format = OmexMetadataOutputFormat(metadata_format)
    rdf = pyomexmeta.RDF()
    if archive_uri:
        rdf.set_archive_uri(archive_uri)
    rdf.set_model_uri(os.path.basename(model_filename))

    pyomexmeta_log_level = pyomexmeta.Logger.get_level()
    pyomexmeta.Logger.clear()
    pyomexmeta.Logger.set_level(pyomexmeta.eLogLevel.err)

    editor = rdf.to_editor(model_filename, generate_new_metaids=True, sbml_semantic_extraction=True)

    pyomexmeta.Logger.set_level(pyomexmeta_log_level)

    logger = pyomexmeta.Logger()

    errors = [logger[i_message].get_message() for i_message in range(len(logger))]
    if errors:
        raise ValueError('Metadata could not be extracted from model `{}`:\n  {}'.format(
            model_filename, '\n'.join(errors).replace('\n', '\n  ')))

    try:
        model = editor.get_xml()
    except Exception as exception:
        raise ValueError('Model `{}` could not be read'.format(model_filename)) from exception
    if not model:
        errors = [logger[i_message].get_message() for i_message in range(len(logger))]
        raise ValueError('Model `{}` could not be read:\n  {}'.format(
            model_filename, errors.replace('\n', '\n  ')))
    with open(model_filename, 'w', encoding=encoding) as file:
        file.write(model)

    if rdf.to_file(metadata_filename, metadata_format.value) != 0:
        errors = [logger[i_message].get_message() for i_message in range(len(logger))]
        raise RuntimeError('OMEX metadata could not be saved to `{}` in `{}` format:\n  {}'.format(
            metadata_filename, metadata_format.value, errors.replace('\n', '\n  ')))


def get_local_combine_archive_content_uri(content_uri, archive_uri=None):
    """ Get the relative URI for a content item of a COMBINE/OMEX archive

    Args:
        content_uri (:obj:`str`): global URI for a content item of a COMBINE/OMEX archive
        archive_uri (:obj:`str`, optional): URI for the parent COMBINE/OMEX archive

    Returns:
        :obj:`tuple:`

            * :obj:`str`: global URI for the content item
            * :obj:`str`: URI for the parent COMBINE/OMEX archive
    """
    if archive_uri:
        if content_uri in [archive_uri, archive_uri + '/']:
            return ('.', archive_uri)
        if content_uri.startswith(archive_uri + '/'):
            return ('./' + os.path.relpath(content_uri[len(archive_uri)+1:], '.'), archive_uri)
        return (content_uri, None)
    else:
        return (content_uri, archive_uri)


def get_global_combine_archive_content_uri(content_rel_uri, archive_uri=None):
    """ Get a global URI for a content item of a COMBINE/OMEX archive

    Args:
        content_rel_uri (:obj:`str`): URI for a content item of a COMBINE/OMEX archive,
            relative to its parent archive
        archive_uri (:obj:`str`, optional): URI for the parent COMBINE/OMEX archive

    Returns:
        :obj:`str`: global URI for the content item
    """
    if archive_uri:
        content_rel_uri = os.path.relpath(content_rel_uri, '.').replace("\\", "/")
        if content_rel_uri == '.':
            return archive_uri
        else:
            return archive_uri + '/' + content_rel_uri
    else:
        return content_rel_uri
