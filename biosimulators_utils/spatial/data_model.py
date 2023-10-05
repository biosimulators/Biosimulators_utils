"""
:Author: Alexander Patrie <apatrie@uchc.edu>
:Date: 2023-09-16
:Copyright: 2023, UConn Health
:License: MIT


Using the Biosimulators side of Smoldyn to generate a modelout.txt Smoldyn file for a specified OMEX/COMBINE archive
which then is used to generate a .simularium file for the given simulation. That .simularium file is then stored along
with the log.yml and report.{FORMAT} relative to the simulation. Remember: each simulation, while not inherently
published, has the potential for publication based purely on the simulation's ability to provide a valid OMEX/COMBINE
archive. There exists (or should exist) an additional layer of abstraction to then validate and
verify the contents therein.
"""


# pragma: no cover
import os
from dataclasses import dataclass
from warnings import warn
from typing import Optional, Tuple, Dict, List, Union
from abc import ABC, abstractmethod
# noinspection PyPackageRequirements
from smoldyn import Simulation as smoldynSim
import numpy as np
import pandas as pd
from simulariumio import (
    CameraData,
    UnitData,
    MetaData,
    DisplayData,
    BinaryWriter,
    JsonWriter,
    TrajectoryConverter,
    TrajectoryData,
    AgentData
)
from simulariumio.smoldyn.smoldyn_data import InputFileData
from simulariumio.smoldyn import SmoldynConverter, SmoldynData
from simulariumio.filters import TranslateFilter
from biosimulators_utils.combine.data_model import CombineArchiveContent
from biosimulators_utils.combine.io import CombineArchiveReader, CombineArchiveWriter
from biosimulators_utils.archive.io import ArchiveReader, ArchiveWriter
from biosimulators_utils.model_lang.smoldyn.validation import validate_model


__all__ = [
    'ModelValidation',
    'SpatialCombineArchive',
    'SmoldynCombineArchive',
    'BiosimulatorsDataConverter',
    'SmoldynDataConverter',
]


"""*Validation/Simulation*"""


@dataclass
class ModelValidation:
    errors: List[List[str]]
    warnings: List[str]
    simulation: smoldynSim
    config: List[str]

    def __init__(self, validation: Tuple[List[List[str]], List, Tuple[smoldynSim, List[str]]]):
        self.errors = validation[0]
        self.warnings = validation[1]
        self.simulation = validation[2][0]
        self.config = validation[2][1]


"""*Spatial Combine Archives*"""


