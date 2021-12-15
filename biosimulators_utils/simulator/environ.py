""" Common environment variables for simulators

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
from ..omex_meta.data_model import OmexMetadataInputFormat, OmexMetadataOutputFormat, OmexMetadataSchema
from ..report.data_model import ReportFormat
from ..viz.data_model import VizFormat
from .data_model import EnvironmentVariable
from kisao import AlgorithmSubstitutionPolicy, ALGORITHM_SUBSTITUTION_POLICY_LEVELS
from unittest import mock

__all__ = [
    'ENVIRONMENT_VARIABLES',
]

with mock.patch.dict('os.environ', {}):
    config = get_config()

ENVIRONMENT_VARIABLES = {
    # formats
    'OMEX_METADATA_INPUT_FORMAT': EnvironmentVariable(
        name='OMEX_METADATA_INPUT_FORMAT',
        description='Which input format to use to validate OMEX metadata files during the validation of COMBINE/OMEX archives.',
        options=sorted(OmexMetadataInputFormat.__members__.keys()),
        default=config.OMEX_METADATA_INPUT_FORMAT.value,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'OMEX_METADATA_OUTPUT_FORMAT': EnvironmentVariable(
        name='OMEX_METADATA_OUTPUT_FORMAT',
        description='Which output format to use to export OMEX metadata files.',
        options=sorted(OmexMetadataOutputFormat.__members__.keys()),
        default=config.OMEX_METADATA_OUTPUT_FORMAT.value,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'OMEX_METADATA_SCHEMA': EnvironmentVariable(
        name='OMEX_METADATA_SCHEMA',
        description='Which schema to use to validate OMEX metadata files during the validation of COMBINE/OMEX archives.',
        options=sorted(OmexMetadataSchema.__members__.keys()),
        default=config.OMEX_METADATA_SCHEMA.value,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    # validation
    'VALIDATE_OMEX_MANIFESTS': EnvironmentVariable(
        name='VALIDATE_OMEX_MANIFESTS',
        description='Whether to validate OMEX manifests during the validation of COMBINE/OMEX archives.',
        options=['0', '1'],
        default='1' if config.VALIDATE_OMEX_MANIFESTS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VALIDATE_SEDML': EnvironmentVariable(
        name='VALIDATE_SEDML',
        description='Whether to validate SED-ML files during the validation of COMBINE/OMEX archives.',
        options=['0', '1'],
        default='1' if config.VALIDATE_SEDML else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VALIDATE_SEDML_MODELS': EnvironmentVariable(
        name='VALIDATE_SEDML_MODELS',
        description='Whether to validate models referenced by SED-ML files during the validation of COMBINE/OMEX archives.',
        options=['0', '1'],
        default='1' if config.VALIDATE_SEDML_MODELS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VALIDATE_IMPORTED_MODEL_FILES': EnvironmentVariable(
        name='VALIDATE_IMPORTED_MODEL_FILES',
        description='Whether to validate files imported from models.',
        options=['0', '1'],
        default='1' if config.VALIDATE_IMPORTED_MODEL_FILES else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VALIDATE_OMEX_METADATA': EnvironmentVariable(
        name='VALIDATE_OMEX_METADATA',
        description='Whether to validate OMEX metadata (RDF files) during the validation of COMBINE/OMEX archives.',
        options=['0', '1'],
        default='1' if config.VALIDATE_OMEX_METADATA else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VALIDATE_IMAGES': EnvironmentVariable(
        name='VALIDATE_IMAGES',
        description='Whether to validate the images in COMBINE/OMEX archives during their validation.',
        options=['0', '1'],
        default='1' if config.VALIDATE_IMAGES else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VALIDATE_RESULTS': EnvironmentVariable(
        name='VALIDATE_RESULTS',
        description='Whether to validate the results of simulations following their execution.',
        options=['0', '1'],
        default='1' if config.VALIDATE_RESULTS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    # algorithm substitution
    'ALGORITHM_SUBSTITUTION_POLICY': EnvironmentVariable(
        name='ALGORITHM_SUBSTITUTION_POLICY',
        description='Policy for substituting alternative algorithms.',
        options=[policy.value for policy, _ in sorted(ALGORITHM_SUBSTITUTION_POLICY_LEVELS.items(),
                                                      key=lambda policy_level: policy_level[1])],
        default=AlgorithmSubstitutionPolicy.SIMILAR_VARIABLES.value,
        more_info_url='https://docs.biosimulations.org/concepts/conventions/simulator-interfaces/',
    ),

    # reports
    'COLLECT_COMBINE_ARCHIVE_RESULTS': EnvironmentVariable(
        name='COLLECT_COMBINE_ARCHIVE_RESULTS',
        description='Whether to assemble an in memory data structure with all of the simulation results of COMBINE/OMEX archives.',
        options=['0', '1'],
        default='1' if config.COLLECT_SED_DOCUMENT_RESULTS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'COLLECT_SED_DOCUMENT_RESULTS': EnvironmentVariable(
        name='COLLECT_SED_DOCUMENT_RESULTS',
        description='Whether to assemble an in memory data structure with all of the simulation results of SED documents.',
        options=['0', '1'],
        default='1' if config.COLLECT_SED_DOCUMENT_RESULTS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'REPORT_FORMATS': EnvironmentVariable(
        name='REPORT_FORMATS',
        description='Comma-separated list of formats to save each SED-ML report.',
        options=sorted(ReportFormat.__members__.keys()),
        default=', '.join(config.REPORT_FORMATS),
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'SAVE_PLOT_DATA': EnvironmentVariable(
        name='SAVE_PLOT_DATA',
        description='Whether to save the data for each SED-ML plot similar to a SED-ML report.',
        options=['0', '1'],
        default='1' if config.SAVE_PLOT_DATA else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'H5_REPORTS_PATH': EnvironmentVariable(
        name='H5_REPORTS_PATH',
        description=(
            'Path relative to output directories to export the results of each SED-ML report '
            '(and, optionally, each plot) in HDF5 format.'
        ),
        options=None,
        default=config.H5_REPORTS_PATH,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'REPORTS_PATH': EnvironmentVariable(
        name='REPORTS_PATH',
        description=(
            'Path relative to output directories to export a zip archive with files that represent '
            'the results of each SED-ML report (and, optionally, each plot) in formats other than HDF5.'
        ),
        options=None,
        default=config.REPORTS_PATH,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    # plots
    'VIZ_FORMATS': EnvironmentVariable(
        name='VIZ_FORMATS',
        description='Comma-separated list of formats to save each SED-ML plot.',
        options=sorted(VizFormat.__members__.keys()),
        default=', '.join(config.VIZ_FORMATS),
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'PLOTS_PATH': EnvironmentVariable(
        name='PLOTS_PATH',
        description=(
            'Path relative to output directories to export a zip archive with files for each SED-ML plot.'
        ),
        options=None,
        default=config.PLOTS_PATH,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    # bundling plots and reports
    'BUNDLE_OUTPUTS': EnvironmentVariable(
        name='BUNDLE_OUTPUTS',
        description=(
            'Whether to bundle all of the exported reports and plots generated by '
            'the execution of a COMBINE/OMEX archive into zip files for all reports and all plots.'
        ),
        options=['0', '1'],
        default='1' if config.BUNDLE_OUTPUTS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'KEEP_INDIVIDUAL_OUTPUTS': EnvironmentVariable(
        name='KEEP_INDIVIDUAL_OUTPUTS',
        description=(
            'Whether to delete the individual report and plot files generated by '
            'the execution of a COMBINE/OMEX after bundling the files into a zip file.'
        ),
        options=['0', '1'],
        default='1' if config.KEEP_INDIVIDUAL_OUTPUTS else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    # logs
    'LOG_PATH': EnvironmentVariable(
        name='LOG_PATH',
        description=(
            'Path relative to output directories to save YAML-formatted logs of the '
            'execution of COMBINE/OMEX archives and SED-ML files.'
        ),
        options=None,
        default=config.LOG_PATH,
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),

    'VERBOSE': EnvironmentVariable(
        name='VERBOSE',
        description='Whether to print additional information about simulation runs.',
        options=['0', '1'],
        default='1' if config.VERBOSE else '0',
        more_info_url='https://docs.biosimulations.org/concepts/conventions/simulator-interfaces/',
    ),

    # debugging
    'DEBUG': EnvironmentVariable(
        name='DEBUG',
        description='Whether to raise exceptions rather than capturing them.',
        options=['0', '1'],
        default='1' if config.DEBUG else '0',
        more_info_url='https://docs.biosimulators.org/Biosimulators_utils/source/biosimulators_utils.html',
    ),
}
