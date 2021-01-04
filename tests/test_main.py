from unittest import mock
import biosimulators_utils
import biosimulators_utils.__main__
import capturer
import os
import shutil
import tempfile
import unittest


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_help(self):
        with biosimulators_utils.__main__.App(argv=[]) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                app.run()
                stdout = captured.stdout.get_text()
                self.assertTrue(stdout.startswith('usage: biosimulators-utils'))
                self.assertEqual(captured.stderr.get_text(), '')

    def test_version(self):
        with biosimulators_utils.__main__.App(argv=['-v']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertEqual(stdout, biosimulators_utils.__version__)
                self.assertEqual(captured.stderr.get_text(), '')

        with biosimulators_utils.__main__.App(argv=['--version']) as app:
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with self.assertRaises(SystemExit) as cm:
                    app.run()
                    self.assertEqual(cm.exception.code, 0)
                stdout = captured.stdout.get_text()
                self.assertEqual(stdout, biosimulators_utils.__version__)
                self.assertEqual(captured.stderr.get_text(), '')

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['', '--help']):
            with self.assertRaises(SystemExit) as context:
                biosimulators_utils.__main__.main()
                self.assertRegex(context.Exception, 'usage: biosimulators-utils')

    def test_exec_modeling_project(self):
        with biosimulators_utils.__main__.App(argv=[
            'exec',
            'ghcr.io/biosimulators/copasi:latest',
            '-i', os.path.join(os.path.dirname(__file__), 'fixtures', 'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex'),
            '-o', os.path.join(self.tmp_dir, 'results'),
            '--env', 'KEY1=value1', 'KEY2=value2',
            '--user', str(os.getuid()),
        ]) as app:
            app.run()

        outputs = os.listdir(os.path.join(self.tmp_dir, 'results'))
        self.assertIn('reports.h5', outputs)

    def test_exec_modeling_project_error_handling(self):
        with self.assertRaisesRegex(SystemExit, 'must be pairs of keys and values'):
            with biosimulators_utils.__main__.App(argv=[
                'exec',
                'ghcr.io/biosimulators/tellurium:latest',
                '-i', os.path.join(os.path.dirname(__file__), 'fixtures', 'BIOMD0000000297.omex'),
                '-o', os.path.join(self.tmp_dir, 'results'),
                '--env', 'KEY1:value1', 'KEY2-value2',
                '--user', str(os.getuid()),
            ]) as app:
                app.run()
