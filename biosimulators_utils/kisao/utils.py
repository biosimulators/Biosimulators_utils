""" Utilities for working with KiSAO terms

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import warn
from .core import get_child_terms, get_parent_terms, get_term_ids
from .data_model import ODE_INTEGRATION_ALGORITHM_PARENT_KISAO_IDS
from .warnings import InvalidKisaoTermIdWarning
import re

__all__ = [
    'normalize_kisao_id',
    'get_ode_integration_kisao_term_ids',
]


def normalize_kisao_id(id):
    """ Normalize an id for a KiSAO term to the official pattern ``KISAO_\\d{7}``.

    The official id pattern for KiSAO terms is ``KISAO_\\d{7}``. This is often confused with ``KISAO:\\d{7}`` and ``\\d{7}``.
    This function automatically converts these other patterns to the offfical pattern.

    Args:
        id (:obj:`str`): offical KiSAO id with pattern ``KISAO_\\d{7}`` or a variant such as ``KISAO:\\d{7}`` or ``\\d{7}``

    Returns:
        :obj:`str`: normalized KiSAO id that follows the official pattern ``KISAO_\\d{7}``
    """
    unnormalized_id = id

    id = str(id)

    if id.startswith('KISAO:'):
        id = 'KISAO_' + id[6:]

    if re.match(r'\d+', id):
        id = 'KISAO_' + '0' * (7 - len(id)) + id

    if not re.match(r'KISAO_\d{7}', id):
        warn("'{}' is likely not an id for a KiSAO term".format(unnormalized_id), InvalidKisaoTermIdWarning)

    return id


def get_ode_integration_kisao_term_ids():
    """ Get the KiSAO ids of ODE integration algorithms

    Returns:
        : obj: `list` of: obj: `str`: ids of ODE integration algorithms
    """
    ode_term_ids = set()
    for parent_id in ODE_INTEGRATION_ALGORITHM_PARENT_KISAO_IDS:
        for term in get_child_terms(parent_id):
            term_id = term.id.partition('#')[2]
            term_parent_ids = set(get_term_ids(get_parent_terms(term_id)))
            term_parent_ids.remove('KISAO_0000000')
            if not term_parent_ids.difference(ODE_INTEGRATION_ALGORITHM_PARENT_KISAO_IDS):
                ode_term_ids.add(term_id)

    return sorted(ode_term_ids)
