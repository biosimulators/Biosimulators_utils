from biosimulators_utils.archive.io import ArchiveReader
from biosimulators_utils.combine import exec
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.exceptions import CombineArchiveExecutionError, NoSedmlError
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import get_config
from biosimulators_utils.log import utils as log_utils
from biosimulators_utils.report.data_model import ReportFormat, ReportResults, SedDocumentResults
from biosimulators_utils.sedml.data_model import SedDocument, Task, Report
from biosimulators_utils.sedml.io import SedmlSimulationReader
from biosimulators_utils.viz.data_model import VizFormat
from unittest import mock
import builtins
import datetime
import dateutil.tz
import os
import functools
import importlib
import re
import shutil
import tempfile
import unittest


class ExecCombineTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_1(self):
        archive = CombineArchive(
            contents=[
                CombineArchiveContent(
                    location='sim.sedml',
                    format='http://identifiers.org/combine.specifications/sed-ml',
                ),
                CombineArchiveContent(
                    location='model.xml',
                    format='http://identifiers.org/combine.specifications/sbml',
                ),
            ],
        )

        in_dir = os.path.join(self.tmp_dir, 'archive')
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        CombineArchiveWriter().run(archive, in_dir, archive_filename)

        def sed_task_executer(task, variables):
            pass

        out_dir = os.path.join(self.tmp_dir, 'outputs')

        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir,
                         rel_path, apply_xml_model_changes=False,
                         indent=0, log=None, log_level=None, config=None):
            out_dir = os.path.join(base_out_dir, rel_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')
            with open(os.path.join(base_out_dir, 'reports.h5'), 'w') as file:
                file.write('DEF')
            return ReportResults({
                'report1': 'ABC',
                'report2': 'DEF',
            }), None

        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            sed_doc = SedDocument(
                tasks=[Task(id='task_1')],
                outputs=[Report(id='output_1')],
            )
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=sed_doc):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)

                config = get_config()
                config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
                config.VIZ_FORMATS = []
                config.BUNDLE_OUTPUTS = True
                config.KEEP_INDIVIDUAL_OUTPUTS = True
                config.COLLECT_COMBINE_ARCHIVE_RESULTS = False

                results, _ = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)
                self.assertEqual(results, None)

                config.COLLECT_COMBINE_ARCHIVE_RESULTS = True
                results, _ = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)
                self.assertEqual(results, SedDocumentResults({
                    'sim.sedml': ReportResults({
                        'report1': 'ABC',
                        'report2': 'DEF',
                    })
                }))

        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['reports.h5', 'reports.zip', 'sim.sedml', 'log.yml']))
        self.assertEqual(sorted(os.listdir(os.path.join(out_dir, 'sim.sedml'))),
                         sorted(['report1.csv', 'report2.csv']))

        archive.contents[0].format = CombineArchiveContentFormat.TEXT
        CombineArchiveWriter().run(archive, in_dir, archive_filename)
        with self.assertRaisesRegex(NoSedmlError, 'does not contain any executing SED-ML files'):
            with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)

                config = get_config()
                config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
                config.VIZ_FORMATS = []
                config.BUNDLE_OUTPUTS = True
                config.KEEP_INDIVIDUAL_OUTPUTS = True
                config.DEBUG = True

                exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)

        archive.contents[0].format = 'http://identifiers.org/combine.specifications/sed-ml'
        CombineArchiveWriter().run(archive, in_dir, archive_filename)
        out_dir = os.path.join(self.tmp_dir, 'outputs-with-error')

        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir,
                         rel_path, apply_xml_model_changes=False,
                         indent=0, log=None, log_level=None, config=None):
            out_dir = os.path.join(base_out_dir, rel_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            with open(os.path.join(out_dir, 'report2.csv'), 'w') as file:
                file.write('DEF')
            with open(os.path.join(base_out_dir, 'reports.h5'), 'w') as file:
                file.write('DEF')
            raise ValueError('An error')
        sed_doc = SedDocument(
            tasks=[Task(id='task_1')],
            outputs=[Report(id='output_1')],
        )
        with mock.patch.object(SedmlSimulationReader, 'run', return_value=sed_doc):
            sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
            with self.assertRaisesRegex(CombineArchiveExecutionError, 'An error'):
                config = get_config()
                config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
                config.VIZ_FORMATS = []
                config.BUNDLE_OUTPUTS = True
                config.KEEP_INDIVIDUAL_OUTPUTS = True

                _, log = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)
                if log.exception:
                    raise log.exception

        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['reports.h5', 'reports.zip', 'sim.sedml', 'log.yml']))
        self.assertEqual(sorted(os.listdir(os.path.join(out_dir, 'sim.sedml'))),
                         sorted(['report1.csv', 'report2.csv']))

    def test_2(self):
        archive = CombineArchive(
            contents=[
                CombineArchiveContent(
                    location='dir1/dir2/sim.sedml',
                    format='http://identifiers.org/combine.specifications/sed-ml',
                ),
                CombineArchiveContent(
                    location='model.xml',
                    format='http://identifiers.org/combine.specifications/sbml',
                ),
            ],
        )

        in_dir = os.path.join(self.tmp_dir, 'archive')
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        CombineArchiveWriter().run(archive, in_dir, archive_filename)

        def sed_task_executer(task, variables):
            pass

        out_dir = os.path.join(self.tmp_dir, 'outputs')

        config = get_config()
        config.REPORT_FORMATS = [ReportFormat.csv]
        config.VIZ_FORMATS = [VizFormat.pdf]

        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir, rel_path='.',
                         apply_xml_model_changes=False,
                         indent=0, log=None, log_level=None, config=config):
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
            return None, None

        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                config = get_config()
                config.BUNDLE_OUTPUTS = True
                config.KEEP_INDIVIDUAL_OUTPUTS = True
                exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)

        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['reports.zip', 'plots.zip', 'dir1', 'log.yml']))
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
                config = get_config()
                config.BUNDLE_OUTPUTS = False
                config.KEEP_INDIVIDUAL_OUTPUTS = False
                exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)
        self.assertEqual(sorted(os.listdir(out_dir)), sorted(['log.yml', 'extra-file', 'dir1']))
        self.assertEqual(sorted(os.listdir(os.path.join(out_dir, 'dir1'))), sorted(['extra-file']))

        out_dir = os.path.join(self.tmp_dir, 'outputs-3')
        with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
            with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir)
        self.assertIn('log.yml', os.listdir(out_dir))

    def test_capturer_not_available(self):
        archive = CombineArchive(
            contents=[
                CombineArchiveContent(
                    location='dir1/dir2/sim.sedml',
                    format='http://identifiers.org/combine.specifications/sed-ml',
                ),
            ],
        )

        in_dir = os.path.join(self.tmp_dir, 'archive')
        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        CombineArchiveWriter().run(archive, in_dir, archive_filename)

        def sed_task_executer(task, variables):
            pass

        out_dir = os.path.join(self.tmp_dir, 'outputs')

        config = get_config()
        config.REPORT_FORMATS = [ReportFormat.csv]
        config.VIZ_FORMATS = []
        config.BUNDLE_OUTPUTS = True
        config.KEEP_INDIVIDUAL_OUTPUTS = True
        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir, rel_path='.',
                         apply_xml_model_changes=False,
                         indent=0, log=None, log_level=None, config=config):
            out_dir = os.path.join(base_out_dir, rel_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(os.path.join(out_dir, 'report1.csv'), 'w') as file:
                file.write('ABC')
            return None, None

        builtin_import = builtins.__import__

        def import_mock(name, *args):
            if name == 'capturer':
                raise ModuleNotFoundError
            return builtin_import(name, *args)

        with mock.patch('builtins.__import__', side_effect=import_mock):
            importlib.reload(log_utils)

            with mock.patch('biosimulators_utils.sedml.exec.exec_sed_doc', side_effect=exec_sed_doc):
                with mock.patch.object(SedmlSimulationReader, 'run', return_value=SedDocument()):
                    sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)
                    config = get_config()
                    config.BUNDLE_OUTPUTS = True
                    config.KEEP_INDIVIDUAL_OUTPUTS = True
                    _, log = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir, config=config)
        self.assertNotEqual(log.output, None)
        for doc_log in log.sed_documents.values():
            self.assertNotEqual(doc_log.output, None)

        importlib.reload(log_utils)

    def test_exec_sedml_docs_in_archive_error_handling(self):
        def exec_sed_doc(task_executer, filename, working_dir, base_out_dir,
                         rel_path, apply_xml_model_changes=False,
                         indent=0, log=None, log_level=None, config=None):
            return None, None

        def sed_task_executer(task, variables):
            pass

        sed_doc_executer = functools.partial(exec_sed_doc, sed_task_executer)

        config = get_config()
        config.DEBUG = True

        # valid archive
        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures',
                                        'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint.omex')
        exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)

        # invalid archive
        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml-validation',
                                        'invalid-omex-manifest-missing-attribute.omex')
        with self.assertRaisesRegex(ValueError, re.compile('archive is invalid.\n  - ', re.MULTILINE)):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)
        with self.assertRaisesRegex(ValueError, 'must have the required attributes'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)

        # invalid SED-ML file in archive
        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures',
                                        'sedml-validation', 'invalid-sedml-missing-attribute.omex')
        with self.assertRaisesRegex(ValueError, re.compile('archive is invalid.\n  - ', re.MULTILINE)):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)
        with self.assertRaisesRegex(ValueError, 'must have the required attributes'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)
