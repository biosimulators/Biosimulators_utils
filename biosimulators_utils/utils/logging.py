""" Utilities for logging

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import logging
import os

__all__ = ['get_logger']

FILENAME_PATTERN = '~/.biosimulators-utils/logs/{}.log'


def get_logger(name='log', filename_pattern=FILENAME_PATTERN):
    """ Get a logger

    Args:
        name (:obj:`str`, optional): name
        filename_pattern (:obj:`str`, optional): pattern for paths for log files

    Returns:
        :obj:`logging.Logger`: logger
    """
    logger = logging.getLogger('biosimulators-utils-' + name)
    if not logger.handlers:
        config_logger(logger, name, filename_pattern=filename_pattern)
    return logger


def config_logger(logger, name='log', filename_pattern=FILENAME_PATTERN):
    """ Configure a new logger

    Args:
        logger (:obj:`logging.Logger`): logger
        name (:obj:`str`, optional): name
        filename_pattern (:obj:`str`, optional): pattern for paths for log files
    """
    formatter = logging.Formatter(
        '%(levelname)s'
        '-%(asctime)s'
        '-%(pathname)s'
        '-%(funcName)s'
        '-%(lineno)d'
        ': %(message)s'
    )

    log_filename = os.path.expanduser(filename_pattern.format(name))
    log_dir = os.path.dirname(log_filename)
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    handler = logging.FileHandler(log_filename)
    handler.setFormatter(formatter)

    logger = logging.getLogger('biosimulators-utils-' + name)
    logger.addHandler(handler)

    logger.log(logging.INFO, (
        '\n'
        '\n'
        '===============\n'
        'Log initialized\n'
        '==============='
    ))
