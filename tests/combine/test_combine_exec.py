from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.combine.io import CombineArchiveWriter
from unittest import mock
import datetime
import dateutil.tz
import os
import shutil
import tempfile
import unittest


class ExecCombineTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_1(self):
        updated = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        archive = CombineArchive(
            contents=[
                CombineArchiveContent(
                    location='sim.sedml',
                    format='http://identifiers.org/combine.specifications/sed-ml',
                    updated=updated,
                ),
                CombineArchiveContent(
                    location='model.xml',
                    format='http://identifiers.org/combine.specifications/sbml',
                    updated=updated,
                ),
            ],
            updated=updated,
        )

        in_dir = os.path.join(self.tmp_dir, 'archive')
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        CombineArchiveWriter().run(archive, in_dir, archive_filename)

        def sed_task_executer(task, variables):
            pass

        out_dir = os.path.join(self.tmp_dir, 'outputs')

        def exec_doc(filename, working_dir, task_executer, out_dir, apply_xml_model_changes=False):
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')

        with mock.patch('biosimulators_utils.sedml.exec.exec_doc', side_effect=exec_doc):
            exec_sedml_docs_in_archive(archive_filename, sed_task_executer, out_dir)

        self.assertEqual(os.listdir(out_dir), ['sim'])
        self.assertEqual(os.listdir(os.path.join(out_dir, 'sim')), ['report1.csv', 'report2.csv'])
        with open(os.path.join(out_dir, 'sim', 'report1.csv'), 'r') as file:
            self.assertEqual(file.read(), 'ABC')
        with open(os.path.join(out_dir, 'sim', 'report2.csv'), 'r') as file:
            self.assertEqual(file.read(), 'DEF')

    def test_2(self):
        updated = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        archive = CombineArchive(
            contents=[
                CombineArchiveContent(
                    location='dir1/dir2/sim.sedml',
                    format='http://identifiers.org/combine.specifications/sed-ml',
                    updated=updated,
                ),
                CombineArchiveContent(
                    location='model.xml',
                    format='http://identifiers.org/combine.specifications/sbml',
                    updated=updated,
                ),
            ],
            updated=updated,
        )

        in_dir = os.path.join(self.tmp_dir, 'archive')
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        CombineArchiveWriter().run(archive, in_dir, archive_filename)

        def sed_task_executer(task, variables):
            pass

        out_dir = os.path.join(self.tmp_dir, 'outputs')

        def exec_doc(filename, working_dir, task_executer, out_dir, apply_xml_model_changes=False):
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')

        with mock.patch('biosimulators_utils.sedml.exec.exec_doc', side_effect=exec_doc):
            exec_sedml_docs_in_archive(archive_filename, sed_task_executer, out_dir)

        self.assertEqual(os.listdir(out_dir), ['dir1'])
        self.assertEqual(os.listdir(os.path.join(out_dir, 'dir1')), ['dir2'])
        self.assertEqual(os.listdir(os.path.join(out_dir, 'dir1', 'dir2')), ['sim'])
        self.assertEqual(os.listdir(os.path.join(out_dir, 'dir1', 'dir2', 'sim')), ['report1.csv', 'report2.csv'])
        with open(os.path.join(out_dir, 'dir1', 'dir2', 'sim', 'report1.csv'), 'r') as file:
            self.assertEqual(file.read(), 'ABC')
        with open(os.path.join(out_dir, 'dir1', 'dir2', 'sim', 'report2.csv'), 'r') as file:
            self.assertEqual(file.read(), 'DEF')
