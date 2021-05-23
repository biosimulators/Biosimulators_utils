""" Utilities for validating CellML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-10
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import libcellml
import os


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

    if not os.path.isfile(filename):
        errors.append(['`{}` is not a file.'.format(filename)])
        return (errors, warnings)

    # read model
    parser = libcellml.Parser()
    with open(filename, 'r') as file:
        model = parser.parseModel(file.read())

    for i_error in range(parser.errorCount()):
        error = parser.error(i_error)
        errors.append([error.description()])

    for i_warning in range(parser.warningCount()):
        warning = parser.warning(i_warning)
        warnings.append([warning.description()])

    if errors:
        return (errors, warnings)

    # validate model
    validator = libcellml.Validator()
    validator.validateModel(model)

    for i_error in range(validator.errorCount()):
        error = validator.error(i_error)
        errors.append([error.description()])

    for i_warning in range(validator.warningCount()):
        warning = validator.warning(i_warning)
        warnings.append([warning.description()])

    return (errors, warnings)