# TODO: Add more robust rezipping
class SpatialCombineArchive(ABC):
    __zipped_file_format: str
    was_unzipped: bool
    paths: Dict[str, str]

    def __init__(self,
                 rootpath: str,
                 simularium_filename=None):
        """ABC Object for storing and setting/getting files pertaining to simularium file conversion.

            Args:
                rootpath: root of the unzipped archive. Consider this your working dirpath.
                simularium_filename:`Optional`: full path which to assign to the newly generated simularium file.
                If using this value, it EXPECTS a full path. Defaults to `{name}_output_for_simularium`.
                name: Commonplace name for the archive to be used if no `simularium_filename` is passed. Defaults to
                    `new_spatial_archive`.
        """
        super().__init__()
        self.rootpath = rootpath
        if not simularium_filename:
            simularium_filename = 'spatial_combine_archive'
            self.simularium_filename = os.path.join(self.rootpath, simularium_filename)
        self.__parse_rootpath()
        self.paths = self.get_all_archive_filepaths()

    @property
    def __zipped_file_format(self) -> str:
        return '.omex'

    def __parse_rootpath(self):
        """Private method for parsing whether `self.rootpath` is the path to a directory or single OMEX/COMBINE
            zipped file. If .omex, then decompress the input path into an unzipped directory for working and sets
            `self.was_unzipped` to `True` and `False` if not.
        """
        if self.rootpath.endswith(self.__zipped_file_format):
            self.unzip()
            self.was_unzipped = True
        else:
            self.was_unzipped = False

    def unzip(self, unzipped_output_location: str = None):
        reader = ArchiveReader()
        try:
            if not unzipped_output_location:
                unzipped_output_location = self.rootpath.replace(
                    self.__zipped_file_format,
                    '_UNZIPPED'
                )  # TODO: make tempdir here instead
            reader.run(self.rootpath, unzipped_output_location)
            print('Omex successfully unzipped!...')
            self.rootpath = unzipped_output_location
        except Exception as e:
            warn(f'Omex could not be unzipped because: {e}')

    def rezip(self, paths_to_write: Optional[List[str]] = None, destination: Optional[str] = None):
        if self.__zipped_file_format in self.rootpath:
            writer = ArchiveWriter()
            if not paths_to_write:
                paths_to_write = list(self.get_all_archive_filepaths().values())
                print(f'HERE THEY ARE: {paths_to_write}')
            if not destination:
                destination = self.rootpath
            writer.run(archive=paths_to_write, archive_filename=destination)
            print(f'Omex successfully bundled with the following paths: {paths_to_write}!')

    def get_all_archive_filepaths(self) -> Dict[str, str]:
        """Recursively read the contents of the directory found at `self.rootpath` and set their full paths.

            Returns:
                `Dict[str, str]`: Dict of form {'path_root': full_path}
        """
        paths = {}
        if os.path.exists(self.rootpath):
            for root, _, files in os.walk(self.rootpath):
                paths['root'] = root
                for f in files:
                    fp = os.path.join(root, f)
                    paths[f] = fp
        return paths

    def get_manifest_filepath(self) -> Union[List[str], str]:
        """Read SmoldynCombineArchive manifest files. Return all filepaths containing the word 'manifest'.

            Returns:
                :obj:`str`: path if there is just one manifest file, otherwise `List[str]` of manifest filepaths.
        """
        manifest = []
        for v in list(self.paths.values()):
            if 'manifest' in v:
                manifest.append(v)
                self.paths['manifest'] = v
        return list(set(manifest))[0]

    def read_manifest_contents(self):
        """Reads the contents of the manifest file within `self.rootpath`.
            Read the return value of `self.get_manifest_filepath()` as the input for `CombineArchiveReader.run().
        """
        manifest_fp = self.get_manifest_filepath()
        reader = CombineArchiveReader()
        return reader.read_manifest(filename=manifest_fp)

    @staticmethod
    def generate_new_archive_content(fp: str) -> CombineArchiveContent:
        """Factory for generating a new instance of `CombineArchiveContent` using just fp.

            Args:
                fp: filepath of the content you wish to add to the combine archive.

            Returns:
                `CombineArchiveContent` based on the passed `fp`.
        """
        return CombineArchiveContent(fp)

    def add_file_to_manifest(self, contents_fp: str) -> None:
        contents = self.read_manifest_contents()
        new_content = self.generate_new_archive_content(contents_fp)
        contents.append(new_content)
        writer = CombineArchiveWriter()
        try:
            manifest_fp = self.get_manifest_filepath()
            writer.write_manifest(contents=contents, filename=manifest_fp)
            print('File added to archive manifest contents!')
        except Exception as e:
            print(e)
            warn(f'The simularium file found at {contents_fp} could not be added to manifest.')
            return

    def add_modelout_file_to_manifest(self, model_fp) -> None:
        return self.add_file_to_manifest(model_fp)

    def add_simularium_file_to_manifest(self, simularium_fp: Optional[str] = None) -> None:
        """Read the contents of the manifest file found at `self.rootpath`, create a new instance of
            `CombineArchiveContent` using a set simularium_fp, append the new content to the original,
            and re-write the archive to reflect the newly added content.

            Args:
                  simularium_fp:`Optional`: path to the newly generated simularium file. Defaults
                    to `self.simularium_filename`.
        """
        try:
            if not simularium_fp:
                simularium_fp = self.simularium_filename
            self.add_file_to_manifest(simularium_fp)
            print('Simularium File added to archive manifest contents!')
        except Exception:
            raise IOError(f'The simularium file found at {simularium_fp} could not be added to manifest.')

    def verify_smoldyn_in_manifest(self) -> bool:
        """Pass the return value of `self.get_manifest_filepath()` into a new instance of `CombineArchiveReader`
            such that the string manifest object tuples are evaluated for the presence of `smoldyn`.

            Returns:
                `bool`: Whether there exists a smoldyn model in the archive based on the archive's manifest.
        """
        manifest_contents = [c.to_tuple() for c in self.read_manifest_contents()]
        model_info = manifest_contents[0][1]
        return 'smoldyn' in model_info

    @abstractmethod
    def set_model_filepath(self,
                           model_default: str,
                           model_filename: Optional[str] = None) -> Union[str, None]:
        """Recurse `self.rootpath` and search for your simulator's model file extension."""
        pass

    @abstractmethod
    def set_model_output_filepath(self) -> None:
        """Recursively read the directory at `self.rootpath` and standardize the model output filename to become
                    `self.model_output_filename`.
        """
        pass

    @abstractmethod
    def generate_model_validation_object(self) -> ModelValidation:
        """Generate an instance of `ModelValidation` based on the output of `self.model_path`
                    with your simulator's primary validation method.

                Returns:
                    :obj:`ModelValidation`
        """
        pass


