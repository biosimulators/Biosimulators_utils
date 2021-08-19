""" Common configuration for simulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import appdirs
import enum
import os

__all__ = ['Config', 'get_config', 'Colors', 'get_app_dirs']


class Config(object):
    """ Configuration

    Attributes:
        VALIDATE_OMEX_MANIFESTS (:obj:`bool`): whether to validate OMEX manifests during the validation of COMBINE/OMEX archives
        VALIDATE_SEDML (:obj:`bool`): whether to validate SED-ML files during the validation of COMBINE/OMEX archives
        VALIDATE_SEDML_MODELS (:obj:`bool`): whether to validate models referenced by SED-ML files during the validation of COMBINE/OMEX archives
        VALIDATE_OMEX_METADATA (:obj:`bool`): whether to validate OMEX metadata (RDF files) during the validation of COMBINE/OMEX archives
        VALIDATE_IMAGES (:obj:`bool`): whether to validate the images in COMBINE/OMEX archives during their validation
        ALGORITHM_SUBSTITUTION_POLICY (:obj:`str`): algorithm substition policy
        SAVE_PLOT_DATA (:obj:`bool`): whether to save data for plots alongside data for reports in CSV/HDF5 files
        REPORT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate reports in
        VIZ_FORMATS (:obj:`list` of :obj:`str`): default formats to generate plots in
        H5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
        REPORTS_PATH (:obj:`str`): path to save zip archive of reports relative to base output directory
        PLOTS_PATH (:obj:`str`): path to save zip archive of plots relative to base output directory
        BUNDLE_OUTPUTS (:obj:`bool`): indicates whether bundles of report and plot outputs should be produced
        KEEP_INDIVIDUAL_OUTPUTS (:obj:`bool`): indicates whether the individual output files should be kept
        LOG_PATH (:obj:`str`): path to save the execution status of a COMBINE/OMEX archive
        BIOSIMULATORS_API_ENDPOINT (:obj:`str`): URL for BioSimulators API
        VERBOSE (:obj:`bool`): whether to display the detailed output of the execution of each task
        DEBUG (:obj:`bool`): whether to raise exceptions rather than capturing them
    """

    def __init__(self,
                 VALIDATE_OMEX_MANIFESTS, VALIDATE_SEDML, VALIDATE_SEDML_MODELS, VALIDATE_OMEX_METADATA, VALIDATE_IMAGES,
                 ALGORITHM_SUBSTITUTION_POLICY, SAVE_PLOT_DATA, REPORT_FORMATS, VIZ_FORMATS,
                 H5_REPORTS_PATH, REPORTS_PATH, PLOTS_PATH, BUNDLE_OUTPUTS, KEEP_INDIVIDUAL_OUTPUTS,
                 LOG_PATH, BIOSIMULATORS_API_ENDPOINT, VERBOSE, DEBUG):
        """
        Args:
            VALIDATE_OMEX_MANIFESTS (:obj:`bool`): whether to validate OMEX manifests during the execution of COMBINE/OMEX archives
            VALIDATE_SEDML (:obj:`bool`): whether to validate SED-ML files during the execution of COMBINE/OMEX archives
            VALIDATE_SEDML_MODELS (:obj:`bool`): whether to validate models referenced by SED-ML files during the execution of COMBINE/OMEX archives
            VALIDATE_OMEX_METADATA (:obj:`bool`): whether to validate OMEX metadata (RDF files) during the execution of COMBINE/OMEX archives
            VALIDATE_IMAGES (:obj:`bool`): whether to validate the images in COMBINE/OMEX archives during their execution
            ALGORITHM_SUBSTITUTION_POLICY (:obj:`str`): algorithm substition policy
            SAVE_PLOT_DATA (:obj:`bool`): whether to save data for plots alongside data for reports in CSV/HDF5 files
            REPORT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate reports in
            VIZ_FORMATS (:obj:`list` of :obj:`str`): default formats to generate plots in
            H5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
            REPORTS_PATH (:obj:`str`): path to save zip archive of reports relative to base output directory
            PLOTS_PATH (:obj:`str`): path to save zip archive of plots relative to base output directory
            BUNDLE_OUTPUTS (:obj:`bool`): indicates whether bundles of report and plot outputs should be produced
            KEEP_INDIVIDUAL_OUTPUTS (:obj:`bool`): indicates whether the individual output files should be kept
            LOG_PATH (:obj:`str`): path to save the execution status of a COMBINE/OMEX archive
            BIOSIMULATORS_API_ENDPOINT (:obj:`str`): URL for BioSimulators API
            VERBOSE (:obj:`bool`): whether to display the detailed output of the execution of each task
            DEBUG (:obj:`bool`): whether to raise exceptions rather than capturing them
        """
        self.VALIDATE_OMEX_MANIFESTS = VALIDATE_OMEX_MANIFESTS
        self.VALIDATE_SEDML = VALIDATE_SEDML
        self.VALIDATE_SEDML_MODELS = VALIDATE_SEDML_MODELS
        self.VALIDATE_OMEX_METADATA = VALIDATE_OMEX_METADATA
        self.VALIDATE_IMAGES = VALIDATE_IMAGES
        self.ALGORITHM_SUBSTITUTION_POLICY = ALGORITHM_SUBSTITUTION_POLICY
        self.SAVE_PLOT_DATA = SAVE_PLOT_DATA
        self.REPORT_FORMATS = REPORT_FORMATS
        self.VIZ_FORMATS = VIZ_FORMATS
        self.H5_REPORTS_PATH = H5_REPORTS_PATH
        self.REPORTS_PATH = REPORTS_PATH
        self.PLOTS_PATH = PLOTS_PATH
        self.BUNDLE_OUTPUTS = BUNDLE_OUTPUTS
        self.KEEP_INDIVIDUAL_OUTPUTS = KEEP_INDIVIDUAL_OUTPUTS
        self.LOG_PATH = LOG_PATH
        self.BIOSIMULATORS_API_ENDPOINT = BIOSIMULATORS_API_ENDPOINT
        self.VERBOSE = VERBOSE
        self.DEBUG = DEBUG


def get_config():
    """ Get the configuration

    Returns:
        :obj:`Config`: configuration
    """
    report_formats = os.environ.get('REPORT_FORMATS', 'csv, h5').strip()
    if report_formats:
        report_formats = [format.strip().lower() for format in report_formats.split(',')]
    else:
        report_formats = []

    viz_formats = os.environ.get('VIZ_FORMATS', 'pdf').strip()
    if viz_formats:
        viz_formats = [format.strip().lower() for format in viz_formats.split(',')]
    else:
        viz_formats = []

    return Config(
        VALIDATE_OMEX_MANIFESTS=os.environ.get('VALIDATE_OMEX_MANIFESTS', '1').lower() in ['1', 'true'],
        VALIDATE_SEDML=os.environ.get('VALIDATE_SEDML', '1').lower() in ['1', 'true'],
        VALIDATE_SEDML_MODELS=os.environ.get('VALIDATE_SEDML_MODELS', '1').lower() in ['1', 'true'],
        VALIDATE_OMEX_METADATA=os.environ.get('VALIDATE_OMEX_METADATA', '1').lower() in ['1', 'true'],
        VALIDATE_IMAGES=os.environ.get('VALIDATE_IMAGES', '1').lower() in ['1', 'true'],
        ALGORITHM_SUBSTITUTION_POLICY=os.environ.get('ALGORITHM_SUBSTITUTION_POLICY', 'SIMILAR_VARIABLES'),
        SAVE_PLOT_DATA=os.environ.get('SAVE_PLOT_DATA', '1').lower() in ['1', 'true'],
        REPORT_FORMATS=report_formats,
        VIZ_FORMATS=viz_formats,
        H5_REPORTS_PATH=os.environ.get('H5_REPORTS_PATH', 'reports.h5'),
        REPORTS_PATH=os.environ.get('REPORTS_PATH', 'reports.zip'),
        PLOTS_PATH=os.environ.get('PLOTS_PATH', 'plots.zip'),
        BUNDLE_OUTPUTS=os.environ.get('BUNDLE_OUTPUTS', '1').lower() in ['1', 'true'],
        KEEP_INDIVIDUAL_OUTPUTS=os.environ.get('KEEP_INDIVIDUAL_OUTPUTS', '1').lower() in ['1', 'true'],
        LOG_PATH=os.environ.get('LOG_PATH', 'log.yml'),
        BIOSIMULATORS_API_ENDPOINT=os.environ.get('BIOSIMULATORS_API_ENDPOINT', 'https://api.biosimulators.org/'),
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
