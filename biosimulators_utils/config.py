import os

REPORT_FORMATS = [format.strip().upper() for format in os.environ.get('REPORT_FORMATS', 'CSV, HDF5').split(',')]
HDF5_REPORTS_PATH = os.environ.get('HDF5_REPORTS_PATH', 'reports.h5')
CSV_REPORTS_PATH = os.environ.get('CSV_REPORTS_PATH', 'reports.zip')
PDF_PLOTS_PATH = os.environ.get('PDF_PLOTS_PATH', 'plots.zip')
