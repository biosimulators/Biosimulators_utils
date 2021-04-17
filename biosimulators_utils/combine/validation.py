""" Methods for validating COMBINE archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-16
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.io import SedmlSimulationReader
from .data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat, CombineArchiveContentFormatPattern  # noqa: F401
from .utils import get_sedml_contents
import os


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

            if not content.format:
                content_errors.append(['Content element must have a format (e.g., `{}`).'.format(
                    CombineArchiveContentFormat.SED_ML)])

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

    # validate SED-ML files
    for doc_contents in sedml_contents:
        doc_filename = os.path.join(archive_dirname, doc_contents.location)
        reader = SedmlSimulationReader()
        try:
            reader.run(doc_filename, validate_models_with_languages=validate_models_with_languages)
        except Exception:
            if not reader.errors:
                raise

        if reader.errors:
            errors.append([
                'The SED-ML file at location `{}` is invalid.'.format(doc_contents.location),
                reader.errors,
            ])
        if reader.warnings:
            warnings.append([
                'The SED-ML file at location `{}` may be invalid.'.format(doc_contents.location),
                reader.warnings,
            ])

    # return errors and warnings
    return (errors, warnings)
