""" Utilities for validating SBML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-13
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...log.data_model import StandardOutputErrorCapturerLevel
from ...log.utils import StandardOutputErrorCapturer
import bionetgen
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

    if filename:
        if os.path.isfile(filename):
            with StandardOutputErrorCapturer(level=StandardOutputErrorCapturerLevel.c, relay=False) as captured:
                try:
                    bionetgen.bngmodel(filename)
                except Exception as exception:
                    errors.append(['`{}` is not a valid BNGL or BGNL XML file.'.format(filename or ''), [[str(exception)]]])

            stdout = captured.get_text()
            if "XML file couldn't be generated" in stdout:
                errors.append(['`{}` is not a valid BNGL or BGNL XML file.'.format(filename or ''), [[captured.get_text()]]])

        else:
            errors.append(['`{}` is not a file.'.format(filename or '')])

    else:
        errors.append(['`filename` must be a path to a file, not `{}`.'.format(filename or '')])

    return (errors, warnings)
