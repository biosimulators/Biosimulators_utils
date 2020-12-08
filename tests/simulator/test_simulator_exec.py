from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent
from biosimulators_utils.simulator import exec
from unittest import mock
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
        # exec.exec_sedml_docs_in_archive_with_containerized_simulator()
        pass