class SmoldynCombineArchive(SpatialCombineArchive):
    def __init__(self,
                 rootpath: str,
                 model_output_filename='modelout.txt',
                 simularium_filename='smoldyn_combine_archive'):
        """Object for handling the output of Smoldyn simulation data. Implementation child of `SpatialCombineArchive`.

            Args:
                rootpath: fp to the root of the archive 'working dir'.
                model_output_filename: filename ONLY not filepath of the model file you are working with. Defaults to
                    `modelout.txt`.
                simularium_filename:
        """
        super().__init__(rootpath, simularium_filename)
        self.set_model_filepath()
        self.model_output_filename = os.path.join(self.rootpath, model_output_filename)
        self.paths['model_output_file'] = self.model_output_filename

    def set_model_filepath(self, model_default='model.txt', model_filename: Optional[str] = None):
        """Recursively read the full paths of all files in `self.paths` and return the full path of the file
            containing the term 'model.txt', which is the naming convention.
            Implementation of ancestral abstract method.

            Args:
                model_filename: `Optional[str]`: index by which to label a file in directory as the model file.
                    Defaults to `model_default`.
                model_default: `str`: default model filename naming convention. Defaults to `'model.txt'`
        """
        if not model_filename:
            model_filename = os.path.join(self.rootpath, model_default)  # default Smoldyn model name
        for k in self.paths.keys():
            full_path = self.paths[k]
            if model_filename in full_path:
                # noinspection PyAttributeOutsideInit
                self.model_path = model_filename

    def set_model_output_filepath(self) -> None:
        """Recursively search the directory at `self.rootpath` for a smoldyn
            modelout file (`.txt`) and standardize the model output filename to become
            `self.model_output_filename`. Implementation of ancestral abstract method.
        """
        for root, _, files in os.walk(self.rootpath):
            for f in files:
                if f.endswith('.txt') and 'model' not in f and os.path.exists(f):
                    f = os.path.join(root, f)
                    os.rename(f, self.model_output_filename)

    def generate_model_validation_object(self) -> ModelValidation:
        """Generate an instance of `ModelValidation` based on the output of `self.model_path`
            with `biosimulators-utils.model_lang.smoldyn.validate_model` method.
            Implementation of ancestral abstract method.

        Returns:
            :obj:`ModelValidation`
        """
        validation_info = validate_model(self.model_path)
        validation = ModelValidation(validation_info)
        return validation


"""*Converters*"""


