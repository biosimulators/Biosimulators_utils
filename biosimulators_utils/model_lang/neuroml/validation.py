""" Utilities for validating NeuroML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-10
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...log.data_model import StandardOutputErrorCapturerLevel  # noqa: E402
from ...log.utils import StandardOutputErrorCapturer  # noqa: E402
from neuroml.loaders import NeuroMLLoader
import pyneuroml.pynml


__all__ = ['validate_model', 'validate_model_l1', 'validate_model_l2']


def validate_model(filename, name=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`neuroml.nml.nml.NeuroMLDocument`: model
    """
    l1_valid, l1_output = validate_model_l1(filename)
    if l1_valid:
        return ([], [], NeuroMLLoader.load(filename))

    l2_valid, l2_output = validate_model_l2(filename)
    if l2_valid:
        return ([], [], NeuroMLLoader.load(filename))

    return ([[l2_output]], [], None)


def validate_model_l1(filename):
    """ Check that a file is a valid NeuroML L1 model

    Args:
        filename (:obj:`str`): path to model

    Returns:
        :obj:`tuple`:

            * :obj:`bool`: whether the file is valid
            * :obj:`str`: error message
    """
    with StandardOutputErrorCapturer(level=StandardOutputErrorCapturerLevel.python, relay=False) as captured:
        valid = pyneuroml.pynml.validate_neuroml1(filename)
        output = captured.get_text()
    return (valid, output)


def validate_model_l2(filename):
    """ Check that a file is a valid NeuroML L2 model

    Args:
        filename (:obj:`str`): path to model

    Returns:
        :obj:`tuple`:

            * :obj:`bool`: whether the file is valid
            * :obj:`str`: error message
    """
    with StandardOutputErrorCapturer(level=StandardOutputErrorCapturerLevel.python, relay=False) as captured:
        valid = pyneuroml.pynml.validate_neuroml2(filename)
        output = captured.get_text()
    return (valid, output)
