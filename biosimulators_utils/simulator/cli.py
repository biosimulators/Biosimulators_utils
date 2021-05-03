""" Utilities for creating BioSimulators-compliant command-line interfaces for biosimulation tools.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-04
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .._version import __version__ as biosimulators_utils_version
from .data_model import EnvironmentVariable  # noqa: F401
from kisao._version import __version__ as kisao_version
import cement
import libcombine
try:
    import libsbml
except ModuleNotFoundError:  # pragma: no cover
    libsbml = None
import libsedml
import platform
import sys
import termcolor
import types  # noqa: F401

__all__ = [
    'build_cli',
]


def build_cli(cli_name=None, cli_version=None,
              simulator_name=None, simulator_version=None, simulator_url=None,
              combine_archive_executer=None, environment_variables=None):
    """ Create a BioSimulators-compliant command-line application for a biosimulation tool.

    The command-line application will have two inputs

    * A path to a COMBINE/OMEX archive that describes one or more simulations or one or more models
    * A path to a directory to store the outputs of the execution of the simulations defined in the archive

    The command-line application will also support two additional commands

    * A command for printing help information about the command-line application (`-h`, `--help`)
    * A command for printing version information about the command-line application (`-v`, `--version`)

    Args:
        cli_name (:obj:`str`): name of the command-line program (e.g., `copasi`)
        cli_version (:obj:`str`, optional): version of the command-line application
        simulator_name (:obj:`str`): name of the simulator (e.g., `COPASI`)
        simulator_version (:obj:`str`, optional): version of the simulator
        simulator_url (:obj:`str`, optional): URL for information about the simulator
        combine_archive_executer (:obj:`types.FunctionType`): a function which has two positional arguments
            * The path to the COMBINE/OMEX archive
            * The path to the directory to save the outputs of the simulations defined in the archive
        environment_variables (:obj:`list` of :obj:`EnvironmentVariable`, optional): description of the environment
            variables recognized by the simulator

    Returns:
        :obj:`cement.App`: command-line application

    Raises:
        :obj:`SystemExit`: if the execution of the COMBINE/OMEX archive fails
    """
    python_version = '.'.join(str(i) for i in sys.version_info[0:3])

    if not cli_name:
        raise ValueError('CLI name must be defined')
    if not simulator_name:
        raise ValueError('Simulator name must be defined')
    if not combine_archive_executer:
        raise ValueError('COMBINE/OMEX archive execution method must be provided')

    description_value = "BioSimulators-compliant command-line interface to the {} simulation program{}.".format(
        simulator_name,
        ' <{}>'.format(simulator_url) if simulator_url else '')

    if environment_variables:
        description_value += ('\n\nIn addition to the command-line arguments outlined below, '
                              '{} also supports the following environment variables:\n'
                              ).format(simulator_name)

        for env_var in sorted(environment_variables, key=lambda var: var.name):
            description_value += "\n  '{}': {}".format(env_var.name, env_var.description)
            if env_var.options:
                option_values = ["'" + val + "'" for val in env_var.options]
                description_value += "\n    Options: {}".format(', '.join(option_values))
            if env_var.default:
                description_value += "\n    Default value: '{}'".format(env_var.default)
            if env_var.more_info_url:
                description_value += "\n    More information: {}".format(env_var.more_info_url)

    versions = []
    if simulator_version:
        versions.append(simulator_name + ': ' + simulator_version)
    if cli_version:
        versions.append('CLI: ' + cli_version)
    versions.append('BioSimulators utils: ' + biosimulators_utils_version)
    versions.append('libSED-ML: ' + libsedml.__version__)
    versions.append('KiSAO: ' + kisao_version)
    if libsbml:
        versions.append('libSBML: ' + libsbml.__version__)
    versions.append('libCOMBINE: ' + libcombine.__version__)
    versions.append('Python: ' + python_version)
    versions.append('OS: {} {}'.format(
        platform.system(),
        platform.release(),
    ))
    versions.append('Machine: ' + platform.machine())
    version = '\n'.join(versions)

    class BaseController(cement.Controller):
        """ Base controller for command line application """

        class Meta:
            label = 'base'
            description = description_value
            help = cli_name
            arguments = [
                (
                    ['-i', '--archive'],
                    dict(
                        type=str,
                        required=True,
                        help='Path to COMBINE/OMEX file which contains one or more SED-ML-encoded simulation experiments',
                    ),
                ),
                (
                    ['-o', '--out-dir'],
                    dict(
                        type=str,
                        default='.',
                        help='Directory to save outputs',
                    ),
                ),
                (
                    ['-v', '--version'],
                    dict(
                        action='version',
                        version=version,
                    ),
                ),
            ]

        @cement.ex(hide=True)
        def _default(self):
            args = self.app.pargs
            try:
                combine_archive_executer(args.archive, args.out_dir)
            except Exception as exception:
                raise SystemExit(termcolor.colored(str(exception), 'red')) from exception

    class App(cement.App):
        """ Command line application """
        class Meta:
            label = cli_name
            base_controller = 'base'
            handlers = [
                BaseController,
            ]

    return App
