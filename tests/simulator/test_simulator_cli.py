from biosimulators_utils.log.data_model import CombineArchiveLog
from biosimulators_utils.simulator.cli import build_cli
from biosimulators_utils.simulator.environ import ENVIRONMENT_VARIABLES
import capturer
import sys
import unittest


class CliTestCase(unittest.TestCase):
    def setUp(self):
        def exec_sedml_docs_in_combine_archive(archive_filename, outputs_dirname, config=None):
            if archive_filename:
                print(archive_filename)
            if outputs_dirname:
                raise Exception(outputs_dirname)
            return None, CombineArchiveLog()
        self.App = build_cli('test-simulator', '4.5.6',
                             'Test Simulator', '1.2.3', 'https://test-simulator.org',
                             exec_sedml_docs_in_combine_archive,
                             environment_variables=ENVIRONMENT_VARIABLES.values())

    def test_help(self):
        with self.assertRaises(SystemExit) as cm:
            with self.App(argv=['-h']) as app:
                app.run()
            self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            with self.App(argv=['--help']) as app:
                app.run()
            self.assertEqual(cm.exception.code, 0)

    def test_version(self):
        with self.App(argv=['-v']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertIn('Test Simulator: 1.2.3', stdout)
                self.assertIn('CLI: 4.5.6', stdout)
                self.assertIn('Python: {}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro), stdout)
                self.assertEqual(captured.stderr.get_text(), '')

        with self.App(argv=['--version']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertIn('Test Simulator: 1.2.3', stdout)
                self.assertIn('CLI: 4.5.6', stdout)
                self.assertIn('Python: {}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro), stdout)
                self.assertEqual(captured.stderr.get_text(), '')

    def test_exec_archive(self):
        with self.App(argv=['-i', 'path to COMBINE/OMEX archive', '-o', '']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                app.run()
                self.assertEqual(captured.stdout.get_text(), 'path to COMBINE/OMEX archive')
                self.assertEqual(captured.stderr.get_text(), '')

        with self.App(argv=['-i', '', '-o', 'path to directory to save outputs']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 'path to directory to save outputs')
                self.assertEqual(captured.stdout.get_text(), '')
                self.assertEqual(captured.stderr.get_text(), '')

    def test_error(self):
        def exec_sedml_docs_in_combine_archive(archive_filename, outputs_dirname):
            pass

        with self.assertRaises(ValueError):
            self.App = build_cli(None, '4.5.6',
                                 'Test Simulator', '1.2.3', 'https://test-simulator.org',
                                 exec_sedml_docs_in_combine_archive)

        with self.assertRaises(ValueError):
            self.App = build_cli('test-simulator', '4.5.6',
                                 None, '1.2.3', 'https://test-simulator.org',
                                 exec_sedml_docs_in_combine_archive)

        with self.assertRaises(ValueError):
            self.App = build_cli('test-simulator', '4.5.6',
                                 'Test Simulator', '1.2.3', 'https://test-simulator.org',
                                 None)
