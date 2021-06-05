""" Utilities for working with KiSAO

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-27
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from kisao import Kisao
from kisao.data_model import TermType  # noqa: F401
import kisao.utils
import pronto  # noqa: F401
import re

__all__ = [
    'get_term',
    'get_term_type',
]


def get_term(id):
    """ Get a KiSAO term

    Args:
        id (:obj:`str`): id

    Returns:
        :obj:`pronto.Term`
    """
    if not id or not re.match(r'^KISAO_\d{7}$', id):
        return None
    kisao = Kisao()
    try:
        return kisao.get_term(id)
    except ValueError:
        return None


def get_term_type(term):
    """ Get the type of a KiSAO term (algorithm, algorithm characteristic, algorithm parameter)

    Args:
        term (:obj:`pronto.Term`): term

    Returns:
        :obj:`TermType`: type of the term
    """
    if term:
        return kisao.utils.get_term_type(term)

    return None
