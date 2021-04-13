""" Utilities for validating SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-13
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import libsbml


def validate_model(filename, name=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages

    Raises:
        :obj:`ValueError`: if the model is not valid
    """
    doc = libsbml.readSBMLFromFile(filename)

    errors = []
    for i_error in range(doc.getNumErrors()):
        sbml_error = doc.getError(i_error)
        if not (sbml_error.isInfo() or sbml_error.isWarning()):
            errors.append(sbml_error.getMessage())

    if errors:
        msg = 'Model `{}` could not be executed because it is not valid:\n\n  {}'.format(
            name or filename,
            '\n\n  '.join(error.replace('\n', '\n  ') for error in errors))
        raise ValueError(msg)