class BiosimulatorsDataConverter(ABC):
    has_smoldyn: bool

    def __init__(self, archive: SpatialCombineArchive):
        """This class serves as the abstract interface for a simulator-specific implementation
            of utilities through which the user may convert Biosimulators outputs to a valid simularium File.

                Args:
                    :obj:`archive`:(`SpatialCombineArchive`): instance of an archive to base conv and save on.
        """
        self.archive = archive
        self.has_smoldyn = self.archive.verify_smoldyn_in_manifest()

    # Factory Methods
    @abstractmethod
    def generate_output_data_object(
            self,
            file_data: InputFileData,
            display_data: Optional[Dict[str, DisplayData]] = None,
            spatial_units="nm",
            temporal_units="ns",
            ):
        """Factory to generate a data object to fit the simulariumio.TrajectoryData interface.
        """
        pass

    @abstractmethod
    def translate_data_object(self,
                              data_object_converter: TrajectoryConverter,
                              box_size: Union[float, int],
                              n_dim: str = 3) -> TrajectoryData:
        """Factory to create a mirrored negative image of a distribution and apply it to 3dimensions if
            AND ONLY IF it contains all non-negative values.
        """
        pass

    @abstractmethod
    def generate_simularium_file(
            self,
            simularium_filename: str,
            box_size: float,
            translate: bool,
            spatial_units="nm",
            temporal_units="ns",
            n_dim=3,
            display_data: Optional[Dict[str, DisplayData]] = None,
            ) -> None:
        """Factory for a taking in new data_object, optionally translate it, convert to simularium, and save.
        """
        pass

    @abstractmethod
    def generate_converter(self, data: TrajectoryData):
        """Factory for creating a new instance of a translator/filter converter based on the Simulator,
            whose output you are attempting to visualize.
        """
        pass

    @staticmethod
    def generate_agent_data_object(
            timestep: int,
            total_steps: int,
            n_agents: int,
            box_size: float,
            min_radius: int,
            max_radius: int,
            display_data_dict: Dict[str, DisplayData],
            type_names: List[List[str]],
            positions=None,
            radii=None,
            ) -> AgentData:
        """Factory for a new instance of an `AgentData` object following the specifications of the simulation within the
            relative combine archive.

            Returns:
                `AgentData` instance.
        """
        positions = positions or np.random.uniform(size=(total_steps, n_agents, 3)) * box_size - box_size * 0.5
        radii = radii or (max_radius - min_radius) * np.random.uniform(size=(total_steps, n_agents)) + min_radius
        return AgentData(
            times=timestep * np.array(list(range(total_steps))),
            n_agents=np.array(total_steps * [n_agents]),
            viz_types=np.array(total_steps * [n_agents * [1000.0]]),  # default viz type = 1000
            unique_ids=np.array(total_steps * [list(range(n_agents))]),
            types=type_names,
            positions=positions,
            radii=radii,
            display_data=display_data_dict
        )

    @staticmethod
    def prepare_simularium_fp(**simularium_config) -> str:
        """Generate a simularium dir and joined path if not using the init object.

            Kwargs:
                (obj):`**simularium_config`: keys are 'simularium_dirpath' and 'simularium_fname'

            Returns:
                (obj):`str`: complete simularium filepath
        """
        dirpath = simularium_config.get('simularium_dirpath')
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        return os.path.join(dirpath, simularium_config.get('simularium_fname'))

    @staticmethod
    def generate_metadata_object(box_size: np.ndarray[int], camera_data: CameraData) -> MetaData:
        """Factory for a new instance of `simulariumio.MetaData` based on the input params of this method.
            Currently, `ModelMetaData` is not supported as a param.

            Args:
                box_size: ndarray containing the XYZ dims of the simulation bounding volume. Defaults to [100,100,100].
                camera_data: new `CameraData` instance to control visuals.

            Returns:
                `MetaData` instance.
        """
        return MetaData(box_size=box_size, camera_defaults=camera_data)

    @staticmethod
    def generate_camera_data_object(
            position: np.ndarray,
            look_position: np.ndarray,
            up_vector: np.ndarray
            ) -> CameraData:
        """Factory for a new instance of `simulariumio.CameraData` based on the input params.
            Wraps the simulariumio object.

            Args:
                position: 3D position of the camera itself Default: np.array([0.0, 0.0, 120.0]).
                look_position: np.ndarray (shape = [3]) position the camera looks at Default: np.zeros(3).
                up_vector: np.ndarray (shape = [3]) the vector that defines which direction is “up” in the
                    camera’s view Default: np.array([0.0, 1.0, 0.0])

            Returns:
                `CameraData` instance.
        """
        return CameraData(position=position, look_at_position=look_position, up_vector=up_vector)

    @staticmethod
    def generate_display_data_object(
            name: str,
            radius: float,
            display_type=None,
            obj_color: Optional[str] = None,
    ) -> DisplayData:
        """Factory for creating a new instance of `simularimio.DisplayData` based on the params.

            Args:
                name: name of agent
                radius: `float`
                display_type: any one of the `simulariumio.DISPLAY_TYPE` properties. Defaults to None.
                obj_color: `str`: hex color of the display agent.

            Returns:
                `DisplayData` instance.
        """
        return DisplayData(
            name=name,
            radius=radius,
            display_type=display_type,
            color=obj_color
        )

    @staticmethod
    def generate_display_data_object_dict(agent_displays: List) -> Dict[str, DisplayData]:
        """Factory to generate a display object dict.

            Args:
                agent_displays: `List[AgentDisplayData]`: A list of `AgentDisplayData` instances which describe the
                    visualized agents.

            Returns:
                `Dict[str, DisplayData]`
        """
        displays = {}
        for agent_display in agent_displays:
            key = agent_display.name
            display = DisplayData(
                name=agent_display.name,
                radius=agent_display.radius,
                display_type=agent_display.display_type,
                url=agent_display.url,
                color=agent_display.color
            )
            displays[key] = display
        return displays

    def generate_input_file_data_object(self, model_output_file: Optional[str] = None) -> InputFileData:
        """Factory that generates a new instance of `simulariumio.data_model.InputFileData` based on
            `self.archive.model_output_filename` (which itself is derived from the model file) if no `model_output_file`
            is passed.

            Args:
                  model_output_file(:obj:`str`): `Optional`: file on which to base the `InputFileData` instance.
            Returns:
                  (:obj:`InputFileData`): simulariumio input file data object based on `self.archive.model_output_filename`

        """
        model_output_file = model_output_file or self.archive.model_output_filename
        return InputFileData(model_output_file)

    # IO Methods
    @staticmethod
    def write_simularium_file(
            data: Union[SmoldynData, TrajectoryData],
            simularium_filename: str,
            save_format: str,
            validation=True
            ) -> None:
        """Takes in either a `SmoldynData` or `TrajectoryData` instance and saves a simularium file based on it
            with the name of `simularium_filename`. If none is passed, the file will be saved in `self.archive.rootpath`

            Args:
                data(:obj:`Union[SmoldynData, TrajectoryData]`): data object to save.
                simularium_filename(:obj:`str`): `Optional`: name by which to save the new simularium file. If None is
                    passed, will default to `self.archive.rootpath/self.archive.simularium_filename`.
                save_format(:obj:`str`): format which to write the `data`. Options include `json, binary`.
                validation(:obj:`bool`): whether to call the wrapped method using `validate_ids=True`. Defaults
                    to `True`.
        """
        save_format = save_format.lower()
        if not os.path.exists(simularium_filename):
            if 'binary' in save_format:
                writer = BinaryWriter()
            elif 'json' in save_format:
                writer = JsonWriter()
            else:
                warn('You must provide a valid writer object.')
                return
            return writer.save(trajectory_data=data, output_path=simularium_filename, validate_ids=validation)

    def simularium_to_json(self, data: Union[SmoldynData, TrajectoryData], simularium_filename: str, v=True) -> None:
        """Write the contents of the simularium stream to a JSON Simularium file.

            Args:
                data: data to write.
                simularium_filename: filepath at which to write the new simularium file.
                v: whether to call the wrapped method with validate_ids=True. Defaults to `True`.
        """
        return self.write_simularium_file(
            data=data,
            simularium_filename=simularium_filename,
            save_format='json',
            validation=v
        )

    def simularium_to_binary(self, data: Union[SmoldynData, TrajectoryData], simularium_filename: str, v=True) -> None:
        """Write the contents of the simularium stream to a Binary Simularium file.

            Args:
                data: data to write.
                simularium_filename: filepath at which to write the new simularium file.
                v: whether to call the wrapped method with validate_ids=True. Defaults to `True`.
        """
        return self.write_simularium_file(
            data=data,
            simularium_filename=simularium_filename,
            save_format='binary',
            validation=v
        )


