from biosimulators_utils.archive.io import ArchiveReader
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.combine.warnings import NoSedmlWarning
from biosimulators_utils.plot.data_model import PlotFormat
from biosimulators_utils.report.data_model import ReportFormat
from biosimulators_utils.sedml.data_model import SedDocument
from biosimulators_utils.sedml.io import SedmlSimulationReader
from unittest import mock
import datetime
import dateutil.tz
import os
import functools
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

        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir,
                     rel_path, apply_xml_model_changes=False, report_formats=None, plot_formats=None,
                     indent=0, exec_status=None):
            out_dir = os.path.join(base_out_dir, rel_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')
            with open(os.path.join(base_out_dir, 'reports.h5'), 'w') as file:
                file.write('DEF')

        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                           report_formats=[ReportFormat.h5, ReportFormat.csv],
                                           plot_formats=[],
                                           bundle_outputs=True, keep_individual_outputs=True)

        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['reports.h5', 'reports.zip', 'sim.sedml', 'status.yml']))
        self.assertEqual(sorted(os.listdir(os.path.join(out_dir, 'sim.sedml'))),
                         sorted(['report1.csv', 'report2.csv']))

        archive.contents[0].format = 'unknown'
        CombineArchiveWriter().run(archive, in_dir, archive_filename)
        with self.assertWarnsRegex(NoSedmlWarning, 'does not contain any executing SED-ML files'):
            with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                           report_formats=[ReportFormat.h5, ReportFormat.csv],
                                           plot_formats=[],
                                           bundle_outputs=True, keep_individual_outputs=True)

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

        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir, rel_path='.',
                     apply_xml_model_changes=False, report_formats=[ReportFormat.csv], plot_formats=[PlotFormat.pdf],
                     indent=0, exec_status=None):
            out_dir = os.path.join(base_out_dir, rel_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')
            with open(os.path.join(out_dir, 'plot1.pdf'), 'w') as file:
                file.write('GHI')
            with open(os.path.join(out_dir, 'plot2.pdf'), 'w') as file:
                file.write('JKL')

        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                           bundle_outputs=True, keep_individual_outputs=True)

        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['reports.zip', 'plots.zip', 'dir1', 'status.yml']))
        self.assertEqual(os.listdir(os.path.join(out_dir, 'dir1')), ['dir2'])
        self.assertEqual(os.listdir(os.path.join(out_dir, 'dir1', 'dir2')), ['sim.sedml'])
        self.assertEqual(sorted(os.listdir(os.path.join(out_dir, 'dir1', 'dir2', 'sim.sedml'))),
                         sorted(['report1.csv', 'report2.csv', 'plot1.pdf', 'plot2.pdf']))

        archive_dir = os.path.join(self.tmp_dir, 'archive')

        archive = ArchiveReader().run(os.path.join(out_dir, 'reports.zip'), archive_dir)
        self.assertEqual(sorted(file.archive_path for file in archive.files), sorted([
            'dir1/dir2/sim.sedml/report1.csv',
            'dir1/dir2/sim.sedml/report2.csv',
        ]))
        with open(os.path.join(archive_dir, 'dir1', 'dir2', 'sim.sedml', 'report1.csv'), 'r') as file:
            self.assertEqual(file.read(), 'ABC')
        with open(os.path.join(archive_dir, 'dir1', 'dir2', 'sim.sedml', 'report2.csv'), 'r') as file:
            self.assertEqual(file.read(), 'DEF')

        archive = ArchiveReader().run(os.path.join(out_dir, 'plots.zip'), archive_dir)
        self.assertEqual(sorted(file.archive_path for file in archive.files), sorted([
            'dir1/dir2/sim.sedml/plot1.pdf',
            'dir1/dir2/sim.sedml/plot2.pdf',
        ]))
        with open(os.path.join(archive_dir, 'dir1', 'dir2', 'sim.sedml', 'plot1.pdf'), 'r') as file:
            self.assertEqual(file.read(), 'GHI')
        with open(os.path.join(archive_dir, 'dir1', 'dir2', 'sim.sedml', 'plot2.pdf'), 'r') as file:
            self.assertEqual(file.read(), 'JKL')

        # don't bundle outputs, don't keep individual outputs
        out_dir = os.path.join(self.tmp_dir, 'outputs-2')
        os.makedirs(out_dir)
        os.makedirs(os.path.join(out_dir, 'dir1'))
        with open(os.path.join(out_dir, 'extra-file'), 'w'):
            pass
        with open(os.path.join(out_dir, 'dir1', 'extra-file'), 'w'):
            pass
        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                           bundle_outputs=False, keep_individual_outputs=False)
        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['status.yml', 'extra-file', 'dir1']))
        self.assertEqual(sorted(os.listdir(os.path.join(out_dir, 'dir1'))), sorted(['extra-file']))

        out_dir = os.path.join(self.tmp_dir, 'outputs-3')
        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir)
        self.assertIn('status.yml', os.listdir(out_dir))

    def test_error(self):
        updated = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        archive = CombineArchive(
            contents=[
                CombineArchiveContent(
                    location='/dir1/dir2/sim.sedml',
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

        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir, rel_path='.',
                     apply_xml_model_changes=False, report_formats=[ReportFormat.csv], plot_formats=[],
                     indent=0, exec_status=None):
            out_dir = os.path.join(base_out_dir, rel_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')
