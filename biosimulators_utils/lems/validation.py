""" Utilities for validating LEMS models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-03
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from lems.model.model import Model
import lxml.etree


def validate_model(filename, name=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []
    try:
        model = Model(include_includes=False)
        model.import_from_file(filename)

        root = lxml.etree.parse(filename).getroot()
        if root.xpath('/Lems/Include'):
            warnings.append(['Includes could not be validated.'])
    except Exception as exception:
        errors.append([str(exception)])

    return (errors, warnings)
