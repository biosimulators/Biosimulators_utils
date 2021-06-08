""" Utilities for validating NeuroML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-10
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from neuroml.loaders import NeuroMLLoader
import warnings


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
    with warnings.catch_warnings(record=True) as caught_warnings:
        try:
            model = NeuroMLLoader.load(filename)
            error_messages = []
        except Exception as exception:
            model = None
            error_messages = [[str(exception)]]

        warning_messages = [['{}: {}'.format(caught_warning.category, caught_warning.message)] for caught_warning in caught_warnings]

    return (error_messages, warning_messages, model)
