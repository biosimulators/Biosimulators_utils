""" Common configuration for simulation tools

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-29
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum
import os

__all__ = ['Config', 'get_config', 'Colors']


class Config(object):
    """ Configuration

    Attributes:
        ALGORITHM_SUBSTITUTION_POLICY (:obj:`str`): algorithm substition policy
        REPORT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate reports in
        PLOT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate plots in
        H5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
        REPORTS_PATH (:obj:`str`): path to save zip archive of reports relative to base output directory
        PLOTS_PATH (:obj:`str`): path to save zip archive of plots relative to base output directory
        BUNDLE_OUTPUTS (:obj:`bool`): indicates whether bundles of report and plot outputs should be produced
        KEEP_INDIVIDUAL_OUTPUTS (:obj:`bool`): indicates whether the individual output files should be kept
        LOG_PATH (:obj:`str`): path to save the execution status of a COMBINE/OMEX archive
        BIOSIMULATORS_API_ENDPOINT (:obj:`str`): URL for BioSimulators API
        VERBOSE (:obj:`bool`): whether to display the detailed output of the execution of each task
    """

    def __init__(self, ALGORITHM_SUBSTITUTION_POLICY, REPORT_FORMATS, PLOT_FORMATS,
                 H5_REPORTS_PATH, REPORTS_PATH, PLOTS_PATH, BUNDLE_OUTPUTS, KEEP_INDIVIDUAL_OUTPUTS,
                 LOG_PATH, BIOSIMULATORS_API_ENDPOINT, VERBOSE):
        """
        Args:
            ALGORITHM_SUBSTITUTION_POLICY (:obj:`str`): algorithm substition policy
            REPORT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate reports in
            PLOT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate plots in
            H5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
            REPORTS_PATH (:obj:`str`): path to save zip archive of reports relative to base output directory
            PLOTS_PATH (:obj:`str`): path to save zip archive of plots relative to base output directory
            BUNDLE_OUTPUTS (:obj:`bool`): indicates whether bundles of report and plot outputs should be produced
            KEEP_INDIVIDUAL_OUTPUTS (:obj:`bool`): indicates whether the individual output files should be kept
            LOG_PATH (:obj:`str`): path to save the execution status of a COMBINE/OMEX archive
            BIOSIMULATORS_API_ENDPOINT (:obj:`str`): URL for BioSimulators API
            VERBOSE (:obj:`bool`): whether to display the detailed output of the execution of each task
        """
        self.ALGORITHM_SUBSTITUTION_POLICY = ALGORITHM_SUBSTITUTION_POLICY
        self.REPORT_FORMATS = REPORT_FORMATS
        self.PLOT_FORMATS = PLOT_FORMATS
        self.H5_REPORTS_PATH = H5_REPORTS_PATH
        self.REPORTS_PATH = REPORTS_PATH
        self.PLOTS_PATH = PLOTS_PATH
        self.BUNDLE_OUTPUTS = BUNDLE_OUTPUTS
        self.KEEP_INDIVIDUAL_OUTPUTS = KEEP_INDIVIDUAL_OUTPUTS
        self.LOG_PATH = LOG_PATH
        self.BIOSIMULATORS_API_ENDPOINT = BIOSIMULATORS_API_ENDPOINT
        self.VERBOSE = VERBOSE


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

    plot_formats = os.environ.get('PLOT_FORMATS', 'pdf').strip()
    if plot_formats:
        plot_formats = [format.strip().lower() for format in plot_formats.split(',')]
    else:
        plot_formats = []

    return Config(
        ALGORITHM_SUBSTITUTION_POLICY=os.environ.get('ALGORITHM_SUBSTITUTION_POLICY', 'SIMILAR_VARIABLES'),
        REPORT_FORMATS=report_formats,
        PLOT_FORMATS=plot_formats,
        H5_REPORTS_PATH=os.environ.get('H5_REPORTS_PATH', 'reports.h5'),
        REPORTS_PATH=os.environ.get('REPORTS_PATH', 'reports.zip'),
        PLOTS_PATH=os.environ.get('PLOTS_PATH', 'plots.zip'),
        BUNDLE_OUTPUTS=os.environ.get('BUNDLE_OUTPUTS', '1').lower() in ['1', 'true'],
        KEEP_INDIVIDUAL_OUTPUTS=os.environ.get('KEEP_INDIVIDUAL_OUTPUTS', '1').lower() in ['1', 'true'],
        LOG_PATH=os.environ.get('LOG_PATH', 'log.yml'),
        BIOSIMULATORS_API_ENDPOINT=os.environ.get('BIOSIMULATORS_API_ENDPOINT', 'https://api.biosimulators.org/'),
        VERBOSE=os.environ.get('VERBOSE', '1').lower() in ['1', 'true'],
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
