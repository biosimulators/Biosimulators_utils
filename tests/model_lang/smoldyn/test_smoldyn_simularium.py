import os
from biosimulators_utils.model_lang.smoldyn.utils import generate_new_simularium_file

ARCHIVE_NAME = 'minE_Andrews_0523'
ARCHIVE_PATH = os.path.join('tests', 'fixtures', 'smoldyn', ARCHIVE_NAME)
SIMULARIUM_FILE = os.path.join(ARCHIVE_PATH, f'{ARCHIVE_NAME}')

generate_new_simularium_file(
    archive_rootpath=ARCHIVE_PATH,
    simularium_filename=SIMULARIUM_FILE
)
