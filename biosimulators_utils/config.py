import os


class Config(object):
    """ Configuration

    Attributes:
        REPORT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate reports in
        HDF5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
        CSV_REPORTS_PATH (:obj:`str`): path to save zip archive of reports in CSV format relative to base output directory
        PDF_PLOTS_PATH (:obj:`str`): path to save zip archive of plots in PDF format relative to base output directory
    """

    def __init__(self, REPORT_FORMATS, HDF5_REPORTS_PATH, CSV_REPORTS_PATH, PDF_PLOTS_PATH):
        """
        Args:
            REPORT_FORMATS (:obj:`list` of :obj:`str`): default formats to generate reports in
            HDF5_REPORTS_PATH (:obj:`str`): path to save reports in HDF5 format relative to base output directory
            CSV_REPORTS_PATH (:obj:`str`): path to save zip archive of reports in CSV format relative to base output directory
            PDF_PLOTS_PATH (:obj:`str`): path to save zip archive of plots in PDF format relative to base output directory
        """
        self.REPORT_FORMATS = REPORT_FORMATS
        self.HDF5_REPORTS_PATH = HDF5_REPORTS_PATH
        self.CSV_REPORTS_PATH = CSV_REPORTS_PATH
        self.PDF_PLOTS_PATH = PDF_PLOTS_PATH


def get_config():
    """ Get the configuration

    Returns:
        :obj:`Config`: configuration
    """
    return Config(
        REPORT_FORMATS=[format.strip().upper() for format in os.environ.get('REPORT_FORMATS', 'CSV, HDF5').split(',')],
        HDF5_REPORTS_PATH=os.environ.get('HDF5_REPORTS_PATH', 'reports.h5'),
        CSV_REPORTS_PATH=os.environ.get('CSV_REPORTS_PATH', 'reports.zip'),
        PDF_PLOTS_PATH=os.environ.get('PDF_PLOTS_PATH', 'plots.zip'),
    )
