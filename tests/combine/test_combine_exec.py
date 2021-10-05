from biosimulators_utils.archive.io import ArchiveReader
from biosimulators_utils.combine import exec
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.exceptions import CombineArchiveExecutionError, NoSedmlError
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import get_config
from biosimulators_utils.log import utils as log_utils
from biosimulators_utils.report.data_model import ReportFormat, ReportResults, SedDocumentResults, VariableResults
from biosimulators_utils.sedml.data_model import (SedDocument, Task, Report, Model,
                                                  ModelLanguage, UniformTimeCourseSimulation, Algorithm, Variable, DataGenerator, DataSet)
from biosimulators_utils.sedml import exec as sedml_exec
from biosimulators_utils.sedml.io import SedmlSimulationReader, SedmlSimulationWriter
from biosimulators_utils.viz.data_model import VizFormat
from unittest import mock
import builtins
import datetime
import dateutil.tz
import functools
import importlib
import numpy
import numpy.testing
import os
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
                config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
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
                config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
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

    def test_exec_sedml_docs_in_archive_without_log(self):
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

        sed_doc = SedDocument()
        model = Model(id='model_1', source='model.xml', language=ModelLanguage.SBML.value)
        sed_doc.models.append(model)
        sim = UniformTimeCourseSimulation(id='sim_1', initial_time=0., output_start_time=0., output_end_time=10., number_of_points=10,
                                          algorithm=Algorithm(kisao_id='KISAO_0000019'))
        sed_doc.simulations.append(sim)
        task = Task(id='task_1', model=model, simulation=sim)
        sed_doc.tasks.append(task)
        sed_doc.data_generators.append(DataGenerator(
            id='data_gen_1',
            variables=[
                Variable(
                    id='var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
                    task=task
                )],
            math='var_1',
        ))
        sed_doc.data_generators.append(DataGenerator(
            id='data_gen_2',
            variables=[
                Variable(
                    id='var_2',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clb']",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
                    task=task
                )],
            math='var_2',
        ))
        report = Report(id='output_1')
        sed_doc.outputs.append(report)
        report.data_sets.append(DataSet(id='data_set_1', label='data_set_1', data_generator=sed_doc.data_generators[0]))
        report.data_sets.append(DataSet(id='data_set_2', label='data_set_2', data_generator=sed_doc.data_generators[1]))

        archive_dirname = os.path.join(self.tmp_dir, 'archive')
        os.makedirs(archive_dirname)

        shutil.copyfile(
            os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml'),
            os.path.join(archive_dirname, 'model.xml'))
        SedmlSimulationWriter().run(sed_doc, os.path.join(archive_dirname, 'sim.sedml'))

        archive_filename = os.path.join(self.tmp_dir, 'archive.omex')
        CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

        def sed_task_executer(task, variables, log=None, config=None):
            if log:
                log.algorithm = task.simulation.algorithm.kisao_id
                log.simulator_details = {
                    'attrib': 'value',
                }

            return VariableResults({
                'var_1': numpy.linspace(0., 10., task.simulation.number_of_points + 1),
                'var_2': numpy.linspace(10., 20., task.simulation.number_of_points + 1),
            }), log

        def sed_task_executer_error(task, variables, log=None, config=None):
            raise ValueError('Big error')

        out_dir = os.path.join(self.tmp_dir, 'outputs')

        config = get_config()
        config.REPORT_FORMATS = []
        config.VIZ_FORMATS = []
        config.COLLECT_COMBINE_ARCHIVE_RESULTS = True
        config.LOG = True

        # with log
        sed_doc_executer = functools.partial(sedml_exec.exec_sed_doc, sed_task_executer)
        results, log = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                                       apply_xml_model_changes=False,
                                                       config=config)
        self.assertEqual(set(results.keys()), set(['sim.sedml']))
        self.assertEqual(set(results['sim.sedml'].keys()), set(['output_1']))
        self.assertEqual(set(results['sim.sedml']['output_1'].keys()), set(['data_set_1', 'data_set_2']))
        numpy.testing.assert_allclose(results['sim.sedml']['output_1']['data_set_1'], numpy.linspace(0., 10., 11))
        numpy.testing.assert_allclose(results['sim.sedml']['output_1']['data_set_2'], numpy.linspace(10., 20., 11))
        self.assertEqual(log.exception, None)
        self.assertEqual(log.sed_documents['sim.sedml'].tasks['task_1'].algorithm, task.simulation.algorithm.kisao_id)
        self.assertEqual(log.sed_documents['sim.sedml'].tasks['task_1'].simulator_details, {'attrib': 'value'})

        sed_doc_executer = functools.partial(sedml_exec.exec_sed_doc, sed_task_executer_error)
        results, log = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                                       apply_xml_model_changes=False,
                                                       config=config)
        self.assertIsInstance(log.exception, CombineArchiveExecutionError)

        config.DEBUG = True
        sed_doc_executer = functools.partial(sedml_exec.exec_sed_doc, sed_task_executer_error)
        with self.assertRaisesRegex(ValueError, 'Big error'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                            apply_xml_model_changes=False,
                                            config=config)

        # without log
        config.COLLECT_COMBINE_ARCHIVE_RESULTS = False
        config.LOG = False
        config.DEBUG = False

        sed_doc_executer = functools.partial(sedml_exec.exec_sed_doc, sed_task_executer)
        results, log = exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                                       apply_xml_model_changes=False,
                                                       config=config)
        self.assertEqual(results, None)
        self.assertEqual(log, None)

        sed_doc_executer = functools.partial(sedml_exec.exec_sed_doc, sed_task_executer_error)
        with self.assertRaisesRegex(CombineArchiveExecutionError, 'Big error'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                            apply_xml_model_changes=False,
                                            config=config)

        config.DEBUG = True
        sed_doc_executer = functools.partial(sedml_exec.exec_sed_doc, sed_task_executer_error)
        with self.assertRaisesRegex(ValueError, 'Big error'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                            apply_xml_model_changes=False,
                                            config=config)

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
        with self.assertRaisesRegex(ValueError, re.compile('is not a valid COMBINE/OMEX archive.\n  - ', re.MULTILINE)):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)
        with self.assertRaisesRegex(ValueError, 'must have the required attributes'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)

        # invalid SED-ML file in archive
        archive_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures',
                                        'sedml-validation', 'invalid-sedml-missing-attribute.omex')
        with self.assertRaisesRegex(ValueError, re.compile('is not a valid COMBINE/OMEX archive.\n  - ', re.MULTILINE)):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)
        with self.assertRaisesRegex(ValueError, 'must have the required attributes'):
            exec.exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, self.tmp_dir, config=config)
