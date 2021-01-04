from biosimulators_utils.simulator import exec
from unittest import mock
import builtins
import capturer
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class SimulatorExecTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_exec_sedml_docs_in_archive_with_simulator_cli(self):
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        outputs_dir = os.path.join(self.tmp_dir, 'results')
        simulator_cmd = 'tellurium'

        def check_call(cmd):
            for i_arg, arg in enumerate(cmd):
                if arg == '-o':
                    out_dir = cmd[i_arg + 1]
                    break

            reports_filename = os.path.join(out_dir, 'reports.h5')
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(reports_filename, 'w') as file:
                file.write('ABC')

        with mock.patch('subprocess.check_call', side_effect=check_call):
            exec.exec_sedml_docs_in_archive_with_simulator_cli(archive_filename, outputs_dir, simulator_cmd)
        self.assertEqual(os.listdir(outputs_dir), ['reports.h5'])
        with open(os.path.join(outputs_dir, 'reports.h5'), 'r') as file:
            self.assertEqual(file.read(), 'ABC')

    def test_exec_sedml_docs_in_archive_with_simulator_cli_error(self):
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        outputs_dir = os.path.join(self.tmp_dir, 'results')
        simulator_cmd = 'tellurium'

        def check_call(cmd):
            raise FileNotFoundError(1, 'Not found', cmd)

        with self.assertRaisesRegex(RuntimeError, "The command 'tellurium' could not be found"):
            with mock.patch('subprocess.check_call', side_effect=check_call):
                exec.exec_sedml_docs_in_archive_with_simulator_cli(archive_filename, outputs_dir, simulator_cmd)

        def check_call(cmd):
            print(sys.stderr, 'Error details')
            raise subprocess.CalledProcessError(1, cmd, 'output', 'Unknown\nerror')

        with self.assertRaisesRegex(RuntimeError, "The command 'tellurium' could not execute the archive:\n\n  Unknown\n  error"):
            with mock.patch('subprocess.check_call', side_effect=check_call):
                exec.exec_sedml_docs_in_archive_with_simulator_cli(archive_filename, outputs_dir, simulator_cmd)

        def check_call(cmd):
            raise Exception('Other error')

        with self.assertRaisesRegex(RuntimeError, "The command 'tellurium' could not execute the archive:\n\n  Other error"):
            with mock.patch('subprocess.check_call', side_effect=check_call):
                exec.exec_sedml_docs_in_archive_with_simulator_cli(archive_filename, outputs_dir, simulator_cmd)

    def test_exec_sedml_docs_in_archive_with_containerized_simulator(self):
        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.omex')
        outputs_dir = os.path.join(self.tmp_dir, 'results')
        docker_image = 'ghcr.io/biosimulators/tellurium:latest'

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                archive_filename, outputs_dir, docker_image,
                environment={'ARG_1': 'val-1'})
            self.assertNotEqual(captured.stdout.get_text(), '')
            self.assertEqual(captured.stderr.get_text(), '')

        self.assertNotEqual(os.listdir(self.tmp_dir), [])

        with self.assertRaises(NotImplementedError):
            with mock.patch('os.name', 'nt'):
                exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                    archive_filename, outputs_dir, docker_image)

        with mock.patch('subprocess.check_call', return_value=True):
            exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                archive_filename, outputs_dir, docker_image,
                user_to_exec_within_container='my-user')

    def test_exec_sedml_docs_in_archive_with_containerized_simulator_errors(self):
        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.omex')
        outputs_dir = os.path.join(self.tmp_dir, 'results')
        docker_image = 'ghcr.io/biosimulators/tellurium:latest'

        def check_call(cmd):
            raise FileNotFoundError(1, 'Not found', cmd)

        with mock.patch('subprocess.check_call', side_effect=check_call):
            with self.assertRaises(RuntimeError):
                exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                    archive_filename, outputs_dir, docker_image)

        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'does-not-exist.omex')
        outputs_dir = os.path.join(self.tmp_dir, 'results')
        docker_image = 'ghcr.io/biosimulators/tellurium:latest'

        with self.assertRaises(RuntimeError):
            exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                archive_filename, outputs_dir, docker_image)

        def check_call(cmd):
            raise Exception('Other error')

        with mock.patch('subprocess.check_call', side_effect=check_call):
            with self.assertRaises(RuntimeError):
                exec.exec_sedml_docs_in_archive_with_containerized_simulator(
                    archive_filename, outputs_dir, docker_image)

    def test_docker_not_available(self):
        builtin_import = builtins.__import__

        def import_mock(name, *args):
            if name == 'docker':
                raise ModuleNotFoundError
            return builtin_import(name, *args)

        with mock.patch('builtins.__import__', side_effect=import_mock):
            importlib.reload(exec)

            with self.assertRaises(ModuleNotFoundError):
                exec.exec_sedml_docs_in_archive_with_containerized_simulator(None, None, None)

        importlib.reload(exec)
