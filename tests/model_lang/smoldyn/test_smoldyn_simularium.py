import os
from biosimulators_utils.model_lang.smoldyn.utils import generate_new_simularium_file
from biosimulators_utils.model_lang.smoldyn.simularium_converter import SmoldynDataConverter, SmoldynCombineArchive


ARCHIVE_NAME = 'minE_Andrews_0523'
ARCHIVE_PATH = os.path.join('tests', 'fixtures', 'smoldyn', ARCHIVE_NAME)
SIMULARIUM_FILE = os.path.join(ARCHIVE_PATH, f'{ARCHIVE_NAME}')


def test_plot_3d_from_df():
    archive = SmoldynCombineArchive(rootpath=ARCHIVE_PATH, simularium_filename=SIMULARIUM_FILE)
    converter = SmoldynDataConverter(archive)

    # NOTE: Add Sub-method for plotting to 3d
    df = converter.read_model_output_dataframe()
    data_generators = list(set(df['mol_name'].tolist()))
    print(df)
    print(data_generators)


def test_generate_simularium_file():
    archive = SmoldynCombineArchive(rootpath=ARCHIVE_PATH, simularium_filename=SIMULARIUM_FILE)
    converter = SmoldynDataConverter(archive)
    print(f'Has smoldyn: {converter.has_smoldyn}')


if __name__ == '__main__':
    # generate_new_simularium_file(
    #     archive_rootpath=ARCHIVE_PATH,
    #     simularium_filename=SIMULARIUM_FILE
    # )
    # test_plot_3d_from_df()
    test_generate_simularium_file()




