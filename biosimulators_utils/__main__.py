""" Program for validating that simulation tools are consistent with the BioSimulators standards

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-22
:Copyright: 2020, BioSimulators Team
:License: MIT
"""

from .combine.data_model import CombineArchiveContentFormat
from .sedml.data_model import ModelLanguage, OneStepSimulation, SteadyStateSimulation, UniformTimeCourseSimulation
from .utils.core import flatten_nested_list_of_strings
from .warnings import warn, BioSimulatorsWarning
import biosimulators_utils
import cement
import shutil
import tempfile


class BaseController(cement.Controller):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = "Utilities for working with containerized biosimulation tools"
        help = "Utilities for working with containerized biosimulation tools"
        arguments = [
            (['-v', '--version'], dict(
                action='version',
                version=biosimulators_utils.__version__,
            )),
        ]

    @cement.ex(hide=True)
    def _default(self):
        self._parser.print_help()


BUILD_COMBINE_ARCHIVE_MODEL_LANGUAGES = [
    ModelLanguage.BNGL,
    ModelLanguage.CellML,
    # ModelLanguage.LEMS,
    ModelLanguage.SBML,
    ModelLanguage.Smoldyn,
]

BUILD_COMBINE_ARCHIVE_SIMULATION_TYPES = [
    OneStepSimulation,
    SteadyStateSimulation,
    UniformTimeCourseSimulation,
]


