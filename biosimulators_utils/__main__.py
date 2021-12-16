""" Program for validating that simulation tools are consistent with the BioSimulators standards

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-22
:Copyright: 2020, BioSimulators Team
:License: MIT
"""

from .combine.data_model import CombineArchiveContentFormat
from .config import get_config
from .sedml.data_model import ModelLanguage, OneStepSimulation, SteadyStateSimulation, UniformTimeCourseSimulation
from .utils.core import flatten_nested_list_of_strings
from .warnings import warn, BioSimulatorsWarning
import biosimulators_utils
import cement
import json
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
    # ModelLanguage.ZGINML,
    # ModelLanguage.LEMS,
    # ModelLanguage.NeuroML,
    ModelLanguage.RBA,
    ModelLanguage.SBML,
    ModelLanguage.Smoldyn,
    ModelLanguage.XPP,
]

VALIDATE_MODEL_LANGUAGES = [
    ModelLanguage.BNGL,
    ModelLanguage.CellML,
    # ModelLanguage.ZGINML,
    ModelLanguage.LEMS,
    ModelLanguage.NeuroML,
    ModelLanguage.RBA,
    ModelLanguage.SBML,
    ModelLanguage.Smoldyn,
    ModelLanguage.XPP,
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
            assert model_lang in BUILD_COMBINE_ARCHIVE_MODEL_LANGUAGES
        except (KeyError, AssertionError):
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

        config = get_config()
        build_combine_archive_for_model(model_filename, model_lang, sim_type, args.archive_filename, config=config)


class ValidateModelController(cement.Controller):
    """ Controller for validating models (e.g., CellML, SBML files) """

    class Meta:
        label = 'validate-model'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Validate a model (e.g., CellML, SBML file)"
        description = "Validate a model (e.g., CellML, SBML file)"
        arguments = [
            (
                ['language'],
                dict(
                    type=str,
                    help='Model language ({}, or {})'.format(
                        ', '.join('`{}`'.format(lang.name) for lang in VALIDATE_MODEL_LANGUAGES[0:-1]),
                        ', '.join('`{}`'.format(lang.name) for lang in VALIDATE_MODEL_LANGUAGES[-1:]),
                    ),
                ),
            ),
            (
                ['filename'],
                dict(
                    type=str,
                    help='Path to model',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        import biosimulators_utils.sedml.validation

        args = self.app.pargs

        try:
            language = ModelLanguage[args.language]
            assert language in VALIDATE_MODEL_LANGUAGES
        except (KeyError, AssertionError):
            raise SystemExit('Model language must be one of {}, or {}, not `{}`.'.format(
                ', '.join('`{}`'.format(lang.name) for lang in VALIDATE_MODEL_LANGUAGES[0:-1]),
                ', '.join('`{}`'.format(lang.name) for lang in VALIDATE_MODEL_LANGUAGES[-1:]),
                args.language,
            ))

        filename = args.filename

        config = get_config()
        errors, warnings, _ = biosimulators_utils.sedml.validation.validate_model_with_language(filename, language, config=config)

        if warnings:
            msg = 'The model file `{}` may be invalid.\n  {}'.format(
                filename, flatten_nested_list_of_strings(warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)

        if errors:
            msg = 'The model file `{}` is invalid.\n  {}'.format(
                filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  '))
            raise SystemExit(msg)

        print('The model file `{}` is valid.'.format(filename))


class ValidateSimulationController(cement.Controller):
    """ Controller for validating simulation experiments (SED-ML files) """

    class Meta:
        label = 'validate-simulation'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Validate a simulation experiment (SED-ML file)"
        description = "Validate a simulation experiment (SED-ML file)"
        arguments = [
            (
                ['filename'],
                dict(
                    type=str,
                    help='Path to a SED-ML file',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        import biosimulators_utils.sedml.io

        args = self.app.pargs

        config = get_config()
        reader = biosimulators_utils.sedml.io.SedmlSimulationReader()
        try:
            reader.run(args.filename, validate_models_with_languages=False, validate_targets_with_model_sources=False, config=config)
        except Exception:
            if not reader.errors:
                raise

        if reader.warnings:
            msg = 'The SED-ML file `{}` may be invalid.\n  {}'.format(
                args.filename, flatten_nested_list_of_strings(reader.warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)

        if reader.errors:
            msg = 'The SED-ML file `{}` is invalid.\n  {}'.format(
                args.filename, flatten_nested_list_of_strings(reader.errors).replace('\n', '\n  '))
            raise SystemExit(msg)

        print('The SED-ML file `{}` is likely valid.'.format(args.filename))


class ValidateMetadataController(cement.Controller):
    """ Controller for validating metadata (OMEX Metadata files) """

    class Meta:
        label = 'validate-metadata'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Validate metadata (OMEX Metadata file)"
        description = "Validate metadata (OMEX Metadata file)"
        arguments = [
            (
                ['filename'],
                dict(
                    type=str,
                    help='Path to an OMEX Metadata file',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        import biosimulators_utils.omex_meta.io

        args = self.app.pargs

        _, errors, warnings = biosimulators_utils.omex_meta.io.read_omex_meta_file(args.filename)

        if warnings:
            msg = 'The OMEX Metadata file `{}` may be invalid.\n  {}'.format(
                args.filename, flatten_nested_list_of_strings(warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)

        if errors:
            msg = 'The OMEX Metadata file `{}` is invalid.\n  {}'.format(
                args.filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  '))
            raise SystemExit(msg)

        print('The OMEX metadata file `{}` is valid.'.format(args.filename))


class ValidateModelingProjectController(cement.Controller):
    """ Controller for validating modeling projects (COMBINE/OMEX archives) """

    class Meta:
        label = 'validate-project'
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

        config = get_config()

        reader = biosimulators_utils.combine.io.CombineArchiveReader()
        try:
            archive = reader.run(args.filename, archive_dirname, config=config)
        except Exception as exception:
            shutil.rmtree(archive_dirname)
            raise SystemExit(str(exception))

        errors, warnings = biosimulators_utils.combine.validation.validate(
            archive, archive_dirname,
            formats_to_validate=list(CombineArchiveContentFormat.__members__.values()),
            config=config,
        )
        if warnings:
            msg = 'The COMBINE/OMEX archive may be invalid.\n  {}'.format(
                flatten_nested_list_of_strings(warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)

        if errors:
            shutil.rmtree(archive_dirname)

            msg = '`{}` is not a valid COMBINE/OMEX archive.\n  {}'.format(
                args.filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  '))
            raise SystemExit(msg)

        # print summary
        print(biosimulators_utils.combine.utils.get_summary_sedml_contents(archive, archive_dirname, config=config))

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
                    metavar='docker-image',
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
            config = get_config()
            if config.DEBUG:
                raise
            raise SystemExit(str(exception))


class ConvertController(cement.Controller):
    """ Controller for converting among formats """

    class Meta:
        label = 'convert'
        stacked_on = 'base'
        stacked_type = 'nested'
        help = "Convert files among formats"
        description = "Convert files among formats"
        arguments = []

    @cement.ex(hide=True)
    def _default(self):
        self._parser.print_help()


class ConvertEscherController(cement.Controller):
    """ Controller for converting Escher maps to Vega data visualizations """

    class Meta:
        label = 'escher-to-vega'
        stacked_on = 'convert'
        stacked_type = 'nested'
        help = "Convert an Escher map to Vega"
        description = "Convert an Escher map of a metabolic network to the Vega data visualization format"
        arguments = [
            (
                ['--data-sedml'],
                dict(
                    type=str,
                    help=(
                        'Id of a report in a SED-ML file and the location of the SED-ML file in its parent '
                        'COMBINE archive which can record the predicted flux of each reaction '
                        '(e.g., `path/to/simulation.sedml/Table_1`)'
                    ),
                    default=None,
                ),
            ),
            (
                ['--data-file'],
                dict(
                    type=str,
                    help=(
                        'Path to a JSON file which represents a list of dictionaries, each which have two keys '
                        '`label` and `values` whose values are the ids of reactions and arrays of length 1 of '
                        'their predicted fluxes'
                    ),
                    default=None,
                ),
            ),
            (
                ['--data-url'],
                dict(
                    type=str,
                    help=(
                        'URL for a JSON file which represents a list of dictionaries, each which have two keys '
                        '`label` and `values` whose values are the ids of reactions and arrays of length 1 of '
                        'their predicted fluxes'
                    ),
                    default=None,
                ),
            ),
            (
                ['escher_file'],
                dict(
                    metavar='escher-file',
                    type=str,
                    help='Path to the configuration of an Escher map',
                ),
            ),
            (
                ['vega_file'],
                dict(
                    metavar='vega-file',
                    type=str,
                    help='Path to save the diagram in Vega format',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        from biosimulators_utils.viz.vega.escher.core import escher_to_vega
        _convert_diagram(self.app.pargs, 'escher_file', escher_to_vega)


class ConvertGinmlController(cement.Controller):
    """ Controller for converting GINML activity flow diagrams to Vega data visualizations """

    class Meta:
        label = 'ginml-to-vega'
        stacked_on = 'convert'
        stacked_type = 'nested'
        help = "Convert a GINML activity flow diagram to Vega"
        description = "Convert a GINML activity flow diagram to the Vega data visualization format"
        arguments = [
            (
                ['--data-sedml'],
                dict(
                    action='store_true',
                    help=(
                        'Set to indicate that the predicted value of each node should be read from the reports of '
                        'the SED-ML files in a COMBINE archive'
                    ),
                ),
            ),
            (
                ['--data-file'],
                dict(
                    type=str,
                    help=(
                        'Path to a JSON file which represents a list of dictionaries, each which have two keys '
                        '`label` and `values` whose values are the ids of nodes and arrays of their predicted values'
                    ),
                    default=None,
                ),
            ),
            (
                ['--data-url'],
                dict(
                    type=str,
                    help=(
                        'URL for a JSON file which represents a list of dictionaries, each which have two keys '
                        '`label` and `values` whose values are the ids of nodes and arrays of their predicted values'
                    ),
                    default=None,
                ),
            ),
            (
                ['ginml_file'],
                dict(
                    metavar='ginml-file',
                    type=str,
                    help='Path to the GINML file',
                ),
            ),
            (
                ['vega_file'],
                dict(
                    metavar='vega-file',
                    type=str,
                    help='Path to save the diagram in Vega format',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        from biosimulators_utils.viz.vega.ginml.core import ginml_to_vega
        _convert_diagram(self.app.pargs, 'ginml_file', ginml_to_vega)


class ConvertSbgnController(cement.Controller):
    """ Controller for converting SBGN process description maps to Vega data visualizations """

    class Meta:
        label = 'sbgn-to-vega'
        stacked_on = 'convert'
        stacked_type = 'nested'
        help = "Convert a SBGN process description map to Vega"
        description = "Convert a SBGN process description map to the Vega data visualization format"
        arguments = [
            (
                ['--data-sedml'],
                dict(
                    type=str,
                    help=(
                        'Id of a report in a SED-ML file and the location of the SED-ML file in its parent '
                        'COMBINE archive which can record the predicted concentration of each glyph '
                        '(e.g., `path/to/simulation.sedml/Table_1`)'
                    ),
                    default=None,
                ),
            ),
            (
                ['--data-file'],
                dict(
                    type=str,
                    help=(
                        'Path to a JSON file which represents a list of dictionaries, each which have two keys '
                        '`label` and `values` whose values are the labels of glyphs and arrays of their predicted '
                        'concentrations'
                    ),
                    default=None,
                ),
            ),
            (
                ['--data-url'],
                dict(
                    type=str,
                    help=(
                        'URL for a JSON file which represents a list of dictionaries, each which have two keys '
                        '`label` and `values` whose values are the labels of glyphs and arrays of their predicted '
                        'concentrations'
                    ),
                    default=None,
                ),
            ),
            (
                ['sbgn_file'],
                dict(
                    metavar='sbgn-file',
                    type=str,
                    help='Path to the SBGN file',
                ),
            ),
            (
                ['vega_file'],
                dict(
                    metavar='vega-file',
                    type=str,
                    help='Path to save the diagram in Vega format',
                ),
            ),
        ]

    @cement.ex(hide=True)
    def _default(self):
        from biosimulators_utils.viz.vega.sbgn.core import sbgn_pd_map_to_vega
        _convert_diagram(self.app.pargs, 'sbgn_file', sbgn_pd_map_to_vega)


def _convert_diagram(args, diagram_file_attr, converter):
    n_data_args = (
        (args.data_sedml not in [None, False]) +
        (args.data_file is not None) +
        (args.data_url is not None)
    )

    if n_data_args == 0:
        raise SystemExit('One of --data-sedml, --data-file, or --data-url must be used')
    elif n_data_args > 1:
        raise SystemExit('Only one of --data-sedml, --data-file, or --data-url can be used')

    if args.data_sedml:
        if isinstance(args.data_sedml, bool):
            data_set = {'sedmlUri': []}
        else:
            sedDocumentlocation, _, reportId = args.data_sedml.rpartition('/')
            data_set = {'sedmlUri': [sedDocumentlocation, reportId]}

    elif args.data_file:
        with open(args.data_file, 'rb') as file:
            data_set = {'values': json.load(file)}

    else:
        data_set = {'url': args.data_url}

    try:
        converter(data_set, getattr(args, diagram_file_attr), args.vega_file)
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
            ValidateModelController,
            ValidateSimulationController,
            ValidateMetadataController,
            ValidateModelingProjectController,
            ExecuteModelingProjectController,
            ConvertController,
            ConvertEscherController,
            ConvertGinmlController,
            ConvertSbgnController,
        ]


def main():
    with App() as app:
        app.run()
