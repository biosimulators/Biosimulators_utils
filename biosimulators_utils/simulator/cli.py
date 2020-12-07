""" Utilities for creating BioSimulators-compliant command-line interfaces for biosimulation tools.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-04
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import cement
import sys
import types  # noqa: F401

__all__ = [
    'build_cli',
]


def build_cli(cli_name=None, cli_version=None,
              simulator_name=None, simulator_version=None, simulator_url=None,
              combine_archive_executer=None):
    """ Create a BioSimulators-compliant command-line application for a biosimulation tool.

    The command-line application will have two inputs

    * A path to a COMBINE/OMEX archive that describes one or more simulations or one or more models
    * A path to a directory to store the ouputs of the execution of the simulations defined in the archive

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

    versions = []
    if simulator_version:
        versions.append(simulator_name + ': ' + simulator_version)
    if cli_version:
        versions.append('CLI: ' + cli_version)
    versions.append('Python: ' + python_version)
    version = ', '.join(versions)

    class BaseController(cement.Controller):
        """ Base controller for command line application """

        class Meta:
            label = 'base'
            description = "BioSimulators-compliant command-line interface to the {} simulation program{}.".format(
                simulator_name,
                '<{}>'.format(simulator_url) if simulator_url else '')
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
                raise SystemExit(str(exception)) from exception

    class App(cement.App):
        """ Command line application """
        class Meta:
            label = 'cli'
            base_controller = 'base'
            handlers = [
                BaseController,
            ]

    return App
