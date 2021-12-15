""" Utilities for validating LEMS models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-03
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...log.data_model import StandardOutputErrorCapturerLevel
from ...log.utils import StandardOutputErrorCapturer
from ...config import Config, get_config  # noqa: F401
from lems.model.model import Model
from pyneuroml.pynml import get_path_to_jnml_jar, run_jneuroml, DEFAULTS
import os
import shutil
import tempfile
import zipfile


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
            * :obj:`Model`: model
    """
    config = config or get_config()

    errors = []
    warnings = []
    model = None

    with StandardOutputErrorCapturer(relay=False, level=StandardOutputErrorCapturerLevel.c):
        valid, output = validate_neuroml2_lems_file(filename, exit_on_fail=False, return_string=True)
        if not valid:
            errors.append(['`{}` is not a valid LEMS file.'.format(filename), [[output]]])
            return (errors, warnings, model)

    core_types_dir = tempfile.mkdtemp()
    jar_filename = get_path_to_jnml_jar()
    with zipfile.ZipFile(jar_filename, 'r') as jar_file:
        neuroml2_core_type_members = (name for name in jar_file.namelist() if name.startswith('NeuroML2CoreTypes/'))
        jar_file.extractall(core_types_dir, members=neuroml2_core_type_members)

    model = Model(include_includes=True, fail_on_missing_includes=config.VALIDATE_IMPORTED_MODEL_FILES)
    model.add_include_directory(os.path.join(core_types_dir, 'NeuroML2CoreTypes'))
    model.import_from_file(filename)
    shutil.rmtree(core_types_dir)

    return (errors, warnings, model)


def validate_neuroml2_lems_file(
    nml2_lems_file_name, max_memory=DEFAULTS["default_java_max_memory"], exit_on_fail=True, return_string=False,
):
    # type: (str, str) -> bool
    """Validate a NeuroML 2 LEMS file using jNeuroML.
    Note that this uses jNeuroML and so is aware of the standard NeuroML LEMS
    definitions.
    TODO: allow inclusion of other paths for user-defined LEMS definitions
    (does the -norun option allow the use of -I?)
    :param nml2_lems_file_name: name of file to validate
    :type nml2_lems_file_name: str
    :param max_memory: memory to use for the Java virtual machine
    :type max_memory: str
    :param exit_on_fail: toggle whether command should exit if jnml fails
    :type exit_on_fail: bool
    :param return_string: toggle whether the output string should be returned
    :type return_string: bool
    :returns: Either a bool, or a tuple (bool, str): True if jnml ran without errors, false if jnml fails; along with the message returned by jnml
    """
    post_args = ""
    post_args += "-norun"

    return run_jneuroml(
        "",
        nml2_lems_file_name,
        post_args,
        max_memory=max_memory,
        verbose=False,
        report_jnml_output=True,
        exit_on_fail=exit_on_fail,
        return_string=return_string,
    )
