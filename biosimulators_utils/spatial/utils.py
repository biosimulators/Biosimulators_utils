"""Utility functions related to `spatial` library.

:Author: Alexander Patrie <apatrie@uchc.edu>
:Date: 2023-09-16
:Copyright: 2023, UConn Health
:License: MIT
"""


from biosimulators_utils.model_lang.smoldyn.validation import validate_model
from biosimulators_utils.spatial.data_model import SpatialCombineArchive, ModelValidation


def generate_model_validation_object(archive: SpatialCombineArchive) -> ModelValidation:
    """ Generate an instance of `ModelValidation` based on the output of `archive.model_path`
            with above `validate_model` method.

    Args:
        archive: (:obj:`SpatialCombineArchive`): Instance of `SpatialCombineArchive` to generate model validation on.

    Returns:
        :obj:`ModelValidation`
    """
    validation_info = validate_model(archive.model_path)
    validation = ModelValidation(validation_info)
    return validation


def verify_simularium_in_archive(archive: SpatialCombineArchive) -> bool:
    return '.simularium' in list(archive.paths.keys())
