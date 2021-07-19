""" Methods for generating OMEX metdata files for models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-07-19
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import OmexMetaOutputFormat
from ..log.data_model import StandardOutputErrorCapturerLevel
from ..log.utils import StandardOutputErrorCapturer
import os
import pyomexmeta
import subprocess
import sys

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

    result = subprocess.run(
        [
            sys.executable,
            '-c',
            ';'.join([
                "from {} import _build_omex_meta_file_for_model".format(sys.modules[__name__].__name__),
                "_build_omex_meta_file_for_model('{}', '{}', '{}')".format(
                    model_filename.replace("'", "\'"),
                    metadata_filename.replace("'", "\'"),
                    metadata_format.value.replace("'", "\'"),
                )
            ])
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    if result.returncode != 0:
        msg = 'OMEX metadata file could not be generated for `{}`:\n  {}'.format(
            model_filename, result.stdout.decode(errors="ignore"))
        raise RuntimeError(msg)


def _build_omex_meta_file_for_model(model_filename,
                                    metadata_filename,
                                    metadata_format=OmexMetaOutputFormat.rdfxml_abbrev.value):
    """ Create an OMEX metadata file for a model encoded in CellML or SBML. Also
    add missing metadata ids to the model file.

    Args:
        model_filename (:obj:`str`): path to model to extract metadata about
        metadata_filename (:obj:`str`): path to save metadata
        metadata_format (:obj:`str`, optional): format for :obj:`metadata_filename`
    """
    rdf = pyomexmeta.RDF()
    with StandardOutputErrorCapturer(relay=False, level=StandardOutputErrorCapturerLevel.c) as captured:
        editor = rdf.to_editor(model_filename, generate_new_metaids=True, sbml_semantic_extraction=True)
    stdout = captured.get_text().strip()
    if stdout:
        raise RuntimeError('Model `{}` could not be read:\n  {}'.format(
            model_filename, stdout.replace('\n', '\n  ')))

    model = editor.get_xml()
    if not model:
        raise RuntimeError('Model `{}` could not be read:\n  {}'.format(
            model_filename, stdout.replace('\n', '\n  ')))
    with open(model_filename, 'w') as file:
        file.write(model)

    if rdf.to_file(metadata_filename, metadata_format) != 0:
        raise RuntimeError('OMEX metadata could not be saved to `{}` in `{}` format.'.format(
            metadata_filename, metadata_format))
