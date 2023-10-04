"""Methods for writing and reading simularium files within COMBINE/OMEX archives.

:Author: Alexander Patrie <apatrie@uchc.edu>
:Date: 2023-09-16
:Copyright: 2023, UConn Health
:License: MIT
"""


from typing import Optional
from biosimulators_utils.spatial.data_model import SmoldynCombineArchive, SmoldynDataConverter
from biosimulators_utils.spatial.utils import generate_model_validation_object


__all__ = [
    'generate_new_simularium_file',
]


# pragma: no cover
def generate_new_simularium_file(
        archive_rootpath: str,
        simularium_filename: Optional[str] = None,
        save_output_df: bool = False,
        __fmt: str = 'smoldyn'
        ) -> None:
    """Generate a new `.simularium` file based on the `model.txt` within the passed-archive rootpath using the above
        validation method. Raises a `ValueError` if there are errors present.

    Args:
        archive_rootpath (:obj:`str`): Parent dirpath relative to the model.txt file.
        simularium_filename (:obj:`str`): `Optional`: Desired save name for the simularium file to be saved
            in the `archive_rootpath`. Defaults to `None`.
        save_output_df (:obj:`bool`): Whether to save the modelout.txt contents as a pandas df in csv form. Defaults
            to `False`.
        __fmt (:obj:`str`): format by which to convert and save the simularium file. Currently, only 'smoldyn' is
            supported. Defaults to `smoldyn`.
    """

    # verify smoldyn combine archive
    if 'smoldyn' in __fmt.lower():
        archive = SmoldynCombineArchive(rootpath=archive_rootpath, simularium_filename=simularium_filename)

        # store and parse model data
        model_validation = generate_model_validation_object(archive)
        if model_validation.errors:
            raise ValueError(
                f'There are errors involving your model file:\n{model_validation.errors}\nPlease adjust your model file.'
            )

        # construct converter and save
        converter = SmoldynDataConverter(archive)

        if save_output_df:
            df = converter.read_model_output_dataframe()
            csv_fp = archive.model_output_filename.replace('txt', 'csv')
            df.to_csv(csv_fp)
        return converter.generate_simularium_file(simularium_filename=simularium_filename)
    else:
        raise ValueError('The only currently available format is "smoldyn".')