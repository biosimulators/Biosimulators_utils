""" Methods for validating COMBINE archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-16
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..omex_meta.data_model import OmexMetaInputFormat, OmexMetaSchema
from ..omex_meta.io import read_omex_meta_file
from ..sedml.io import SedmlSimulationReader
from .data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat, CombineArchiveContentFormatPattern  # noqa: F401
from .utils import get_sedml_contents
import os
import re

__all__ = [
    'validate',
    'validate_format',
    'validate_content',
    'validate_omex_meta_file',
]


def validate(archive, archive_dirname,
             include_all_sed_docs_when_no_sed_doc_is_master=True,
             always_include_all_sed_docs=False,
             validate_models_with_languages=True):
    """ Validate a COMBINE/OMEX archive and the SED-ML and model documents it contains

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dirname (:obj:`str`): directory with the content of the archive
        include_all_sed_docs_when_no_sed_doc_is_master (:obj:`bool`, optional): if :obj:`true`
            and no SED document has ``master="true"``, return all SED documents.
        always_include_all_sed_docs (:obj:`bool`, optional): if :obj:`true`,
            return all SED documents, regardless of whether they have ``master="true"`` or not.
        validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors with the archive
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the archive
    """
    errors = []
    warnings = []

    if not archive.contents:
        errors.append(['Archive must have at least one content element.'])

    # check for errors with the content elements of the archive
    for i_content, content in enumerate(archive.contents):
        content_errors = []

        if isinstance(content, CombineArchiveContent):
            if content.location:
                if not os.path.isfile(os.path.join(archive_dirname, content.location)):
                    content_errors.append(['Location is not a file.'])

            else:
                content_errors.append(['Content element must have a location (e.g., `{}`).'.format(
                    'key-experiment/simulation.sedml')])

            content_errors.extend(validate_format(content.format))

        else:
            content_errors.append(['Contents element must be an instance of `CombineArchiveContent`.'])

        if content_errors:
            content_id = '`' + content.location + '`' if getattr(content, 'location', None) else str(i_content + 1)
            errors.append(['Content element {} is invalid.'.format(content_id), content_errors])

    # check if the archive has at least one SED-ML file that should be executed
    sedml_contents = get_sedml_contents(archive,
                                        include_all_sed_docs_when_no_sed_doc_is_master=include_all_sed_docs_when_no_sed_doc_is_master,
                                        always_include_all_sed_docs=always_include_all_sed_docs)
    if not sedml_contents:
        warnings.append(['The archive does not contain any SED-ML files that should be executed.'])

    # validate files
    for content in archive.contents:
        if isinstance(content, CombineArchiveContent) and content.format:
            content_errors, content_warnings = validate_content(
                content, archive_dirname, validate_models_with_languages=validate_models_with_languages)
            errors.extend(content_errors)
            warnings.extend(content_warnings)

    # return errors and warnings
    return (errors, warnings)


def validate_format(format):
    """ Validate a COMBINE of an element of a COMBINE/OMEX archive

    Args:
        format (:obj:`str`): format

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors with the archive
    """
    errors = []

    if format:
        if not (
            re.match(r'^http://purl\.org/NET/mediatypes/[a-z0-9_\-\+\.]+/[a-z0-9_\-\+\.;]+$', format, re.IGNORECASE)
            or re.match(r'^http://identifiers\.org/combine\.specifications/\w+(\-|\.|\w)*$', format, re.IGNORECASE)
        ):
            errors.append([(
                'The format `{}` of the content element is invalid. '
                'The format must be a persistent URL for an internet media type '
                '(e.g., http://purl.org/NET/mediatypes/text/plain) or for the specifications '
                'of a COMBINE format (e.g., http://identifiers.org/combine.specifications/sbml).'
            ).format(format)])
    else:
        errors.append(['Content element must have a format (e.g., `{}`).'.format(
            CombineArchiveContentFormat.SED_ML)])

    return errors


def validate_content(content, archive_dirname, validate_models_with_languages=True):
    """ Validate an item of a COMBINE/OMEX archive

    Args:
        content (:obj:`CombineArchiveContent`): item of a COMBINE/OMEX archive
        archive_dirname (:obj:`str`): directory with the content of the archive
        validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors with the archive
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the archive
    """
    errors = []
    warnings = []
    filename = os.path.join(archive_dirname, content.location)
    file_type = None

    if re.match(CombineArchiveContentFormatPattern.SED_ML.value, content.format):
        file_type = 'SED-ML'
        reader = SedmlSimulationReader()
        try:
            reader.run(filename, validate_models_with_languages=validate_models_with_languages)
        except Exception:
            if not reader.errors:
                raise

        errors = reader.errors or []
        warnings = reader.warnings or []

    elif re.match(CombineArchiveContentFormatPattern.OMEX_METADATA.value, content.format):
        file_type = 'OMEX Meta'

        errors, warnings = validate_omex_meta_file(filename, archive_dirname)

    if errors:
        errors = [[
            'The {} file at location `{}` is invalid.'.format(file_type, content.location),
            errors,
        ]]
    if warnings:
        warnings = [[
            'The {} file at location `{}` may be invalid.'.format(file_type, content.location),
            warnings,
        ]]

    return (errors, warnings)


def validate_omex_meta_file(filename, archive_dirname, schema=OmexMetaSchema.triples, format=OmexMetaInputFormat.rdfxml):
    """ validate an OMEX Meta file

    Args:
        filename (:obj:`str`): path to file
        archive_dirname (:obj:`str`): directory with the content of the archive
        schema (:obj:`OmexMetaSchema`, optional): expected schema for OMEX Meta file
        format (:obj:`OmexMetaInputFormat`, optional): format of the file; must be one of the formats
            supported by pyomexmeta such as ``rdfxml`` or ``turtle``

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Meta file
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Meta file
    """
    _, _, errors, warnings = read_omex_meta_file(filename, schema=schema, format=format, working_dir=archive_dirname)
    return (errors, warnings)
