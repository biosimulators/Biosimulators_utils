""" Data model for XPP simulation methods

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-08
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

__all__ = ['SIMULATION_METHOD_KISAO_MAP']

SIMULATION_METHOD_KISAO_MAP = {
    'rungekutta': {
        'kisao_id': 'KISAO_0000032',
        'parameters': {
            'dt': 'KISAO_0000483',
        }
    },
    'discrete': {
        'kisao_id': 'KISAO_0000029',
        'parameters': {
            'seed': 'KISAO_0000488',
        }
    },
    'euler': {
        'kisao_id': 'KISAO_0000030',
        'parameters': {
            'dt': 'KISAO_0000483',
        }
    },
    'backeul': {
        'kisao_id': 'KISAO_0000031',
        'parameters': {
            'dt': 'KISAO_0000483',
        }
    },
    'adams': {
        'kisao_id': 'KISAO_0000279',
        'parameters': {
            'dt': 'KISAO_0000483',
        }
    },
    'gear': {
        'kisao_id': 'KISAO_0000288',
        'parameters': {
            'dtmin': 'KISAO_0000485',
            'dtmax': 'KISAO_0000467',
            'toler': 'KISAO_0000597',
        }
    },
    '5dp': {
        'kisao_id': 'KISAO_0000087',
        'parameters': {
            'toler': 'KISAO_0000209',
            'atoler': 'KISAO_0000211',
        }
    },
    '83dp': {
        'kisao_id': 'KISAO_0000436',
        'parameters': {
            'toler': 'KISAO_0000209',
            'atoler': 'KISAO_0000211',
        }
    },
    '2rb': {
        'kisao_id': 'KISAO_0000033',
        'parameters': {
            'toler': 'KISAO_0000209',
            'atoler': 'KISAO_0000211',
            'bandlo': 'KISAO_0000480',
            'bandup': 'KISAO_0000479',
        }
    },
    'cvode': {
        'kisao_id': 'KISAO_0000019',
        'parameters': {
            'toler': 'KISAO_0000209',
            'atoler': 'KISAO_0000211',
            'bandlo': 'KISAO_0000480',
            'bandup': 'KISAO_0000479',
        }
    },
    'qualrk': {
        'kisao_id': 'KISAO_0000672',
        'parameters': {
            'toler': 'KISAO_0000597',
            'dtmin': 'KISAO_0000485',
            'dtmax': 'KISAO_0000467',
            'newt_iter': 'KISAO_0000665',
            'newt_tol': 'KISAO_0000565',
            'jac_eps': 'KISAO_0000666',
        }
    },
    'modeuler': {
        'kisao_id': 'KISAO_0000301',
        'parameters': {
            'dt': 'KISAO_0000483',
        }
    },
    'ymp': {
        'kisao_id': 'KISAO_0000367',
        'parameters': {
            'dt': 'KISAO_0000483',
        }
    },
    'volterra': {
        'kisao_id': 'KISAO_0000664',
        'parameters': {
            'vmaxpts': 'KISAO_0000667',
            'dt': 'KISAO_0000483',
        }
    },
    'stiff': {
        'kisao_id': 'KISAO_0000668',
        'parameters': {
            'dtmin': 'KISAO_0000485',
            'dtmax': 'KISAO_0000467',
            'toler': 'KISAO_0000597',
        }
    }
}
