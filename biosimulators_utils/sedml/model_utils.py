""" Utilities for working with models referenced by SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ModelLanguagePattern, ModelAttributeChange, Variable, Simulation  # noqa: F401
import re
import types  # noqa: F401


__all__ = ['get_parameters_variables_for_simulation']


def get_parameters_variables_for_simulation(model_filename, model_language, simulation_type, algorithm, **model_language_options):
    """ Get the possible observables for a simulation of a model

    This method supports the following formats

    * SBML
    * SBML-fbc
    * SBML-qual

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        **model_language_options: additional options to pass to the methods for individual model formats

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model

    Raises:
        :obj:`NotImplementedError`: if :obj:`model_language` is not a supported language
    """
    if re.match(ModelLanguagePattern.SBML.value, model_language):
        import biosimulators_utils.sbml.utils  # imported here to only import libraries for required model languages
        return biosimulators_utils.sbml.utils.get_parameters_variables_for_simulation(
            model_filename, model_language, simulation_type, algorithm,
            **model_language_options,
        )

    else:
        raise NotImplementedError(
            'Models of language `{}` are not supported'.format(model_language))
