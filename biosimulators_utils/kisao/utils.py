""" Utilities for working with KiSAO terms

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import warn
from .warnings import InvalidKisaoTermIdWarning
import re

__all__ = [
    'normalize_kisao_id',
    'get_url_for_term',
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


def get_url_for_term(id):
    """ Get the URL for the OLS web page for a KiSAO term

    Args:
        id (:obj:`str`): id (e.g., ``KISAO_0000019`)

    Returns:
        :obj:`str`: URL for the OLS web page for a KiSAO term
    """
    return 'https://www.ebi.ac.uk/ols/ontologies/kisao/terms?iri=http%3A%2F%2Fwww.biomodels.net%2Fkisao%2FKISAO%23' + id
