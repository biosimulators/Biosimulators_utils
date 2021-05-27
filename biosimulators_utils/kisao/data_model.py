""" Data model for working with KiSAO

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-27
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum

__all__ = [
    'TermType',
]


class TermType(str, enum.Enum):
    """ Type of a KiSAO term """
    root = 'root'
    algorithm = 'KISAO_0000000'
    algorithm_characteristic = 'KISAO_0000097'
    algorithm_parameter = 'KISAO_0000201'