class SmoldynDataConverter(BiosimulatorsDataConverter):
    def __init__(self, archive: SmoldynCombineArchive, generate_model_output: bool = True):
        """General class for converting Smoldyn output (modelout.txt) to .simularium. Checks the passed archive object
            directory for a `modelout.txt` file (standard Smoldyn naming convention) and runs the simulation by default if
            not. At the time of construction, checks for the existence of a simulation `out.txt` file and runs
            `self.generate_model_output_file()` if such a file does not exist, based on `self.archive`. To turn
            this off, pass `generate_data` as `False`.

            Args:
                archive (:obj:`SmoldynCombineArchive`): instance of a `SmoldynCombineArchive` object.
                generate_model_output(`bool`): Automatically generates and standardizes the name of a
                    smoldyn model output file based on the `self.archive` parameter if True. Defaults to `True`.
        """
        super().__init__(archive)
        if generate_model_output:
            self.generate_model_output_file()

    def generate_model_output_file(self,
                                   model_output_filename: Optional[str] = None,
                                   smoldyn_archive: Optional[SmoldynCombineArchive] = None) -> None:
        """Generate a modelout file if one does not exist using the `ModelValidation` interface via
            `.utils.generate_model_validation_object` method. If either parameter is not passed, the data will
            be derived from `self.archive(:obj:`SmoldynCombineArchive`)`.

            Args:
                model_output_filename(:obj:`str`): `Optional`: filename from which to run a smoldyn simulation
                    and generate an out.txt file. Defaults to `self.archive.model_output_filename`.
                smoldyn_archive(:obj:`SmoldynCombineArchive`): `Optional`: instance of `SmoldynCombineArchive` from
                    which to base the simulation/model.txt from. Defaults to `self.archive`.

            Returns:
                None
        """
        model_output_filename = model_output_filename or self.archive.model_output_filename
        archive = smoldyn_archive or self.archive
        if not os.path.exists(model_output_filename):
            validation = archive.generate_model_validation_object()
            validation.simulation.runSim()

        # standardize the modelout filename
        for root, _, files in os.walk(archive.rootpath):
            for f in files:
                if f.endswith('.txt') and 'model' not in f:
                    f = os.path.join(root, f)
                    os.rename(f, archive.model_output_filename)

    def read_model_output_dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe from the contents of `self.archive.model_output_filename`. WARNING: this method
            is currently experimental.

            Returns:
                `pd.DataFrame`: a pandas dataframe with the columns: ['mol_name', 'x', 'y', 'z', 't']
        """
        warn('WARNING: This method is experimental and may not function properly.')
        colnames = ['mol_name', 'x', 'y', 'z', 't']
        return pd.read_csv(self.archive.model_output_filename, sep=" ", header=None, skiprows=1, names=colnames)

    def write_model_output_dataframe_to_csv(self, save_fp: str) -> None:
        """Write output dataframe to csv file.

            Args:
                save_fp:`str`: path at which to save the csv-converted pandas df.
        """
        df = self.read_model_output_dataframe()
        return df.to_csv(save_fp)

    def generate_output_data_object(
            self,
            file_data: InputFileData,
            display_data: Optional[Dict[str, DisplayData]] = None,
            meta_data: Optional[MetaData] = None,
            spatial_units="nm",
            temporal_units="ns",
            ) -> SmoldynData:
        """Generate a new instance of `SmoldynData`. If passing `meta_data`, please create a new `MetaData` instance
            using the `self.generate_metadata_object` interface of this same class.

        Args:
            file_data: (:obj:`InputFileData`): `simulariumio.InputFileData` instance based on model output.
            display_data: (:obj:`Dict[Dict[str, DisplayData]]`): `Optional`: if passing this parameter, please
                use the `self.generate_display_object_dict` interface of this same class.
            meta_data: (:obj:`Metadata`): new instance of `Metadata` object. If passing this parameter, please use the
                `self.generate_metadata_object` interface method of this same class.
            spatial_units: (:obj:`str`): spatial units by which to measure this simularium output. Defaults to `nm`.
            temporal_units: (:obj:`str`): time units to base this simularium instance on. Defaults to `ns`.

        Returns:
            :obj:`SmoldynData`
        """
        return SmoldynData(
            smoldyn_file=file_data,
            spatial_units=UnitData(spatial_units),
            time_units=UnitData(temporal_units),
            display_data=display_data,
            meta_data=meta_data
        )

    def generate_converter(self, data: SmoldynData) -> SmoldynConverter:
        """Implementation of parent-level factory which exposes an object for translating `SmoldynData` instance.

            Args:
                data(`SmoldynData`): Data to be translated.

            Returns:
                `SmoldynConverter` instance based on the data.
        """
        return SmoldynConverter(data)

    def translate_data_object(
            self,
            data_object_converter: SmoldynConverter,
            box_size: Union[float, int],
            n_dim=3,
            translation_magnitude: Optional[Union[int, float]] = None
            ) -> TrajectoryData:
        """Translate the data object's data if the coordinates are all positive to center the data in the
            simularium viewer.

            Args:
                data_object_converter: Instance of `SmoldynConverter` loaded with `SmoldynData`.
                box_size: size of the simularium viewer box.
                n_dim: n dimensions of the simulation output. Defaults to `3`.
                translation_magnitude: magnitude by which to translate and filter. Defaults to `-box_size / 2`.

            Returns:
                `TrajectoryData`: translated data object instance.
        """
        translation_magnitude = translation_magnitude or -box_size / 2
        return data_object_converter.filter_data([
            TranslateFilter(
                translation_per_type={},
                default_translation=translation_magnitude * np.ones(n_dim)
            ),
        ])

    def generate_simularium_file(
            self,
            box_size=1.,
            spatial_units="nm",
            temporal_units="s",
            n_dim=3,
            io_format="binary",
            translate=True,
            overwrite=True,
            validate_ids=True,
            simularium_filename: Optional[str] = None,
            display_data: Optional[Dict[str, DisplayData]] = None,
            new_omex_filename: Optional[str] = None,
            ) -> None:
        """Generate a new simularium file based on `self.archive.rootpath`. If `self.archive.rootpath` is an `.omex`
            file, the outputs will be re-bundled.

            Args:
                box_size(:obj:`float`): `Optional`: size by which to scale the simulation stage. Defaults to `1.`
                spatial_units(:obj:`str`): `Optional`: units by which to measure the spatial aspect
                    of the simulation. Defaults to `nm`.
                temporal_units(:obj:`str`): `Optional`: units by which to measure the temporal aspect
                    of the simulation. Defaults to `s`.
                n_dim(:obj:`int`): `Optional`: n dimensions of the simulation output. Defaults to `3`.
                simularium_filename(:obj:`str`): `Optional`: filename by which to save the simularium output. Defaults
                    to `archive.simularium_filename`.
                display_data(:obj:`Dict[str, DisplayData]`): `Optional`: Dictionary of DisplayData objects.
                new_omex_filename(:obj:`str`): `Optional`: Filename by which to save the newly generate .omex IF and
                    only IF `self.archive.rootpath` is an `.omex` file.
                io_format(:obj:`str`): format in which to write out the simularium file. Used as an input param to call
                    `super.write_simularium_file`. Options include `'binary'` and `'json'`. Capitals may be used in
                    this string. Defaults to `binary`.
                translate(:obj:`bool`): Whether to translate the simulation mirror data. Defaults to `True`.
                overwrite(:obj:`bool`): Whether to overwrite a simularium file of the same name as `simularium_filename`
                    if one already exists in the COMBINE archive. Defaults to `True`.
                validate_ids(:obj:`bool`): Whether to call the write method using `validation=True`. Defaults to True.
        """
        if not simularium_filename:
            simularium_filename = self.archive.simularium_filename

        if os.path.exists(simularium_filename):
            warn('That file already exists in this COMBINE archive.')
            if not overwrite:
                warn('Overwrite is turned off an thus a new file will not be generated.')
                return

        input_file = self.generate_input_file_data_object()
        data = self.generate_output_data_object(
            file_data=input_file,
            display_data=display_data,
            spatial_units=spatial_units,
            temporal_units=temporal_units
        )

        if translate:
            c = self.generate_converter(data)
            data = self.translate_data_object(c, box_size, n_dim, translation_magnitude=box_size)

        # write the simularium file
        self.write_simularium_file(
            data=data,
            simularium_filename=simularium_filename,
            save_format=io_format,
            validation=validate_ids
        )
        print('New Simularium file generated!!')

        # add new file to manifest
        self.archive.add_simularium_file_to_manifest(simularium_fp=simularium_filename)

        # re-zip the archive if it was passed as an omex file
        if self.archive.was_unzipped:
            writer = ArchiveWriter()
            paths = list(self.archive.get_all_archive_filepaths().values())
            writer.run(paths, self.archive.rootpath)
            print('Omex bundled!')