class BuildModelingProjectController(cement.Controller):
    """ Controller for building a COMBINE/OMEX archive with a SED-ML file for a model """

    class Meta:
        label = 'build-project'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Build a modeling project"
        description = "Build a COMBINE/OMEX archive with a SED-ML file for a model"
        arguments = [
            (
                ['model_language'],
                dict(
                    metavar='model-language',
                    type=str,
                    help='Model language ({}, or {})'.format(
                        ', '.join('`{}`'.format(lang.name) for lang in BUILD_COMBINE_ARCHIVE_MODEL_LANGUAGES[0:-1]),
                        ', '.join('`{}`'.format(lang.name) for lang in BUILD_COMBINE_ARCHIVE_MODEL_LANGUAGES[-1:]),
                    ),
                ),
            ),
            (
                ['model_filename'],
                dict(
                    metavar='model-filename',
                    type=str,
                    help='Path to model',
                ),
            ),
            (
                ['simulation_type'],
                dict(
                    metavar='simulation-type',
                    type=str,
                    help='Type of simulation ({}, or {})'.format(
                        ', '.join('`{}`'.format(type.__name__[0:-10]) for type in BUILD_COMBINE_ARCHIVE_SIMULATION_TYPES[0:-1]),
                        ', '.join('`{}`'.format(type.__name__[0:-10]) for type in BUILD_COMBINE_ARCHIVE_SIMULATION_TYPES[-1:]),
                    ),
                ),
            ),
            (
                ['archive_filename'],
                dict(
                    metavar='archive-filename',
                    type=str,
                    help='Path to save archive',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        from .sedml.model_utils import build_combine_archive_for_model

        args = self.app.pargs

        try:
            model_lang = ModelLanguage[args.model_language]
        except KeyError:
            raise SystemExit('Model language must be one of {}, or {}, not `{}`.'.format(
                ', '.join('`{}`'.format(lang.name) for lang in BUILD_COMBINE_ARCHIVE_MODEL_LANGUAGES[0:-1]),
                ', '.join('`{}`'.format(lang.name) for lang in BUILD_COMBINE_ARCHIVE_MODEL_LANGUAGES[-1:]),
                args.model_language,
            ))

        model_filename = args.model_filename

        sim_type = None
        for a_sim_type in BUILD_COMBINE_ARCHIVE_SIMULATION_TYPES:
            if a_sim_type.__name__ == args.simulation_type + 'Simulation':
                sim_type = a_sim_type
                break
        if sim_type is None:
            raise SystemExit('Simulation type must be one of {}, or {}, not `{}`.'.format(
                ', '.join('`{}`'.format(type.__name__[0:-10]) for type in BUILD_COMBINE_ARCHIVE_SIMULATION_TYPES[0:-1]),
                ', '.join('`{}`'.format(type.__name__[0:-10]) for type in BUILD_COMBINE_ARCHIVE_SIMULATION_TYPES[-1:]),
                args.simulation_type,
            ))

        build_combine_archive_for_model(model_filename, model_lang, sim_type, args.archive_filename)


class ValidateModelingProjectController(cement.Controller):
    """ Controller for validating modeling projects (COMBINE/OMEX archives) """

    class Meta:
        label = 'validate'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Validate a model project (COMBINE/OMEX archive)"
        description = "Validate a modeling project (COMBINE/OMEX archive and its contents)"
        arguments = [
            (
                ['filename'],
                dict(
                    type=str,
                    help='Path to a COMBINE/OMEX archive',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        import biosimulators_utils.combine.io
        import biosimulators_utils.combine.utils
        import biosimulators_utils.combine.validation

        args = self.app.pargs

        archive_dirname = tempfile.mkdtemp()

        reader = biosimulators_utils.combine.io.CombineArchiveReader()
        try:
            archive = reader.run(args.filename, archive_dirname)
        except Exception as exception:
            shutil.rmtree(archive_dirname)
            raise SystemExit(str(exception))

        errors, warnings = biosimulators_utils.combine.validation.validate(
            archive, archive_dirname,
            formats_to_validate=list(CombineArchiveContentFormat.__members__.values()))
        if warnings:
            msg = 'The COMBINE/OMEX archive may be invalid.\n  {}'.format(
                flatten_nested_list_of_strings(warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)

        if errors:
            shutil.rmtree(archive_dirname)

            msg = 'The COMBINE/OMEX archive is invalid.\n  {}'.format(
                flatten_nested_list_of_strings(errors).replace('\n', '\n  '))
            raise SystemExit(msg)

        # print summary
        print(biosimulators_utils.combine.utils.get_summary_sedml_contents(archive, archive_dirname))

        # clean up
        shutil.rmtree(archive_dirname)


class ExecuteModelingProjectController(cement.Controller):
    """ Controller for using containerized simulation tools to execute modeling projects (COMBINE/OMEX archives) """

    class Meta:
        label = 'exec'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Execute a model project (COMBINE/OMEX archive)"
        description = "Use a containerized simulation tool to execute a modeling project (COMBINE/OMEX archive)"
        arguments = [
            (
                ['docker_image'],
                dict(
                    type=str,
                    help='Tag or URL for the Docker image of the simulation tools (e.g., ghcr.io/biosimulators/tellurium:latest)',
                ),
            ),
            (
                ['-i', '--archive'],
                dict(
                    type=str,
                    required=True,
                    help='Path to a COMBINE/OMEX file which contains one or more SED-ML-encoded simulation experiments',
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
                ['--do-not-pull-image'],
                dict(
                    action='store_true',
                    help="If set, do not pull Docker image",
                ),
            ),
            (
                ['--env'],
                dict(
                    type=str,
                    nargs='+',
                    default=[],
                    help="Key-value pairs of values of environment variables (e.g., `KEY=value`)",
                ),
            ),
            (
                ['--tmp-dir'],
                dict(
                    type=str,
                    default='/tmp',
                    help="Path to temporary directory in Docker image. Default: `/tmp`.",
                ),
            ),
            (
                ['--path-sep'],
                dict(
                    type=str,
                    default='/',
                    help="Separator for file paths in Docker image. Default: `/`.",
                ),
            ),
            (
                ['--user'],
                dict(
                    type=str,
                    default="_CURRENT_USER_",
                    help="Id of user to execute commands within the Docker container. Default: `_CURRENT_USER_`",
                ),
            ),
            (
                ['--no-tty'],
                dict(
                    action='store_true',
                    help="Do not allocate a pseudo-TTY",
                ),
            ),
            (
                ['--keep-container'],
                dict(
                    action='store_true',
                    help="Keep Docker container (do not automatically remove the container when the archive is finished executing)",
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        import biosimulators_utils.simulator.exec

        args = self.app.pargs

        try:
            env = {}
            for key_value in args.env:
                key, sep, value = key_value.partition('=')
                if sep != '=':
                    raise ValueError('Environment variables must be pairs of keys and values (e.g., KEY=value)')
                env[key] = value

            biosimulators_utils.simulator.exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                args.archive, args.out_dir, args.docker_image,
                docker_image_temp_dir=args.tmp_dir, docker_image_path_sep=args.path_sep,
                environment=env, pull_docker_image=not args.do_not_pull_image,
                user_to_exec_within_container=args.user, allocate_tty=not args.no_tty, remove_docker_container=not args.keep_container)

        except Exception as exception:
            raise SystemExit(str(exception))


class App(cement.App):
    """ Command line application """
    class Meta:
        label = 'biosimulators-utils'
        base_controller = 'base'
        handlers = [
            BaseController,
            BuildModelingProjectController,
            ValidateModelingProjectController,
            ExecuteModelingProjectController,
        ]


def main():
    with App() as app:
        app.run()
