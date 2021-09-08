""" Methods for generating OMEX metdata files for models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-19
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import OmexMetaOutputFormat
import os
import pyomexmeta

__all__ = ['build_omex_meta_file_for_model']


def build_omex_meta_file_for_model(model_filename,
                                   metadata_filename,
                                   metadata_format=OmexMetaOutputFormat.rdfxml_abbrev):
    """ Create an OMEX metadata file for a model encoded in CellML or SBML. Also
    add missing metadata ids to the model file.

    Args:
        model_filename (:obj:`str`): path to model to extract metadata about
        metadata_filename (:obj:`str`): path to save metadata
        metadata_format (:obj:`OmexMetaOutputFormat`, optional): format for :obj:`metadata_filename`
    """
    # uses subprocess by pyomexmetadata has no error handling
    if not isinstance(model_filename, str) or not os.path.isfile(model_filename):
        raise FileNotFoundError('`{}` is not a file.'.format(model_filename))

    if not isinstance(metadata_filename, str) or not os.path.isdir(os.path.dirname(metadata_filename)):
        raise FileNotFoundError('The parent directory for `{}` does not exist.'.format(metadata_filename))

    if not isinstance(metadata_format, OmexMetaOutputFormat):
        raise NotImplementedError('Output format `{}` is not supported.'.format(metadata_format))

    rdf = pyomexmeta.RDF()

    pyomexmeta_log_level = pyomexmeta.Logger.get_level()
    pyomexmeta.Logger.clear()
    pyomexmeta.Logger.set_level(pyomexmeta.eLogLevel.err)

    editor = rdf.to_editor(model_filename, generate_new_metaids=True, sbml_semantic_extraction=True)

    pyomexmeta.Logger.set_level(pyomexmeta_log_level)

    logger = pyomexmeta.Logger()

    errors = ''.join([logger[i_message].get_message() for i_message in range(len(logger))])
    if errors:
        raise ValueError('Metadata could not be extracted from model `{}`:\n  {}'.format(
            model_filename, '\n'.join(errors).replace('\n', '\n  ')))

    model = editor.get_xml()
    if not model:
        errors = ''.join([logger[i_message].get_message() for i_message in range(len(logger))])
        raise RuntimeError('Model `{}` could not be read:\n  {}'.format(
            model_filename, errors.replace('\n', '\n  ')))
    with open(model_filename, 'w') as file:
        file.write(model)

    if rdf.to_file(metadata_filename, metadata_format.value) != 0:
        errors = ''.join([logger[i_message].get_message() for i_message in range(len(logger))])
        raise RuntimeError('OMEX metadata could not be saved to `{}` in `{}` format:\n  {}'.format(
            metadata_filename, metadata_format.value, errors.replace('\n', '\n  ')))
