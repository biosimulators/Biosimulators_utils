""" Utilities for working with KiSAO

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-27
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import TermType
from kisao import Kisao
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
        kisao = Kisao()
        superclass_ids = [kisao.get_term_id(superclass) for superclass in term.superclasses()]

        for term_type in TermType.__members__.values():
            if term_type.value in superclass_ids:
                if term_type.value == kisao.get_term_id(term):
                    return TermType.root
                else:
                    return term_type

    return None
