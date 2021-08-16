from biosimulators_utils.config import get_config, get_app_dirs
from biosimulators_utils.report.data_model import ReportFormat
from biosimulators_utils.viz.data_model import VizFormat
from unittest import mock
import os
import unittest


class ConfigTestCase(unittest.TestCase):
    def test_get_config(self):
        with mock.patch.dict(os.environ, {'REPORT_FORMATS': '', 'VIZ_FORMATS': ''}):
            config = get_config()
        self.assertEqual(config.REPORT_FORMATS, [])
        self.assertEqual(config.VIZ_FORMATS, [])

        with mock.patch.dict(os.environ, {'REPORT_FORMATS': 'h5', 'VIZ_FORMATS': 'pdf'}):
            config = get_config()
        self.assertEqual(config.REPORT_FORMATS, [ReportFormat.h5])
        self.assertEqual(config.VIZ_FORMATS, [VizFormat.pdf])

    def test_get_app_dirs(self):
        self.assertIn('BioSimulatorsUtils', get_app_dirs().user_data_dir)
