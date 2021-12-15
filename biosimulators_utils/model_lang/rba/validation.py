""" Methods for validating RBA files

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config  # noqa: F401
import os
import rba
import shutil
import tempfile
import zipfile


def validate_model(filename, name=None, config=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages
        config (:obj:`Config`, optional): whether to fail on missing includes

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`rba.model.RbaModel`: RBA model
    """
    errors = []
    warnings = []
    model = None

    # check model file exists
    if not isinstance(filename, str):
        errors.append(['`{}` is not a path to an RBA file.'.format(filename)])
        return (errors, warnings, model)

    if not os.path.isfile(filename):
        errors.append(['RBA file `{}` does not exist.'.format(filename)])
        return (errors, warnings, model)

    # check file is a valid zip archive
    temp_dirname = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            zip_file.extractall(temp_dirname)
    except zipfile.BadZipFile:
        shutil.rmtree(temp_dirname)
        errors.append(['`{}` is not a valid RBA file. RBA files must be zip archives which contain TSV and XML files.'.format(filename)])
        return (errors, warnings, model)

    # check that the file contains a valid RBA model
    try:
        model = rba.RbaModel.from_xml(temp_dirname)
    except Exception as exception:
        shutil.rmtree(temp_dirname)
        errors.append(['`{}` is not a valid RBA file. RBA files must be zip archives which contain TSV and XML files.'.format(
            filename), [[str(exception)]]])
        return (errors, warnings, model)

    shutil.rmtree(temp_dirname)

    return (errors, warnings, model)
