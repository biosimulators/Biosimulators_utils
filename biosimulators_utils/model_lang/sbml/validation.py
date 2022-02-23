""" Utilities for validating SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-13
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config  # noqa: F401
import libsbml
import os


def validate_model(filename, name=None, validate_consistency=True, config=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages
        validate_consistency (:obj:`str`, optional): whether to check the consistency of the model
        config (:obj:`Config`, optional): whether to fail on missing includes

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

            warning_map = {}
            for i_error in range(doc.getNumErrors()):
                sbml_error = doc.getError(i_error)
                if sbml_error.isInfo() or sbml_error.isWarning():
                    err_id = sbml_error.getErrorId()
                    if err_id not in warning_map:
                        warning_map[err_id] = [
                            0,
                            sbml_error.getCategoryAsString(),
                            sbml_error.getMessage().strip(),
                            sbml_error.getLine(),
                            sbml_error.getColumn(),
                            sbml_error.getSeverityAsString().lower(),
                        ]
                    warning_map[err_id][0] += 1
                else:
                    errors.append(['{} ({}) at line {}, column {}: {}'.format(
                        sbml_error.getCategoryAsString(), sbml_error.getErrorId(),
                        sbml_error.getLine(), sbml_error.getColumn(),
                        sbml_error.getMessage())
                    ])
            for err_id, (count, category, first_msg, line, column, severity) in warning_map.items():
                warnings.append([
                    '{} {}{} of type {} ({}). The following is the first {} at line {}, column {}:'.format(
                        count, severity, 's' if count > 1 else '', category, err_id, severity, line, column),
                    [[first_msg]]
                ])

        else:
            errors.append(['`{}` is not a file.'.format(filename or '')])

    else:
        errors.append(['`filename` must be a path to a file, not `{}`.'.format(filename or '')])

    return (errors, warnings, doc)
