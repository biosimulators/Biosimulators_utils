""" Utilities for working with models referenced by SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ModelLanguagePattern, Simulation  # noqa: F401
import re


__all__ = ['get_variables_for_simulation']


def get_variables_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id):
    """ Get the possible observables for a simulation of a model

    This method supports the following formts

    * SBML
    * SBML-fbc
    * SBML-qual

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)

    Returns:
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model

    Raises:
        :obj:`NotImplementedError`: if :obj:`model_language` is not a supported language
    """
    if re.match(ModelLanguagePattern.SBML.value, model_language):
        import biosimulators_utils.sbml.utils  # imported here to only import libraries for required model languages
        return biosimulators_utils.sbml.utils.get_variables_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id)

    else:
        raise NotImplementedError(
            'Models of language `{}` are not supported'.format(model_language))
