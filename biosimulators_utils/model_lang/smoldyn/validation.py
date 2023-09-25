""" Utilities for validating Smoldyn models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-13
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import smoldyn  # noqa: F401
from biosimulators_utils.model_lang.smoldyn.simularium_converter import SmoldynCombineArchive
from biosimulators_utils.config import Config  # noqa: F401
from biosimulators_utils.log.data_model import StandardOutputErrorCapturerLevel  # noqa: E402
from biosimulators_utils.log.utils import StandardOutputErrorCapturer  # noqa: E402
from smoldyn.biosimulators.combine import (  # noqa: E402
    read_smoldyn_simulation_configuration,
    disable_smoldyn_graphics_in_simulation_configuration,
    write_smoldyn_simulation_configuration,
    init_smoldyn_simulation_from_configuration_file,
)
import os  # noqa: E402
import tempfile  # noqa: E402
from typing import Tuple, List


class ModelValidation:
    def __init__(self, validation: Tuple[List[str], List[str], Tuple[smoldyn.Simulation, List[str]]]):
        self.errors = validation[0]
        self.warnings = validation[1]
        self.simulation = validation[2][0]
        self.config = validation[2][1]


def validate_model(filename, name=None, config=None):
    """ Check that a model is valid

    Args:
        filename (:obj:`str`): path to model
        name (:obj:`str`, optional): name of model for use in error messages
        config (:obj:`Config`, optional): whether to fail on missing includes

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * :obj:`tuple`:

                * :obj:`smoldyn.Simulation`: model configuration
                * :obj:`list` of :obj:`str`: model configuration
    """
    errors = []
    warnings = []
    model = None
    config = None

    if filename:
        if os.path.isfile(filename):
            config = read_smoldyn_simulation_configuration(filename)
            disable_smoldyn_graphics_in_simulation_configuration(config)
            fid, config_filename = tempfile.mkstemp(suffix='.txt', dir=os.path.dirname(filename))
            os.close(fid)
            write_smoldyn_simulation_configuration(config, config_filename)
            with StandardOutputErrorCapturer(level=StandardOutputErrorCapturerLevel.c, relay=False) as captured:
                try:
                    model = init_smoldyn_simulation_from_configuration_file(config_filename)
                    valid = True
                except ValueError:
                    valid = False
            if not valid:
                errors.append(['`{}` is not a valid Smoldyn configuration file.'.format(filename), [[captured.get_text()]]])
            os.remove(config_filename)

        else:
            errors.append(['`{}` is not a file.'.format(filename or '')])

    else:
        errors.append(['`filename` must be a path to a file, not `{}`.'.format(filename or '')])

    return (errors, warnings, (model, config))


def generate_model_validation_object(archive: SmoldynCombineArchive) -> ModelValidation:
    """Generate an instance of `ModelValidation` based on the output of `archive.model_path`
        with above `validate_model` method.

    Args:
        archive: (:obj:`CombineArchive`): Instance of `CombineArchive` to generate model validation on.

    Returns:
        :obj:`ModelValidation`
    """
    validation_info = validate_model(archive.model_path)
    validation = ModelValidation(validation_info)
    return validation
