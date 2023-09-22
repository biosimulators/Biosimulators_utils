""" Utilities for validating Smoldyn models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-13
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""
import smoldyn

from biosimulators_utils.model_lang.smoldyn.simularium_converter import (
    CombineArchive,
    SmoldynDataConverter,
)
from biosimulators_utils.config import Config  # noqa: F401
from biosimulators_utils.log.data_model import StandardOutputErrorCapturerLevel  # noqa: E402
from biosimulators_utils.log.utils import StandardOutputErrorCapturer  # noqa: E402
from smoldyn.biosimulators.combine import (  # noqa: E402
    read_smoldyn_simulation_configuration,
    disable_smoldyn_graphics_in_simulation_configuration,
    write_smoldyn_simulation_configuration,
    init_smoldyn_simulation_from_configuration_file,
)
import pandas as pd
import os  # noqa: E402
import tempfile  # noqa: E402
from typing import Tuple, Optional, Dict, Union, List


class ModelValidation:
    def __init__(self, validation: Tuple):
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


def generate_model_validation_object(archive: CombineArchive) -> ModelValidation:
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


def generate_new_simularium_file(archive_rootpath: str, simularium_filename: str, save_output_df: bool = False) -> None:
    """Generate a new `.simularium` file based on the `model.txt` in the passed-archive rootpath using the above
        validation method. Raises an `Exception` if there are errors present.

    Args:
        archive_rootpath (:obj:`str`): Parent dirpath relative to the model.txt file.
        simularium_filename (:obj:`str`): Desired save name for the simularium file to be saved
            in the `archive_rootpath`.
        save_output_df (:obj:`bool`): Whether to save the modelout.txt contents as a pandas df in csv form. Defaults
            to `False`.

    Returns:
        None
    """
    archive = CombineArchive(rootpath=archive_rootpath, name=simularium_filename)
    model_validation = generate_model_validation_object(archive)
    if model_validation.errors:
        print(f'There are errors involving your model file:\n{model_validation.errors}\nPlease adjust your model file.')
        raise Exception
    simulation = model_validation.simulation
    print('Running simulation...')
    simulation.runSim()
    print('...Simulation complete!')

    for root, _, files in os.walk(archive.rootpath):
        for f in files:
            if f.endswith('.txt') and 'model' not in f:
                f = os.path.join(root, f)
                os.rename(f, archive.model_output_filename)

    converter = SmoldynDataConverter(archive)

    if save_output_df:
        df = converter.read_model_output_dataframe()
        csv_fp = archive.model_output_filename.replace('txt', 'csv')
        df.to_csv(csv_fp)

    return converter.generate_simularium_file()


TEST_ROOTPATH = 'minE_Andrews'
generate_new_simularium_file(archive_rootpath=TEST_ROOTPATH, simularium_filename='myTest', save_output_df=True)
