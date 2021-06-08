""" Utilities for validating SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-13
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import libsbml
import os


def validate_model(filename, name=None, validate_consistency=True):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages
        validate_consistency (:obj:`str`, optional): whether to check the consistency of the model

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`libsbml.SBMLDocument`: model
    """
    errors = []
    warnings = []
    doc = None

    if filename:
        if os.path.isfile(filename):
            doc = libsbml.readSBMLFromFile(filename)
            if validate_consistency:
                doc.checkConsistency()

            for i_error in range(doc.getNumErrors()):
                sbml_error = doc.getError(i_error)
                if sbml_error.isInfo() or sbml_error.isWarning():
                    warnings.append([sbml_error.getMessage()])
                else:
                    errors.append([sbml_error.getMessage()])

        else:
            errors.append(['`{}` is not a file.'.format(filename or '')])

    else:
        errors.append(['`filename` must be a path to a file, not `{}`.'.format(filename or '')])

    return (errors, warnings, doc)
