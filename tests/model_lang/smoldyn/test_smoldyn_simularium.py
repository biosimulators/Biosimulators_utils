import os
from biosimulators_utils.model_lang.smoldyn.utils import generate_new_simularium_file
from biosimulators_utils.model_lang.smoldyn.simularium_converter import SmoldynDataConverter, CombineArchive
from biosimulators_utils.viz.io import write_plot_3d
from biosimulators_utils.report.data_model import DataGeneratorResults
from biosimulators_utils.sedml.data_model import Plot3D

ARCHIVE_NAME = 'minE_Andrews_0523'
ARCHIVE_PATH = os.path.join('tests', 'fixtures', 'smoldyn', ARCHIVE_NAME)
SIMULARIUM_FILE = os.path.join(ARCHIVE_PATH, f'{ARCHIVE_NAME}')


def test_plot_3d_from_df():
    archive = CombineArchive(rootpath=ARCHIVE_PATH, simularium_filename=SIMULARIUM_FILE)
    converter = SmoldynDataConverter(archive)
    df = converter.read_model_output_dataframe()

    # Sub-method for plotting to 3d
    print(df)
    data_generators = list(set(df['mol_name'].tolist()))
    print(data_generators)
    plot_type = Plot3D()
    results = DataGeneratorResults()
    # plot = write_plot_3d(plot_type,


if __name__ == '__main__':
    generate_new_simularium_file(
        archive_rootpath=ARCHIVE_PATH,
        simularium_filename=SIMULARIUM_FILE
    )
    # test_plot_3d_from_df()




