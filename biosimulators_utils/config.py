""" Common configuration for simulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .omex_meta.data_model import OmexMetadataInputFormat, OmexMetadataOutputFormat, OmexMetadataSchema
from .report.data_model import ReportFormat  # noqa: F401
from .viz.data_model import VizFormat  # noqa: F401
from kisao import AlgorithmSubstitutionPolicy  # noqa: F401
import appdirs
import enum
import os

__all__ = ['Config', 'get_config', 'Colors', 'get_app_dirs']

DEFAULT_OMEX_METADATA_INPUT_FORMAT = OmexMetadataInputFormat.rdfxml
DEFAULT_OMEX_METADATA_OUTPUT_FORMAT = OmexMetadataOutputFormat.rdfxml_abbrev
DEFAULT_OMEX_METADATA_SCHEMA = OmexMetadataSchema.biosimulations
DEFAULT_ALGORITHM_SUBSTITUTION_POLICY = AlgorithmSubstitutionPolicy.SIMILAR_VARIABLES
DEFAULT_H5_REPORTS_PATH = 'reports.h5'
DEFAULT_REPORTS_PATH = 'reports.zip'
DEFAULT_PLOTS_PATH = 'plots.zip'
DEFAULT_LOG_PATH = 'log.yml'
DEFAULT_BIOSIMULATORS_API_ENDPOINT = 'https://api.biosimulators.org/'
DEFAULT_BIOSIMULATIONS_API_ENDPOINT = 'https://api.biosimulations.org/'
DEFAULT_BIOSIMULATIONS_API_AUTH_ENDPOINT = 'https://auth.biosimulations.org/oauth/token'
DEFAULT_BIOSIMULATIONS_API_AUDIENCE = 'api.biosimulations.org'


class Config(object):
    """ Configuration

    Attributes:
        OMEX_METADATA_INPUT_FORMAT (:obj:`OmexMetadataInputFormat`): format to validate OMEX Metadata files against
        OMEX_METADATA_OUTPUT_FORMAT (:obj:`OmexMetadataOutputFormat`): format to export OMEX Metadata files
        OMEX_METADATA_SCHEMA (:obj:`OmexMetadataSchema`): schema to validate OMEX Metadata files against
        VALIDATE_OMEX_MANIFESTS (:obj:`bool`): whether to validate OMEX manifests during the validation of COMBINE/OMEX archives
        VALIDATE_SEDML (:obj:`bool`): whether to validate SED-ML files during the validation of COMBINE/OMEX archives
        VALIDATE_SEDML_MODELS (:obj:`bool`): whether to validate models referenced by SED-ML files during the validation of COMBINE/OMEX archives
        VALIDATE_IMPORTED_MODEL_FILES (:obj:`bool`): whether to validate files imported from models
        VALIDATE_OMEX_METADATA (:obj:`bool`): whether to validate OMEX metadata (RDF files) during the validation of COMBINE/OMEX archives
        VALIDATE_IMAGES (:obj:`bool`): whether to validate the images in COMBINE/OMEX archives during their validation
        VALIDATE_RESULTS (:obj:`bool`): whether to validate the results of simulations following their execution
        ALGORITHM_SUBSTITUTION_POLICY (:obj:`AlgorithmSubstitutionPolicy`): algorithm substition policy
        COLLECT_COMBINE_ARCHIVE_RESULTS (:obj:`bool`): whether to assemble an in memory data structure with all of the simulation results
            of COMBINE/OMEX archives
        COLLECT_SED_DOCUMENT_RESULTS (:obj:`bool`): whether to assemble an in memory data structure with all of the simulation results
            of SED documents
        SAVE_PLOT_DATA (:obj:`bool`): whether to save data for plots alongside data for reports in CSV/HDF5 files
        REPORT_FORMATS (:obj:`list` of :obj:`ReportFormat`): default formats to generate reports in
        VIZ_FORMATS (:obj:`list` of :obj:`VizFormat`): default formats to generate plots in
        H5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
        REPORTS_PATH (:obj:`str`): path to save zip archive of reports relative to base output directory
        PLOTS_PATH (:obj:`str`): path to save zip archive of plots relative to base output directory
        BUNDLE_OUTPUTS (:obj:`bool`): indicates whether bundles of report and plot outputs should be produced
        KEEP_INDIVIDUAL_OUTPUTS (:obj:`bool`): indicates whether the individual output files should be kept
        LOG (:obj:`bool`): whether to log the execution of a COMBINE/OMEX archive
        LOG_PATH (:obj:`str`): path to save the execution log of a COMBINE/OMEX archive
        BIOSIMULATORS_API_ENDPOINT (:obj:`str`): URL for BioSimulators API
        BIOSIMULATIONS_API_ENDPOINT (:obj:`str`): URL for BioSimulations API
        BIOSIMULATIONS_API_AUTH_ENDPOINT (:obj:`str`): authorization endpoint for the BioSimulations API
        BIOSIMULATIONS_API_AUDIENCE (:obj:`str`): audience for the BioSimulations API
        VERBOSE (:obj:`bool`): whether to display the detailed output of the execution of each task
        DEBUG (:obj:`bool`): whether to raise exceptions rather than capturing them
    """

    def __init__(self,
                 OMEX_METADATA_INPUT_FORMAT=DEFAULT_OMEX_METADATA_INPUT_FORMAT,
                 OMEX_METADATA_OUTPUT_FORMAT=DEFAULT_OMEX_METADATA_OUTPUT_FORMAT,
                 OMEX_METADATA_SCHEMA=DEFAULT_OMEX_METADATA_SCHEMA,
                 VALIDATE_OMEX_MANIFESTS=True,
                 VALIDATE_SEDML=True,
                 VALIDATE_SEDML_MODELS=True,
                 VALIDATE_IMPORTED_MODEL_FILES=True,
                 VALIDATE_OMEX_METADATA=True,
                 VALIDATE_IMAGES=True,
                 VALIDATE_RESULTS=True,
                 ALGORITHM_SUBSTITUTION_POLICY=DEFAULT_ALGORITHM_SUBSTITUTION_POLICY,
                 COLLECT_COMBINE_ARCHIVE_RESULTS=False,
                 COLLECT_SED_DOCUMENT_RESULTS=False,
                 SAVE_PLOT_DATA=True,
                 REPORT_FORMATS=[ReportFormat.h5],
                 VIZ_FORMATS=[VizFormat.pdf],
                 H5_REPORTS_PATH=DEFAULT_H5_REPORTS_PATH,
                 REPORTS_PATH=DEFAULT_REPORTS_PATH,
                 PLOTS_PATH=DEFAULT_PLOTS_PATH,
                 BUNDLE_OUTPUTS=True,
                 KEEP_INDIVIDUAL_OUTPUTS=True,
                 LOG=True,
                 LOG_PATH=DEFAULT_LOG_PATH,
                 BIOSIMULATORS_API_ENDPOINT=DEFAULT_BIOSIMULATORS_API_ENDPOINT,
                 BIOSIMULATIONS_API_ENDPOINT=DEFAULT_BIOSIMULATIONS_API_ENDPOINT,
                 BIOSIMULATIONS_API_AUTH_ENDPOINT=DEFAULT_BIOSIMULATIONS_API_AUTH_ENDPOINT,
                 BIOSIMULATIONS_API_AUDIENCE=DEFAULT_BIOSIMULATIONS_API_AUDIENCE,
                 VERBOSE=False,
                 DEBUG=False):
        """
        Args:
            OMEX_METADATA_INPUT_FORMAT (:obj:`OmexMetadataInputFormat`, optional): format to validate OMEX Metadata files against
            OMEX_METADATA_OUTPUT_FORMAT (:obj:`OmexMetadataOutputFormat`, optional): format to export OMEX Metadata files
            OMEX_METADATA_SCHEMA (:obj:`OmexMetadataSchema`, optional): schema to validate OMEX Metadata files against
            VALIDATE_OMEX_MANIFESTS (:obj:`bool`, optional): whether to validate OMEX manifests during the execution of COMBINE/OMEX archives
            VALIDATE_SEDML (:obj:`bool`, optional): whether to validate SED-ML files during the execution of COMBINE/OMEX archives
            VALIDATE_SEDML_MODELS (:obj:`bool`, optional): whether to validate models referenced by SED-ML files during the execution
                of COMBINE/OMEX archives
            VALIDATE_IMPORTED_MODEL_FILES (:obj:`bool`, optional): whether to validate files imported from models
            VALIDATE_OMEX_METADATA (:obj:`bool`, optional): whether to validate OMEX metadata (RDF files) during the execution of
                COMBINE/OMEX archives
            VALIDATE_IMAGES (:obj:`bool`, optional): whether to validate the images in COMBINE/OMEX archives during their execution
            VALIDATE_RESULTS (:obj:`bool`, optional): whether to validate the results of simulations following their execution
            ALGORITHM_SUBSTITUTION_POLICY (:obj:`str`, optional): algorithm substition policy
            COLLECT_COMBINE_ARCHIVE_RESULTS (:obj:`bool`, optional): whether to assemble an in memory data structure with all of the
                simulation results of COMBINE/OMEX archives
            COLLECT_SED_DOCUMENT_RESULTS (:obj:`bool`, optional): whether to assemble an in memory data structure with all of the
                simulation results of SED documents
            SAVE_PLOT_DATA (:obj:`bool`, optional): whether to save data for plots alongside data for reports in CSV/HDF5 files
            REPORT_FORMATS (:obj:`list` of :obj:`str`, optional): default formats to generate reports in
            VIZ_FORMATS (:obj:`list` of :obj:`str`, optional): default formats to generate plots in
            H5_REPORTS_PATH (:obj:`str`, optional): path to save reports in HDF5 format relative to base output directory
            REPORTS_PATH (:obj:`str`, optional): path to save zip archive of reports relative to base output directory
            PLOTS_PATH (:obj:`str`, optional): path to save zip archive of plots relative to base output directory
            BUNDLE_OUTPUTS (:obj:`bool`, optional): indicates whether bundles of report and plot outputs should be produced
            KEEP_INDIVIDUAL_OUTPUTS (:obj:`bool`, optional): indicates whether the individual output files should be kept
            LOG (:obj:`bool`, optional): whether to log the execution of a COMBINE/OMEX archive
            LOG_PATH (:obj:`str`, optional): path to save the execution status of a COMBINE/OMEX archive
            BIOSIMULATORS_API_ENDPOINT (:obj:`str`, optional): URL for BioSimulators API
            BIOSIMULATIONS_API_ENDPOINT (:obj:`str`, optional): URL for BioSimulations API
            BIOSIMULATIONS_API_AUTH_ENDPOINT (:obj:`str`, optional): authorization endpoint for the BioSimulations API
            BIOSIMULATIONS_API_AUDIENCE (:obj:`str`, optional): audience for the BioSimulations API
            VERBOSE (:obj:`bool`, optional): whether to display the detailed output of the execution of each task
            DEBUG (:obj:`bool`, optional): whether to raise exceptions rather than capturing them
        """
        self.OMEX_METADATA_INPUT_FORMAT = OMEX_METADATA_INPUT_FORMAT
        self.OMEX_METADATA_OUTPUT_FORMAT = OMEX_METADATA_OUTPUT_FORMAT
        self.OMEX_METADATA_SCHEMA = OMEX_METADATA_SCHEMA
        self.VALIDATE_OMEX_MANIFESTS = VALIDATE_OMEX_MANIFESTS
        self.VALIDATE_SEDML = VALIDATE_SEDML
        self.VALIDATE_SEDML_MODELS = VALIDATE_SEDML_MODELS
        self.VALIDATE_IMPORTED_MODEL_FILES = VALIDATE_IMPORTED_MODEL_FILES
        self.VALIDATE_OMEX_METADATA = VALIDATE_OMEX_METADATA
        self.VALIDATE_IMAGES = VALIDATE_IMAGES
        self.VALIDATE_RESULTS = VALIDATE_RESULTS
        self.ALGORITHM_SUBSTITUTION_POLICY = ALGORITHM_SUBSTITUTION_POLICY
        self.COLLECT_COMBINE_ARCHIVE_RESULTS = COLLECT_COMBINE_ARCHIVE_RESULTS
        self.COLLECT_SED_DOCUMENT_RESULTS = COLLECT_SED_DOCUMENT_RESULTS
        self.SAVE_PLOT_DATA = SAVE_PLOT_DATA
        self.REPORT_FORMATS = REPORT_FORMATS
        self.VIZ_FORMATS = VIZ_FORMATS
        self.H5_REPORTS_PATH = H5_REPORTS_PATH
        self.REPORTS_PATH = REPORTS_PATH
        self.PLOTS_PATH = PLOTS_PATH
        self.BUNDLE_OUTPUTS = BUNDLE_OUTPUTS
        self.KEEP_INDIVIDUAL_OUTPUTS = KEEP_INDIVIDUAL_OUTPUTS
        self.LOG = LOG
        self.LOG_PATH = LOG_PATH
        self.BIOSIMULATORS_API_ENDPOINT = BIOSIMULATORS_API_ENDPOINT
        self.BIOSIMULATIONS_API_ENDPOINT = BIOSIMULATIONS_API_ENDPOINT
        self.BIOSIMULATIONS_API_AUTH_ENDPOINT = BIOSIMULATIONS_API_AUTH_ENDPOINT
        self.BIOSIMULATIONS_API_AUDIENCE = BIOSIMULATIONS_API_AUDIENCE
        self.VERBOSE = VERBOSE
        self.DEBUG = DEBUG


def get_config():
    """ Get the configuration

    Returns:
        :obj:`Config`: configuration
    """
    report_formats = os.environ.get('REPORT_FORMATS', 'h5').strip()
    if report_formats:
        report_formats = [ReportFormat(format.strip().lower()) for format in report_formats.split(',')]
    else:
        report_formats = []

    viz_formats = os.environ.get('VIZ_FORMATS', 'pdf').strip()
    if viz_formats:
        viz_formats = [VizFormat(format.strip().lower()) for format in viz_formats.split(',')]
    else:
        viz_formats = []

    return Config(
        OMEX_METADATA_INPUT_FORMAT=OmexMetadataInputFormat(os.environ.get(
            'OMEX_METADATA_INPUT_FORMAT', DEFAULT_OMEX_METADATA_INPUT_FORMAT)),
        OMEX_METADATA_OUTPUT_FORMAT=OmexMetadataOutputFormat(os.environ.get(
            'OMEX_METADATA_OUTPUT_FORMAT', DEFAULT_OMEX_METADATA_OUTPUT_FORMAT)),
        OMEX_METADATA_SCHEMA=OmexMetadataSchema(os.environ.get(
            'OMEX_METADATA_SCHEMA', DEFAULT_OMEX_METADATA_SCHEMA)),
        VALIDATE_OMEX_MANIFESTS=os.environ.get('VALIDATE_OMEX_MANIFESTS', '1').lower() in ['1', 'true'],
        VALIDATE_SEDML=os.environ.get('VALIDATE_SEDML', '1').lower() in ['1', 'true'],
        VALIDATE_SEDML_MODELS=os.environ.get('VALIDATE_SEDML_MODELS', '1').lower() in ['1', 'true'],
        VALIDATE_IMPORTED_MODEL_FILES=os.environ.get('VALIDATE_IMPORTED_MODEL_FILES', '1').lower() in ['1', 'true'],
        VALIDATE_OMEX_METADATA=os.environ.get('VALIDATE_OMEX_METADATA', '1').lower() in ['1', 'true'],
        VALIDATE_IMAGES=os.environ.get('VALIDATE_IMAGES', '1').lower() in ['1', 'true'],
        VALIDATE_RESULTS=os.environ.get('VALIDATE_RESULTS', '1').lower() in ['1', 'true'],
        ALGORITHM_SUBSTITUTION_POLICY=AlgorithmSubstitutionPolicy(os.environ.get(
            'ALGORITHM_SUBSTITUTION_POLICY', DEFAULT_ALGORITHM_SUBSTITUTION_POLICY)),
        COLLECT_COMBINE_ARCHIVE_RESULTS=os.environ.get('COLLECT_COMBINE_ARCHIVE_RESULTS', '0').lower() in ['1', 'true'],
        COLLECT_SED_DOCUMENT_RESULTS=os.environ.get('COLLECT_SED_DOCUMENT_RESULTS', '0').lower() in ['1', 'true'],
        SAVE_PLOT_DATA=os.environ.get('SAVE_PLOT_DATA', '1').lower() in ['1', 'true'],
        REPORT_FORMATS=report_formats,
        VIZ_FORMATS=viz_formats,
        H5_REPORTS_PATH=os.environ.get('H5_REPORTS_PATH', DEFAULT_H5_REPORTS_PATH),
        REPORTS_PATH=os.environ.get('REPORTS_PATH', DEFAULT_REPORTS_PATH),
        PLOTS_PATH=os.environ.get('PLOTS_PATH', DEFAULT_PLOTS_PATH),
        BUNDLE_OUTPUTS=os.environ.get('BUNDLE_OUTPUTS', '1').lower() in ['1', 'true'],
        KEEP_INDIVIDUAL_OUTPUTS=os.environ.get('KEEP_INDIVIDUAL_OUTPUTS', '1').lower() in ['1', 'true'],
        LOG=os.environ.get('LOG', '1').lower() in ['1', 'true'],
        LOG_PATH=os.environ.get('LOG_PATH', DEFAULT_LOG_PATH),
        BIOSIMULATORS_API_ENDPOINT=os.environ.get('BIOSIMULATORS_API_ENDPOINT', DEFAULT_BIOSIMULATORS_API_ENDPOINT),
        BIOSIMULATIONS_API_ENDPOINT=os.environ.get('BIOSIMULATIONS_API_ENDPOINT', DEFAULT_BIOSIMULATIONS_API_ENDPOINT),
        BIOSIMULATIONS_API_AUTH_ENDPOINT=os.environ.get('BIOSIMULATIONS_API_AUTH_ENDPOINT', DEFAULT_BIOSIMULATIONS_API_AUTH_ENDPOINT),
        BIOSIMULATIONS_API_AUDIENCE=os.environ.get('BIOSIMULATIONS_API_AUDIENCE', DEFAULT_BIOSIMULATIONS_API_AUDIENCE),
        VERBOSE=os.environ.get('VERBOSE', '1').lower() in ['1', 'true'],
        DEBUG=os.environ.get('DEBUG', '0').lower() in ['1', 'true'],
    )


Colors = enum.Enum('Colors',
                   {
                       'queued': 'cyan',
                       'success': 'blue',
                       'succeeded': 'blue',
                       'running': 'green',
                       'pass': 'green',
                       'passed': 'green',
                       'failure': 'red',
                       'failed': 'red',
                       'skip': 'magenta',
                       'skipped': 'magenta',
                       'warning': 'yellow',
                       'warned': 'yellow',
                   },
                   type=str)


def get_app_dirs():
    """ Get the directories for the application

    Returns:
        :obj:`appdirs.AppDirs`: application directories
    """
    return appdirs.AppDirs("BioSimulatorsUtils", "BioSimulatorsTeam")
