""" Utilities for validating LEMS models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-03
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from lems.model.model import Model
from pyneuroml.pynml import get_path_to_jnml_jar
import os
import shutil
import tempfile
import zipfile


def validate_model(filename, name=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`Model`: model
    """
    errors = []
    warnings = []
    model = None

    core_types_dir = tempfile.mkdtemp()
    jar_filename = get_path_to_jnml_jar()
    with zipfile.ZipFile(jar_filename, 'r') as jar_file:
        neuroml2_core_type_members = (name for name in jar_file.namelist() if name.startswith('NeuroML2CoreTypes/'))
        jar_file.extractall(core_types_dir, members=neuroml2_core_type_members)

    model = Model(include_includes=True, fail_on_missing_includes=True)
    model.add_include_directory(os.path.join(core_types_dir, 'NeuroML2CoreTypes'))
    try:
        model.import_from_file(filename)
    except Exception as exception:
        errors.append(['`{}` is not valid LEMS file.'.format(filename), [[str(exception)]]])

    shutil.rmtree(core_types_dir)

    return (errors, warnings, model)
