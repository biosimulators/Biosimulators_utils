from biosimulators_utils.config import get_config, get_app_dirs
from biosimulators_utils.plot.data_model import PlotFormat
from biosimulators_utils.report.data_model import ReportFormat
from unittest import mock
import os
import unittest


class ConfigTestCase(unittest.TestCase):
    def test_get_config(self):
        with mock.patch.dict(os.environ, {'REPORT_FORMATS': '', 'PLOT_FORMATS': ''}):
            config = get_config()
        self.assertEqual(config.REPORT_FORMATS, [])
        self.assertEqual(config.PLOT_FORMATS, [])

        with mock.patch.dict(os.environ, {'REPORT_FORMATS': 'h5', 'PLOT_FORMATS': 'pdf'}):
            config = get_config()
        self.assertEqual(config.REPORT_FORMATS, [ReportFormat.h5])
        self.assertEqual(config.PLOT_FORMATS, [PlotFormat.pdf])

    def test_get_app_dirs(self):
        self.assertIn('BioSimulatorsUtils', get_app_dirs().user_data_dir)
