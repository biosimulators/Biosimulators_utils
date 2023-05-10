from unittest import mock
import unittest
import os
from biosimulators_utils.config import get_config, get_app_dirs, Config
from biosimulators_utils.report.data_model import ReportFormat
from biosimulators_utils.viz.data_model import VizFormat


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


class TestConfig(unittest.TestCase):
    def test_init(self):
        with mock.patch('appdirs.user_config_dir') as mock_app_dirs:
            mock_app_dirs.return_value = '/fake/config/dir'
            config = Config(
                REPORT_FORMATS='csv',
                VIZ_FORMATS='pdf',
                CUSTOM_SETTINGS={'MY_CUSTOM_SETTING': 'my_custom_value'}
            )
            self.assertEqual(config.OMEX_METADATA_INPUT_FORMAT, 'rdfxml')
            self.assertEqual(config.OMEX_METADATA_OUTPUT_FORMAT, 'rdfxml_abbrev')
            self.assertEqual(config.OMEX_METADATA_SCHEMA, 'biosimulations')
            self.assertTrue(config.VALIDATE_OMEX_MANIFESTS)
            self.assertTrue(config.VALIDATE_SEDML)
            self.assertTrue(config.VALIDATE_SEDML_MODELS)
            self.assertTrue(config.VALIDATE_IMPORTED_MODEL_FILES)
            self.assertTrue(config.VALIDATE_OMEX_METADATA)
            self.assertTrue(config.VALIDATE_IMAGES)
            self.assertTrue(config.VALIDATE_RESULTS)
            self.assertEqual(config.ALGORITHM_SUBSTITUTION_POLICY, 'similarVariables')
            self.assertFalse(config.COLLECT_COMBINE_ARCHIVE_RESULTS)
            self.assertFalse(config.COLLECT_SED_DOCUMENT_RESULTS)
            self.assertTrue(config.SAVE_PLOT_DATA)
            self.assertEqual(config.REPORT_FORMATS, [ReportFormat.h5.value])
            self.assertEqual(config.VIZ_FORMATS, [VizFormat.pdf.value])
            self.assertEqual(config.H5_REPORTS_PATH, 'reports.h5')
            self.assertEqual(config.REPORTS_PATH, 'reports.zip')
            self.assertEqual(config.PLOTS_PATH, 'plots.zip')
            self.assertTrue(config.BUNDLE_OUTPUTS)
            self.assertTrue(config.KEEP_INDIVIDUAL_OUTPUTS)
            self.assertTrue(config.LOG)
            self.assertEqual(config.LOG_PATH, 'log.yml')
            self.assertEqual(config.BIOSIMULATORS_API_ENDPOINT, 'https://api.biosimulators.org/')
            self.assertEqual(config.BIOSIMULATIONS_API_ENDPOINT, 'https://api.biosimulations.org/')
            self.assertEqual(config.BIOSIMULATIONS_API_AUTH_ENDPOINT, 'https://auth.biosimulations.org/oauth/token')
            self.assertEqual(config.BIOSIMULATIONS_API_AUDIENCE, 'api.biosimulations.org')
            self.assertFalse(config.VERBOSE)
            self.assertFalse(config.DEBUG)
            self.assertEqual(config.STDOUT_LEVEL, 'python')
            self.assertEqual(config.CUSTOM_SETTINGS, {'MY_CUSTOM_SETTING': 'my_custom_value'})
            self.assertEqual(config.logger.handlers[0].baseFilename, '/fake/config/dir/logs/app.log')
