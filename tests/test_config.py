from biosimulators_utils.config import get_config
from biosimulators_utils.plot.data_model import PlotFormat
from biosimulators_utils.report.data_model import ReportFormat
import mock
import os
import unittest


class ConfigTestCase(unittest.TestCase):
    def test(self):
        with mock.patch.dict(os.environ, {'REPORT_FORMATS': '', 'PLOT_FORMATS': ''}):
            config = get_config()
        self.assertEqual(config.REPORT_FORMATS, [])
        self.assertEqual(config.PLOT_FORMATS, [])

        with mock.patch.dict(os.environ, {'REPORT_FORMATS': 'h5', 'PLOT_FORMATS': 'pdf'}):
            config = get_config()
        self.assertEqual(config.REPORT_FORMATS, [ReportFormat.h5])
        self.assertEqual(config.PLOT_FORMATS, [PlotFormat.pdf])
