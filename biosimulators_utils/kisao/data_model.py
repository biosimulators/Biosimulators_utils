""" Data model working with KiSAO terms

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-26
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

__all__ = [
    'NAMESPACE',
    'ODE_INTEGRATION_ALGORITHM_PARENT_KISAO_IDS',
]

NAMESPACE = 'http://www.biomodels.net/kisao/KISAO#'


ODE_INTEGRATION_ALGORITHM_PARENT_KISAO_IDS = set([
    'KISAO_0000094',  # Livermore solver
    'KISAO_0000281',  # multistep method
    'KISAO_0000314',  # S-system power-law canonical differential equations solver
    'KISAO_0000377',  # one-step method
    'KISAO_0000433',  # CVODE-like method'
])
