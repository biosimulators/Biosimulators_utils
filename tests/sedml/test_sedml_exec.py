from biosimulators_utils.config import get_config
from biosimulators_utils.log.data_model import (
    Status, CombineArchiveLog, SedDocumentLog, TaskLog, ReportLog)
from biosimulators_utils.log import utils as log_utils
from biosimulators_utils.log.utils import init_sed_document_log
from biosimulators_utils.report.data_model import VariableResults, DataSetResults, ReportResults, ReportFormat
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.report.warnings import RepeatDataSetLabelsWarning, CannotExportMultidimensionalTableWarning
from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import exec
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml import utils
from biosimulators_utils.sedml.exceptions import SedmlExecutionError
from biosimulators_utils.sedml.warnings import (NoTasksWarning, NoOutputsWarning,
                                                InconsistentVariableShapesWarning, SedmlFeatureNotSupportedWarning)
from biosimulators_utils.viz.data_model import VizFormat
from biosimulators_utils.xml.utils import get_namespaces_with_prefixes
from lxml import etree
from unittest import mock
import builtins
import importlib
import numpy
import numpy.testing
import os
import shutil
import tempfile
import unittest


class ExecTaskCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_successful(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        ))
        doc.models.append(data_model.Model(
            id='model2',
            source='https://models.edu/model1.xml',
            language=data_model.ModelLanguage.VCML.value,
        ))

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='ss_sim',
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))
        doc.simulations.append(data_model.UniformTimeCourseSimulation(
            id='time_course_sim',
            initial_time=10.,
            output_start_time=20.,
            output_end_time=30.,
            number_of_steps=5,
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task_1_ss',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))
        doc.tasks.append(data_model.Task(
            id='task_2_time_course',
            model=doc.models[1],
            simulation=doc.simulations[1],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_1_var_1',
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_2',
            variables=[
                data_model.Variable(
                    id='data_gen_2_var_2',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_2']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_2_var_2',
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_3',
            variables=[
                data_model.Variable(
                    id='data_gen_3_var_3',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_3']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[1],
                ),
            ],
            math='data_gen_3_var_3',
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_4',
            variables=[
                data_model.Variable(
                    id='data_gen_4_var_4',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_4']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[1],
                ),
            ],
            math='data_gen_4_var_4',
        ))

        doc.outputs.append(data_model.Report(
            id='report_1',
            data_sets=[
                data_model.DataSet(
                    id='dataset_1',
                    label='dataset_1',
                    data_generator=doc.data_generators[0],
                ),
                data_model.DataSet(
                    id='dataset_2',
                    label='dataset_2',
                    data_generator=doc.data_generators[2],
                ),
            ],
        ))

        doc.outputs.append(data_model.Report(
            id='report_2',
            data_sets=[
                data_model.DataSet(
                    id='dataset_3',
                    label='dataset_3',
                    data_generator=doc.data_generators[1],
                ),
                data_model.DataSet(
                    id='dataset_4',
                    label='dataset_4',
                    data_generator=doc.data_generators[3],
                ),
            ],
        ))

        doc.outputs.append(data_model.Report(
            id='report_3',
            data_sets=[
                data_model.DataSet(
                    id='dataset_5',
                    label='dataset_5',
                    data_generator=doc.data_generators[0],
                ),
            ],
        ))

        doc.outputs.append(data_model.Report(
            id='report_4',
            data_sets=[
                data_model.DataSet(
                    id='dataset_6',
                    label='dataset_6',
                    data_generator=doc.data_generators[3],
                ),
                data_model.DataSet(
                    id='dataset_7',
                    label='dataset_7',
                    data_generator=doc.data_generators[3],
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            if task.id == 'task_1_ss':
                results[doc.data_generators[0].variables[0].id] = numpy.array((1., 2.))
                results[doc.data_generators[1].variables[0].id] = numpy.array((3., 4.))
            else:
                results[doc.data_generators[2].variables[0].id] = numpy.array((5., 6.))
                results[doc.data_generators[3].variables[0].id] = numpy.array((7., 8.))
            return results, log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: None, content=b'')):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                config = get_config()
                config.REPORT_FORMATS = [ReportFormat.csv]
                config.VIZ_FORMATS = []
                config.COLLECT_SED_DOCUMENT_RESULTS = True

                output_results, _ = exec.exec_sed_doc(exec_task, filename, working_dir,
                                                      out_dir, config=config)

        expected_output_results = ReportResults({
            doc.outputs[0].id: DataSetResults({
                'dataset_1': numpy.array((1., 2.)),
                'dataset_2': numpy.array((5., 6.)),
            }),
            doc.outputs[1].id: DataSetResults({
                'dataset_3': numpy.array((3., 4.)),
                'dataset_4': numpy.array((7., 8.)),
            }),
            doc.outputs[2].id: DataSetResults({
                'dataset_5': numpy.array((1., 2.)),
            }),
            doc.outputs[3].id: DataSetResults({
                'dataset_6': numpy.array((7., 8.)),
                'dataset_7': numpy.array((7., 8.)),
            }),
        })
        self.assertEqual(sorted(output_results.keys()), sorted(expected_output_results.keys()))
        for report_id, data_set_results in output_results.items():
            self.assertEqual(sorted(output_results[report_id].keys()), sorted(expected_output_results[report_id].keys()))
            for data_set_id in data_set_results.keys():
                numpy.testing.assert_allclose(
                    output_results[report_id][data_set_id],
                    expected_output_results[report_id][data_set_id])

        data_set_results = ReportReader().run(doc.outputs[0], out_dir, doc.outputs[0].id, format=ReportFormat.csv)
        for data_set in doc.outputs[0].data_sets:
            numpy.testing.assert_allclose(
                output_results[doc.outputs[0].id][data_set.id],
                data_set_results[data_set.id])

        data_set_results = ReportReader().run(doc.outputs[1], out_dir, doc.outputs[1].id, format=ReportFormat.csv)
        for data_set in doc.outputs[1].data_sets:
            numpy.testing.assert_allclose(
                output_results[doc.outputs[1].id][data_set.id],
                data_set_results[data_set.id])

        # save in HDF5 format
        doc.models[1].source = doc.models[0].source
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)
        shutil.rmtree(out_dir)
        with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
            config = get_config()
            config.REPORT_FORMATS = [ReportFormat.h5]
            config.VIZ_FORMATS = []
            config.COLLECT_SED_DOCUMENT_RESULTS = False

            results, _ = exec.exec_sed_doc(exec_task, filename, os.path.dirname(filename), out_dir, config=config)
        self.assertEqual(results, None)

        report_ids = ReportReader().get_ids(out_dir, format=ReportFormat.h5, type=data_model.Report)
        self.assertEqual(set(report_ids), set([doc.outputs[0].id, doc.outputs[1].id, doc.outputs[2].id, doc.outputs[3].id]))

        report_ids = ReportReader().get_ids(out_dir, format=ReportFormat.h5, type=data_model.Plot2D)
        self.assertEqual(set(report_ids), set([]))

        data_set_results = ReportReader().run(doc.outputs[0], out_dir, doc.outputs[0].id, format=ReportFormat.h5)
        for data_set in doc.outputs[0].data_sets:
            numpy.testing.assert_allclose(
                output_results[doc.outputs[0].id][data_set.id],
                data_set_results[data_set.id])

        data_set_results = ReportReader().run(doc.outputs[1], out_dir, doc.outputs[1].id, format=ReportFormat.h5)
        for data_set in doc.outputs[1].data_sets:
            numpy.testing.assert_allclose(
                output_results[doc.outputs[1].id][data_set.id],
                data_set_results[data_set.id])

        # track execution status
        shutil.rmtree(out_dir)
        log = SedDocumentLog(
            tasks={
                'task_1_ss': TaskLog(id='task_1_ss', status=Status.QUEUED),
                'task_2_time_course': TaskLog(id='task_2_time_course', status=Status.QUEUED),
            },
            outputs={
                'report_1': ReportLog(id='report_1', status=Status.QUEUED, data_sets={
                    'dataset_1': Status.QUEUED,
                    'dataset_2': Status.QUEUED,
                }),
                'report_2': ReportLog(id='report_2', status=Status.QUEUED, data_sets={
                    'dataset_3': Status.QUEUED,
                    'dataset_4': Status.QUEUED,
                }),
                'report_3': ReportLog(id='report_3', status=Status.QUEUED, data_sets={
                    'dataset_5': Status.QUEUED,
                }),
                'report_4': ReportLog(id='report_4', status=Status.QUEUED, data_sets={
                    'dataset_6': Status.QUEUED,
                    'dataset_7': Status.QUEUED,
                })
            },
        )
        log.parent = CombineArchiveLog(out_dir=out_dir)
        log.tasks['task_1_ss'].parent = log
        log.tasks['task_2_time_course'].parent = log
        log.outputs['report_1'].parent = log
        log.outputs['report_2'].parent = log
        log.outputs['report_3'].parent = log
        log.outputs['report_4'].parent = log
        with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
            config = get_config()
            config.REPORT_FORMATS = [ReportFormat.h5]
            config.VIZ_FORMATS = []
            exec.exec_sed_doc(exec_task, filename, os.path.dirname(filename), out_dir, log=log, config=config)

        expected_log = {
            'location': None,
            'status': None,
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'tasks': [
                {
                    'id': 'task_1_ss',
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.tasks['task_1_ss'].output,
                    'duration': log.tasks['task_1_ss'].duration,
                    'algorithm': None,
                    'simulatorDetails': None,
                },
                {
                    'id': 'task_2_time_course',
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.tasks['task_2_time_course'].output,
                    'duration': log.tasks['task_2_time_course'].duration,
                    'algorithm': None,
                    'simulatorDetails': None,
                },
            ],
            'outputs': [
                {
                    'id': 'report_1',
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.outputs['report_1'].output,
                    'duration': log.outputs['report_1'].duration,
                    'dataSets': [
                        {'id': 'dataset_1', 'status': 'SUCCEEDED'},
                        {'id': 'dataset_2', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'id': 'report_2',
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.outputs['report_2'].output,
                    'duration': log.outputs['report_2'].duration,
                    'dataSets': [
                        {'id': 'dataset_3', 'status': 'SUCCEEDED'},
                        {'id': 'dataset_4', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'id': 'report_3',
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.outputs['report_3'].output,
                    'duration': log.outputs['report_3'].duration,
                    'dataSets': [
                        {'id': 'dataset_5', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'id': 'report_4',
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.outputs['report_4'].output,
                    'duration': log.outputs['report_4'].duration,
                    'dataSets': [
                        {'id': 'dataset_6', 'status': 'SUCCEEDED'},
                        {'id': 'dataset_7', 'status': 'SUCCEEDED'},
                    ],
                },
            ],
        }
        actual = log.to_json()
        actual['tasks'].sort(key=lambda task: task['id'])
        actual['outputs'].sort(key=lambda output: output['id'])
        for output in actual['outputs']:
            output['dataSets'].sort(key=lambda dat_set: dat_set['id'])
        self.assertEqual(actual, expected_log)
        self.assertTrue(os.path.isfile(os.path.join(out_dir, get_config().LOG_PATH)))

    def test_with_model_changes(self):
        doc = data_model.SedDocument()

        model1 = data_model.Model(
            id='model1',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        )
        doc.models.append(model1)

        model2 = data_model.Model(
            id='model2',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
            changes=[
                data_model.ModelAttributeChange(
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Z']/@id",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    new_value="Z2",
                )
            ]
        )
        doc.models.append(model2)

        model3 = data_model.Model(
            id='model3',
            source='#model2',
            language=data_model.ModelLanguage.SBML.value,
            changes=[
                data_model.ModelAttributeChange(
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Z2']/@initialConcentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    new_value="4.0",
                ),
                data_model.ComputeModelChange(
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Z2']/@initialConcentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    parameters=[
                        data_model.Parameter(
                            id='p',
                            value=3.1,
                        ),
                    ],
                    variables=[
                        data_model.Variable(
                            id='var_Z2',
                            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Z2']/@initialConcentration",
                            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        ),
                    ],
                    math='p * var_Z2',
                ),
            ],
        )
        model3.changes[1].variables[0].model = model3
        doc.models.append(model3)

        model1.changes.append(
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                new_value="2.5",
            )
        ),
        model1.changes.append(
            data_model.ComputeModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Y']/@initialConcentration",
                target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                parameters=[
                    data_model.Parameter(id='a', value=0.2),
                    data_model.Parameter(id='b', value=2.0),
                ],
                variables=[
                    data_model.Variable(
                        id='y',
                        model=model1,
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    ),
                    data_model.Variable(
                        id='z',
                        model=model3,
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Z2']/@initialConcentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    ),
                ],
                math='a * y + b * z',
            ),
        )

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='sim1',
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_1_var_1',
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_2',
            variables=[
                data_model.Variable(
                    id='data_gen_2_var_2',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Y']/@initialConcentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_2_var_2',
        ))

        doc.outputs.append(data_model.Report(
            id='report_1',
            data_sets=[
                data_model.DataSet(
                    id='dataset_1',
                    label='dataset_1',
                    data_generator=doc.data_generators[0],
                ),
                data_model.DataSet(
                    id='dataset_2',
                    label='dataset_2',
                    data_generator=doc.data_generators[1],
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        working_dir = os.path.dirname(filename)
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        shutil.copyfile(
            os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-three-species.xml'),
            os.path.join(working_dir, 'model1.xml'))

        def exec_task(task, variables, log=None, config=None):
            et = etree.parse(task.model.source)

            results = VariableResults()
            for variable in variables:
                obj_xpath, _, attr = variable.target.rpartition('/@')
                obj = et.xpath(obj_xpath, namespaces=get_namespaces_with_prefixes(variable.target_namespaces))[0]
                results[variable.id] = numpy.array((float(obj.get(attr)),))

            return results, log

        out_dir = os.path.join(self.tmp_dir, 'results')

        config = get_config()
        config.COLLECT_SED_DOCUMENT_RESULTS = True

        with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
            report_results, _ = exec.exec_sed_doc(exec_task, filename, working_dir, out_dir,
                                                  apply_xml_model_changes=False, config=config)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[0].id], numpy.array((1., )))
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[1].id], numpy.array((2., )))

        with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
            report_results, _ = exec.exec_sed_doc(exec_task, filename, working_dir, out_dir,
                                                  apply_xml_model_changes=True, config=config)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[0].id], numpy.array((2.5, )))
        expected_value = 0.2 * 2.5 + 2.0 * 3.1 * 4.0
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[1].id], numpy.array((expected_value)))

    def test_warnings(self):
        # no tasks
        doc = data_model.SedDocument()

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)

        def exec_task(task, variables, log=None, config=None):
            return VariableResults(), log

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarns(NoTasksWarning):
            exec.exec_sed_doc(exec_task, filename, os.path.dirname(filename), out_dir)

        # no outputs
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
            changes=[
                data_model.ModelAttributeChange(
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    new_value="2.0",
                ),
            ],
        ))

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='sim1',
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.tasks.append(data_model.Task(
            id='task2',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_1_var_1',
        ))

        doc.outputs.append(data_model.Report(id='report_1', data_sets=[
            data_model.DataSet(id='data_set_1', label='data_set_1', data_generator=doc.data_generators[0]),
        ]))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        def exec_task(task, variables, log=None, config=None):
            if task.id == 'task1':
                return VariableResults({'data_gen_1_var_1': numpy.array(1.)}), log
            else:
                return VariableResults(), log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarns(NoOutputsWarning):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                exec.exec_sed_doc(exec_task, filename, working_dir, out_dir)

    def test_errors(self):
        # unsupported type of task
        doc = data_model.SedDocument()
        doc.tasks.append(mock.Mock(id='task'))
        with self.assertRaisesRegex(SedmlExecutionError, 'not supported'):
            exec.exec_sed_doc(None, doc, None, None)

        # error: variable not recorded
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        ))

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='sim1',
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_1_var_1',
        ))

        doc.outputs.append(data_model.Report(
            id='report_1',
            data_sets=[
                data_model.DataSet(
                    id='dataset_1',
                    label='dataset_1',
                    data_generator=doc.data_generators[0],
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        def exec_task(task, variables, log=None, config=None):
            return VariableResults(), log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        # error: unsupported type of task
        doc = data_model.SedDocument()
        doc.tasks.append(mock.Mock(
            id='task_1_ss',
        ))
        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(SedmlExecutionError, 'not supported'):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                exec.exec_sed_doc(exec_task, doc, '.', out_dir)

        # error: unsupported data generators
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        ))

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='sim1',
        ))

        doc.tasks.append(data_model.Task(
            id='task1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
                data_model.Variable(
                    id='data_gen_1_var_2',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_1_var_1 * data_gen_1_var_2',
        ))

        doc.outputs.append(data_model.Report(
            id='report_1',
            data_sets=[
                data_model.DataSet(
                    id='dataset_1',
                    label='dataset_1',
                    data_generator=doc.data_generators[0],
                ),
            ],
        ))

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[0].variables[1].id] = numpy.array((1.,))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        exec.exec_sed_doc(exec_task, doc, working_dir, out_dir)

        # error: inconsistent math
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='xx',
            ),
        ]
        doc.outputs = [
            data_model.Report(
                id='report_1',
                data_sets=[
                    data_model.DataSet(
                        id='dataset_1',
                        label='dataset_1',
                        data_generator=doc.data_generators[0],
                    ),
                ]
            )
        ]

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(SedmlExecutionError, 'could not be evaluated'):
            exec.exec_sed_doc(exec_task, doc, working_dir, out_dir)

        # error: variables have inconsistent shapes
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                    data_model.Variable(
                        id='data_gen_1_var_2',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_2']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='data_gen_1_var_1 * data_gen_1_var_2',
            ),
        ]

        doc.outputs = [
            data_model.Report(
                id='report_1',
                data_sets=[
                    data_model.DataSet(
                        id='dataset_1',
                        label='dataset_1',
                        data_generator=doc.data_generators[0],
                    ),
                ],
            ),
        ]

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[0].variables[1].id] = numpy.array((1., 2.))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(InconsistentVariableShapesWarning, 'do not have consistent shapes'):
            exec.exec_sed_doc(exec_task, doc, working_dir, out_dir)

        # error: data generators have inconsistent shapes
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='data_gen_1_var_1',
            ),
            data_model.DataGenerator(
                id='data_gen_2',
                variables=[
                    data_model.Variable(
                        id='data_gen_2_var_2',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_2']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='data_gen_2_var_2',
            ),
            data_model.DataGenerator(
                id='data_gen_3',
                variables=[
                    data_model.Variable(
                        id='data_gen_3_var_3',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_3']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='data_gen_3_var_3',
            ),
        ]

        doc.outputs = [
            data_model.Report(
                id='report_1',
                data_sets=[
                    data_model.DataSet(
                        id='dataset_1',
                        label='dataset_1',
                        data_generator=doc.data_generators[0],
                    ),
                    data_model.DataSet(
                        id='dataset_2',
                        label='dataset_2',
                        data_generator=doc.data_generators[1],
                    ),
                ],
            ),
        ]

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[1].variables[0].id] = numpy.array((1., 2.))
            results[doc.data_generators[2].variables[0].id] = numpy.array(((1., 2., 3.), (4., 5., 6.), (7., 8., 9.)))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        config = get_config()
        config.COLLECT_SED_DOCUMENT_RESULTS = True
        with self.assertWarnsRegex(UserWarning, 'do not have consistent shapes'):
            report_results, _ = exec.exec_sed_doc(exec_task, doc, working_dir, out_dir, config=config)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[0].id], numpy.array((1.)))
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[1].id], numpy.array((1., 2.)))

        doc.outputs[0].data_sets.append(
            data_model.DataSet(
                id='dataset_3',
                label='dataset_3',
                data_generator=doc.data_generators[2],
            ),
        )

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results2')
        config = get_config()
        config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
        with self.assertWarnsRegex(CannotExportMultidimensionalTableWarning, 'Multidimensional reports cannot be exported to CSV'):
            exec.exec_sed_doc(exec_task, doc, working_dir, out_dir, config=config)
        with self.assertWarnsRegex(UserWarning, 'do not have consistent shapes'):
            exec.exec_sed_doc(exec_task, doc, working_dir, out_dir, config=config)

        with self.assertWarnsRegex(UserWarning, 'do not have consistent shapes'):
            config = get_config()
            config.REPORT_FORMATS = [ReportFormat.h5]
            config.VIZ_FORMATS = []
            config.COLLECT_SED_DOCUMENT_RESULTS = True
            report_results, _ = exec.exec_sed_doc(exec_task, doc, working_dir, out_dir, config=config)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[0].id],
                                   numpy.array((1.,)))
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[1].id],
                                   numpy.array((1., 2.)))
        numpy.testing.assert_equal(report_results[doc.outputs[0].id][doc.outputs[0].data_sets[2].id],
                                   numpy.array(((1., 2., 3.), (4., 5., 6.), (7., 8., 9.))))

        # warning: data set labels are not unique
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='data_gen_1_var_1',
            ),
            data_model.DataGenerator(
                id='data_gen_2',
                variables=[
                    data_model.Variable(
                        id='data_gen_2_var_2',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                        task=doc.tasks[0],
                    ),
                ],
                math='data_gen_2_var_2',
            ),
        ]

        doc.outputs = [
            data_model.Report(
                id='report_1',
                data_sets=[
                    data_model.DataSet(
                        id='dataset_1',
                        label='dataset_label',
                        data_generator=doc.data_generators[0],
                    ),
                    data_model.DataSet(
                        id='dataset_2',
                        label='dataset_label',
                        data_generator=doc.data_generators[1],
                    ),
                ],
            ),
        ]

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1., 2.))
            results[doc.data_generators[1].variables[0].id] = numpy.array((2., 3.))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        config = get_config()
        config.REPORT_FORMATS = [ReportFormat.h5, ReportFormat.csv]
        with self.assertWarnsRegex(RepeatDataSetLabelsWarning, 'should have unique labels'):
            exec.exec_sed_doc(exec_task, doc, working_dir, out_dir, config=config)

        # error: unsupported outputs
        doc.outputs = [
            mock.Mock(id='unsupported')
        ]

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        log = SedDocumentLog(tasks={}, outputs={})
        for task in doc.tasks:
            log.tasks[task.id] = TaskLog(parent=log)
        for output in doc.outputs:
            log.outputs[output.id] = ReportLog(parent=log)
        with self.assertRaisesRegex(SedmlExecutionError, 'are not supported'):
            exec.exec_sed_doc(exec_task, doc, working_dir, out_dir, log=log)

    def test_2d_plot(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        ))

        doc.simulations.append(data_model.UniformTimeCourseSimulation(
            id='sim',
            initial_time=0.,
            output_start_time=10.,
            output_end_time=10.,
            number_of_steps=10,
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.tasks.append(data_model.Task(
            id='task2',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_time',
            variables=[
                data_model.Variable(
                    id='time',
                    symbol=data_model.Symbol.time,
                    task=doc.tasks[0],
                ),
            ],
            math='time',
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_var',
            variables=[
                data_model.Variable(
                    id='var',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[1],
                ),
            ],
            math='var',
        ))

        doc.outputs.append(data_model.Plot2D(
            id='plot_2d_1',
            curves=[
                data_model.Curve(
                    id='curve1',
                    x_data_generator=doc.data_generators[0],
                    y_data_generator=doc.data_generators[0],
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                ),
                data_model.Curve(
                    id='curve2',
                    x_data_generator=doc.data_generators[1],
                    y_data_generator=doc.data_generators[1],
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                ),
            ],
        ))

        doc.outputs.append(data_model.Plot2D(
            id='plot_2d_2',
            curves=[
                data_model.Curve(
                    id='curve3',
                    x_data_generator=doc.data_generators[1],
                    y_data_generator=doc.data_generators[1],
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.linspace(0., 10., 10 + 1)
            results[doc.data_generators[1].variables[0].id] = 2 * results[doc.data_generators[0].variables[0].id]
            return results, log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        config = get_config()
        config.VIZ_FORMATS = [VizFormat.pdf]
        with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
            _, log = exec.exec_sed_doc(exec_task, filename, working_dir,
                                       out_dir, config=config)

        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_2d_1.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_2d_2.pdf')))

        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'reports.h5')))
        report_ids = ReportReader().get_ids(out_dir, format=ReportFormat.h5, type=data_model.Plot2D)
        self.assertEqual(set(report_ids), set(['plot_2d_1', 'plot_2d_2']))

        self.assertEqual(
            log.to_json()['outputs'],
            [
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][0]['output'],
                    'duration': log.to_json()['outputs'][0]['duration'],
                    'id': 'plot_2d_1',
                    'curves': [
                        {'id': 'curve1', 'status': 'SUCCEEDED'},
                        {'id': 'curve2', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][1]['output'],
                    'duration': log.to_json()['outputs'][1]['duration'],
                    'id': 'plot_2d_2',
                    'curves': [
                        {'id': 'curve3', 'status': 'SUCCEEDED'},
                    ],
                },
            ]
        )

        os.remove(os.path.join(out_dir, 'plot_2d_1.pdf'))
        os.remove(os.path.join(out_dir, 'plot_2d_2.pdf'))

        # error with a curve
        doc.data_generators[0].math = 'time * var'
        io.SedmlSimulationWriter().run(doc, filename, validate_semantics=False, validate_models_with_languages=False)
        log = init_sed_document_log(doc)

        config = get_config()
        config.VIZ_FORMATS = [VizFormat.pdf]

        with self.assertRaisesRegex(SedmlExecutionError, "name 'var' is not defined"):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                with mock.patch('biosimulators_utils.sedml.validation.validate_calculation', return_value=([], [])):
                    exec.exec_sed_doc(exec_task, filename, working_dir,
                                      out_dir, log=log, config=config)

        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_2d_1.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_2d_2.pdf')))

        self.assertEqual(
            log.to_json()['outputs'],
            [
                {
                    'status': 'FAILED',
                    'exception': log.to_json()['outputs'][0]['exception'],
                    'skipReason': None,
                    'output': log.to_json()['outputs'][0]['output'],
                    'duration': log.to_json()['outputs'][0]['duration'],
                    'id': 'plot_2d_1',
                    'curves': [
                        {'id': 'curve1', 'status': 'FAILED'},
                        {'id': 'curve2', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][1]['output'],
                    'duration': log.to_json()['outputs'][1]['duration'],
                    'id': 'plot_2d_2',
                    'curves': [
                        {'id': 'curve3', 'status': 'SUCCEEDED'},
                    ],
                },
            ]
        )

        # error with a task
        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = None
            results[doc.data_generators[1].variables[0].id] = 2 * numpy.linspace(0., 10., 10 + 1)
            return results, log

        doc.data_generators[0].math = 'time'
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)
        log = init_sed_document_log(doc)

        config = get_config()
        config.VIZ_FORMATS = [VizFormat.pdf]

        with self.assertRaisesRegex(SedmlExecutionError, "Some generators could not be produced:"):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                exec.exec_sed_doc(exec_task, filename, working_dir,
                                  out_dir, log=log, config=config)

        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_2d_1.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_2d_2.pdf')))

        self.assertEqual(
            log.to_json()['outputs'],
            [
                {
                    'status': 'FAILED',
                    'exception': log.to_json()['outputs'][0]['exception'],
                    'skipReason': None,
                    'output': log.to_json()['outputs'][0]['output'],
                    'duration': log.to_json()['outputs'][0]['duration'],
                    'id': 'plot_2d_1',
                    'curves': [
                        {'id': 'curve1', 'status': 'FAILED'},
                        {'id': 'curve2', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][1]['output'],
                    'duration': log.to_json()['outputs'][1]['duration'],
                    'id': 'plot_2d_2',
                    'curves': [
                        {'id': 'curve3', 'status': 'SUCCEEDED'},
                    ],
                },
            ]
        )

    def test_3d_plot(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        ))

        doc.simulations.append(data_model.UniformTimeCourseSimulation(
            id='sim',
            initial_time=0.,
            output_start_time=10.,
            output_end_time=10.,
            number_of_steps=10,
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task1',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.tasks.append(data_model.Task(
            id='task2',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_time',
            variables=[
                data_model.Variable(
                    id='time',
                    symbol=data_model.Symbol.time,
                    task=doc.tasks[0],
                ),
            ],
            math='time',
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_var',
            variables=[
                data_model.Variable(
                    id='var',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[1],
                ),
            ],
            math='var',
        ))

        doc.outputs.append(data_model.Plot3D(
            id='plot_3d_1',
            surfaces=[
                data_model.Surface(
                    id='surface1',
                    x_data_generator=doc.data_generators[0],
                    y_data_generator=doc.data_generators[0],
                    z_data_generator=doc.data_generators[0],
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                    z_scale=data_model.AxisScale.linear,
                ),
                data_model.Surface(
                    id='surface2',
                    x_data_generator=doc.data_generators[1],
                    y_data_generator=doc.data_generators[1],
                    z_data_generator=doc.data_generators[1],
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                    z_scale=data_model.AxisScale.linear,
                ),
            ],
        ))

        doc.outputs.append(data_model.Plot3D(
            id='plot_3d_2',
            surfaces=[
                data_model.Surface(
                    id='surface3',
                    x_data_generator=doc.data_generators[1],
                    y_data_generator=doc.data_generators[1],
                    z_data_generator=doc.data_generators[1],
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                    z_scale=data_model.AxisScale.linear,
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            x = numpy.arange(-5, 5, 0.25)
            x, _ = numpy.meshgrid(x, x)
            results[doc.data_generators[0].variables[0].id] = x
            results[doc.data_generators[1].variables[0].id] = x
            return results, log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')

        config = get_config()
        config.VIZ_FORMATS = [VizFormat.pdf]

        with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
            _, log = exec.exec_sed_doc(exec_task, filename, working_dir,
                                       out_dir, config=config)

        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_3d_1.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_3d_2.pdf')))

        self.assertEqual(
            log.to_json()['outputs'],
            [
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][0]['output'],
                    'duration': log.to_json()['outputs'][0]['duration'],
                    'id': 'plot_3d_1',
                    'surfaces': [
                        {'id': 'surface1', 'status': 'SUCCEEDED'},
                        {'id': 'surface2', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][1]['output'],
                    'duration': log.to_json()['outputs'][1]['duration'],
                    'id': 'plot_3d_2',
                    'surfaces': [
                        {'id': 'surface3', 'status': 'SUCCEEDED'},
                    ],
                },
            ]
        )

        os.remove(os.path.join(out_dir, 'plot_3d_1.pdf'))
        os.remove(os.path.join(out_dir, 'plot_3d_2.pdf'))

        # error with a surface
        doc.data_generators[0].math = 'time * var'
        io.SedmlSimulationWriter().run(doc, filename, validate_semantics=False, validate_models_with_languages=False)
        log = init_sed_document_log(doc)

        config = get_config()
        config.VIZ_FORMATS = [VizFormat.pdf]

        with self.assertRaisesRegex(SedmlExecutionError, "name 'var' is not defined"):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                with mock.patch('biosimulators_utils.sedml.validation.validate_calculation', return_value=([], [])):
                    exec.exec_sed_doc(exec_task, filename, working_dir,
                                      out_dir, log=log, config=config)

        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_3d_1.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, 'plot_3d_2.pdf')))

        self.assertEqual(
            log.to_json()['outputs'],
            [
                {
                    'status': 'FAILED',
                    'exception': log.to_json()['outputs'][0]['exception'],
                    'skipReason': None,
                    'output': log.to_json()['outputs'][0]['output'],
                    'duration': log.to_json()['outputs'][0]['duration'],
                    'id': 'plot_3d_1',
                    'surfaces': [
                        {'id': 'surface1', 'status': 'FAILED'},
                        {'id': 'surface2', 'status': 'SUCCEEDED'},
                    ],
                },
                {
                    'status': 'SUCCEEDED',
                    'exception': None,
                    'skipReason': None,
                    'output': log.to_json()['outputs'][1]['output'],
                    'duration': log.to_json()['outputs'][1]['duration'],
                    'id': 'plot_3d_2',
                    'surfaces': [
                        {'id': 'surface3', 'status': 'SUCCEEDED'},
                    ],
                },
            ]
        )

    def test_exec_repeated_task(self):
        # Tests
        # - Multiple subtasks
        # - Nested repeated tasks
        # - UniformRange, VectorRange, FunctionalRange
        # - Multiple models
        # - Set value changes

        doc = data_model.SedDocument()

        model1 = data_model.Model(id='model1', source='model1.xml', language=data_model.ModelLanguage.SBML.value)
        model2 = data_model.Model(id='model2', source='model2.xml', language=data_model.ModelLanguage.SBML.value)
        doc.models.append(model1)
        doc.models.append(model2)

        sim = data_model.UniformTimeCourseSimulation(
            id='sim', initial_time=0., output_start_time=0., output_end_time=10., number_of_steps=10)
        doc.simulations.append(sim)

        task1 = data_model.Task(id='task1', model=model1, simulation=sim)
        task2 = data_model.Task(id='task2', model=model2, simulation=sim)
        doc.tasks.append(task1)
        doc.tasks.append(task2)

        repeated_task1 = data_model.RepeatedTask(id='repeated_task1', reset_model_for_each_iteration=True)
        repeated_task2 = data_model.RepeatedTask(id='repeated_task2', reset_model_for_each_iteration=False)
        doc.tasks.append(repeated_task1)
        doc.tasks.append(repeated_task2)

        repeated_task1.range = data_model.UniformRange(
            id='uniform_range',
            start=0.,
            end=4.,
            number_of_steps=4,
            type=data_model.UniformRangeType.linear,
        )
        repeated_task2.range = data_model.FunctionalRange(
            id='functional_range',
            range=data_model.VectorRange(
                id='vector_range',
                values=[10., 20., 30.],
            ),
            parameters=[
                data_model.Parameter(id='p_1', value=1.5),
            ],
            math='vector_range * p_1',
        )

        repeated_task1.ranges.append(repeated_task1.range)
        repeated_task2.ranges.append(repeated_task2.range)
        repeated_task2.ranges.append(repeated_task2.range.range)

        repeated_task1.changes = [
            data_model.SetValueComputeModelChange(
                model=model1,
                target="/model/variable[@id='x']/@value",
                range=repeated_task1.range,
                parameters=[
                    data_model.Parameter(id='p_1', value=2.0)
                ],
                math='{} * p_1'.format(repeated_task1.range.id),
            ),
            data_model.SetValueComputeModelChange(
                model=model1,
                target="/model/variable[@id='x']/@value",
                range=repeated_task1.range,
                parameters=[
                    data_model.Parameter(id='p_2', value=1.0)
                ],
                variables=[
                    data_model.Variable(id='x', model=model1, target="/model/variable[@id='x']/@value"),
                ],
                math='x + p_2 + {}'.format(repeated_task1.range.id),
            )
        ]

        repeated_task2.changes = [
            data_model.SetValueComputeModelChange(
                model=model2,
                target="/model/variable[@id='a']/@value",
                range=repeated_task2.range,
                parameters=[
                    data_model.Parameter(id='p_3', value=0.1)
                ],
                variables=[
                    data_model.Variable(id='a', model=model2, target="/model/variable[@id='a']/@value"),
                ],
                math='a + p_3 + {}'.format(repeated_task2.range.id),
            ),
        ]

        sub_task1 = data_model.SubTask(task=task1, order=1)
        sub_task2 = data_model.SubTask(task=repeated_task2, order=2)
        sub_task3 = data_model.SubTask(task=task2, order=1)
        repeated_task1.sub_tasks.append(sub_task1)
        repeated_task1.sub_tasks.append(sub_task2)
        repeated_task2.sub_tasks.append(sub_task3)

        report = data_model.Report(id='report')
        doc.outputs.append(report)

        for id in ['x', 'y', 'z', 'a', 'b', 'c']:
            report.data_sets.append(
                data_model.DataSet(
                    id='data_set_' + id,
                    data_generator=data_model.DataGenerator(
                        id='data_gen_' + id,
                        variables=[
                            data_model.Variable(
                                id=id,
                                task=repeated_task1,
                                target="/model/variable[@id='{}']/@value".format(id),
                            )
                        ],
                    ),
                ),
            )

        model_filename1 = os.path.join(self.tmp_dir, 'model1.xml')
        with open(model_filename1, 'w') as file:
            file.write('<model>')
            file.write('  <variable id="x" value="1" />')
            file.write('  <variable id="y" value="2" />')
            file.write('  <variable id="z" value="3" />')
            file.write('</model>')

        model_filename2 = os.path.join(self.tmp_dir, 'model2.xml')
        with open(model_filename2, 'w') as file:
            file.write('<model>')
            file.write('  <variable id="a" value="4" />')
            file.write('  <variable id="b" value="5" />')
            file.write('  <variable id="c" value="6" />')
            file.write('</model>')

        model_etrees = {
            model1.id: etree.parse(model_filename1),
            model2.id: etree.parse(model_filename2),
        }

        def task_executer(task, variables, log=None, config=None):
            et = etree.parse(task.model.source)

            if task.id == task1.id:
                x = float(et.xpath("/model/variable[@id='x']")[0].get('value'))
                y = float(et.xpath("/model/variable[@id='y']")[0].get('value'))
                z = float(et.xpath("/model/variable[@id='z']")[0].get('value'))

                results = VariableResults()
                results['x'] = x * numpy.linspace(0., 5., 6)
                results['y'] = y * numpy.linspace(0., 5., 6)
                results['z'] = z * numpy.linspace(0., 5., 6)
                return results, None
            else:
                a = float(et.xpath("/model/variable[@id='a']")[0].get('value'))
                b = float(et.xpath("/model/variable[@id='b']")[0].get('value'))
                c = float(et.xpath("/model/variable[@id='c']")[0].get('value'))

                results = VariableResults()
                results['a'] = a * numpy.linspace(0., 5., 6)
                results['b'] = b * numpy.linspace(0., 5., 6)
                results['c'] = c * numpy.linspace(0., 5., 6)
                return results, None

        task_vars = utils.get_variables_for_task(doc, repeated_task1)
        results = exec.exec_repeated_task(repeated_task1, task_executer, task_vars, doc, model_etrees=model_etrees,
                                          apply_xml_model_changes=True)

        self.assertEqual(set(results.keys()), set(['x', 'y', 'z', 'a', 'b', 'c']))

        self.assertEqual(results['x'].shape, tuple([5, 2, 6, 1, 6]))
        self.assertEqual(numpy.count_nonzero(~numpy.isnan(results['x'])), 5 * 1 * 6)
        numpy.testing.assert_allclose(results['x'][0, 0, :, 0, 0], (1.) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['x'][1, 0, :, 0, 0], (4.) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['x'][2, 0, :, 0, 0], (7.) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['x'][3, 0, :, 0, 0], (10.) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['x'][4, 0, :, 0, 0], (13.) * numpy.linspace(0., 5., 6))

        numpy.testing.assert_allclose(results['z'][0, 0, :, 0, 0], 3. * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['z'][4, 0, :, 0, 0], 3. * numpy.linspace(0., 5., 6))

        self.assertEqual(results['a'].shape, tuple([5, 2, 6, 1, 6]))
        self.assertEqual(numpy.count_nonzero(~numpy.isnan(results['a'])), 5 * 1 * 3 * 6)
        numpy.testing.assert_allclose(results['a'][0, 1, 0, 0, :], (19.1) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['a'][2, 1, 1, 0, :], (49.2) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['a'][4, 1, 2, 0, :], (94.3) * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['c'][0, 1, 0, 0, :], 6. * numpy.linspace(0., 5., 6))
        numpy.testing.assert_allclose(results['c'][4, 1, 2, 0, :], 6. * numpy.linspace(0., 5., 6))

        with self.assertRaisesRegex(NotImplementedError, 'non-XML-encoded models are not supported.'):
            exec.exec_repeated_task(repeated_task1, task_executer, task_vars, doc, model_etrees=model_etrees,
                                    apply_xml_model_changes=False)

        repeated_task1.changes[0].symbol = 'symbol'
        with self.assertRaisesRegex(NotImplementedError, 'changes of symbols is not supported.'):
            exec.exec_repeated_task(repeated_task1, task_executer, task_vars, doc, model_etrees=model_etrees,
                                    apply_xml_model_changes=True)

        repeated_task1.changes[0].symbol = None
        repeated_task1.sub_tasks.append(data_model.SubTask(order=0, task=mock.Mock(id='task0')))
        with self.assertRaisesRegex(NotImplementedError, 'are not supported.'):
            exec.exec_repeated_task(repeated_task1, task_executer, task_vars, doc, model_etrees=model_etrees,
                                    apply_xml_model_changes=True)

        repeated_task1.sub_tasks.pop()
        repeated_task1.sub_tasks.append(repeated_task1.sub_tasks[-1])
        with self.assertWarnsRegex(SedmlFeatureNotSupportedWarning, 'Only independent execution of sub-tasks is supported'):
            results = exec.exec_repeated_task(repeated_task1, task_executer, task_vars, doc, model_etrees=model_etrees,
                                              apply_xml_model_changes=True)

        with self.assertWarnsRegex(SedmlFeatureNotSupportedWarning,
                                   'Only independent execution of iterations of repeated tasks is supported'):
            results = exec.exec_repeated_task(repeated_task1, task_executer, task_vars, doc, model_etrees=model_etrees,
                                              apply_xml_model_changes=True)

    def test_exec_sed_doc_with_repeated_task(self):
        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model', source='model.xml', language=data_model.ModelLanguage.SBML.value))
        doc.simulations.append(data_model.UniformTimeCourseSimulation(id='sim',
                                                                      initial_time=0., output_start_time=0.,
                                                                      output_end_time=5., number_of_steps=5))
        doc.tasks.append(data_model.Task(id='task1', model=doc.models[0], simulation=doc.simulations[0]))
        doc.tasks.append(data_model.RepeatedTask(id='task2',
                                                 range=data_model.VectorRange(values=[1., 2., 3.]),
                                                 sub_tasks=[data_model.SubTask(order=0, task=doc.tasks[0])],
                                                 reset_model_for_each_iteration=True,
                                                 ))
        doc.tasks[1].ranges.append(doc.tasks[1].range)

        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_x',
                variables=[data_model.Variable(id='x', task=doc.tasks[1], target="/model/variable[@id='x']/@value")],
                math='x',
            ),
            data_model.DataGenerator(
                id='data_gen_y',
                variables=[data_model.Variable(id='y', task=doc.tasks[1], target="/model/variable[@id='x']/@value")],
                math='y',
            ),
        ]
        doc.outputs.append(
            data_model.Report(
                id='report',
                data_sets=[
                    data_model.DataSet(id='data_set_x', label='x', data_generator=doc.data_generators[0]),
                    data_model.DataSet(id='data_set_y', label='y', data_generator=doc.data_generators[1]),
                ]
            )
        )

        model_filename1 = os.path.join(self.tmp_dir, 'model.xml')
        with open(model_filename1, 'w') as file:
            file.write('<model>')
            file.write('  <variable id="x" value="1" />')
            file.write('  <variable id="y" value="2" />')
            file.write('  <variable id="z" value="3" />')
            file.write('</model>')

        def task_executer(task, variables, log=None, config=None):
            results = VariableResults({
                'x': numpy.linspace(10., 15., 6),
                'y': numpy.linspace(20., 25., 6),
            })
            return results, log

        config = get_config()
        config.REPORT_FORMATS = [ReportFormat.h5]
        config.VIZ_FORMATS = []
        config.COLLECT_SED_DOCUMENT_RESULTS = True
        results, _ = exec.exec_sed_doc(task_executer, doc, self.tmp_dir, self.tmp_dir, apply_xml_model_changes=True,
                                       config=config)
        self.assertEqual(set(results.keys()), set(['report']))
        self.assertEqual(set(results['report'].keys()), set(['data_set_x', 'data_set_y']))
        numpy.testing.assert_allclose(results['report']['data_set_x'], [[numpy.linspace(10., 15., 6)]] * 3)
        numpy.testing.assert_allclose(results['report']['data_set_y'], [[numpy.linspace(20., 25., 6)]] * 3)

    def test_capturer_not_available(self):
        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model', source='model.xml', language=data_model.ModelLanguage.SBML.value))
        doc.simulations.append(data_model.UniformTimeCourseSimulation(id='sim',
                                                                      initial_time=0., output_start_time=0.,
                                                                      output_end_time=5., number_of_steps=5))
        doc.tasks.append(data_model.Task(id='task1', model=doc.models[0], simulation=doc.simulations[0]))

        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_x',
                variables=[data_model.Variable(id='x', task=doc.tasks[0], target="/model/variable[@id='x']/@value")],
                math='x',
            ),
        ]
        doc.outputs.append(
            data_model.Report(
                id='report',
                data_sets=[
                    data_model.DataSet(id='data_set_x', label='x', data_generator=doc.data_generators[0]),
                ]
            )
        )

        model_filename1 = os.path.join(self.tmp_dir, 'model.xml')
        with open(model_filename1, 'w') as file:
            file.write('<model>')
            file.write('  <variable id="x" value="1" />')
            file.write('</model>')

        def task_executer(task, variables, log=None, config=None):
            results = VariableResults({
                'x': numpy.linspace(10., 15., 6),
            })
            return results, log

        builtin_import = builtins.__import__

        def import_mock(name, *args):
            if name == 'capturer':
                raise ModuleNotFoundError
            return builtin_import(name, *args)

        with mock.patch('builtins.__import__', side_effect=import_mock):
            importlib.reload(log_utils)

            _, log = exec.exec_sed_doc(task_executer, doc, self.tmp_dir, self.tmp_dir)

        for task_log in log.tasks.values():
            self.assertNotEqual(task_log.output, None)
        for output_log in log.outputs.values():
            self.assertNotEqual(output_log.output, None)
        self.assertEqual(log.output, None)

        importlib.reload(log_utils)

    def test_exec_without_log(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language=data_model.ModelLanguage.SBML.value,
        ))

        doc.simulations.append(data_model.UniformTimeCourseSimulation(
            id='time_course_sim',
            initial_time=10.,
            output_start_time=20.,
            output_end_time=30.,
            number_of_steps=5,
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
        ))

        doc.tasks.append(data_model.Task(
            id='task_time_course',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    target_namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'},
                    task=doc.tasks[0],
                ),
            ],
            math='data_gen_1_var_1',
        ))

        doc.outputs.append(data_model.Report(
            id='report_1',
            data_sets=[
                data_model.DataSet(
                    id='dataset_1',
                    label='dataset_1',
                    data_generator=doc.data_generators[0],
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename, validate_models_with_languages=False)

        def exec_task(task, variables, log=None, config=None):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1., 2.))
            return results, log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        config = get_config()
        config.REPORT_FORMATS = [ReportFormat.h5]
        config.VIZ_FORMATS = []
        config.COLLECT_SED_DOCUMENT_RESULTS = True

        out_dir = os.path.join(self.tmp_dir, 'results')
        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: None, content=b'')):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                output_results, log = exec.exec_sed_doc(exec_task, filename, working_dir, out_dir, config=config)

        expected_output_results = ReportResults({
            doc.outputs[0].id: DataSetResults({
                'dataset_1': numpy.array((1., 2.)),
            }),
        })
        self.assertEqual(sorted(output_results.keys()), sorted(expected_output_results.keys()))
        for report_id, data_set_results in output_results.items():
            self.assertEqual(sorted(output_results[report_id].keys()), sorted(expected_output_results[report_id].keys()))
            for data_set_id in data_set_results.keys():
                numpy.testing.assert_allclose(
                    output_results[report_id][data_set_id],
                    expected_output_results[report_id][data_set_id])

        data_set_results = ReportReader().run(doc.outputs[0], out_dir, doc.outputs[0].id, format=ReportFormat.h5)
        for data_set in doc.outputs[0].data_sets:
            numpy.testing.assert_allclose(
                output_results[doc.outputs[0].id][data_set.id],
                data_set_results[data_set.id])

        self.assertNotEqual(log, None)

        # don't collect results
        config.REPORT_FORMATS = []
        config.COLLECT_SED_DOCUMENT_RESULTS = False
        config.LOG = False
        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: None, content=b'')):
            with mock.patch('biosimulators_utils.model_lang.sbml.validation.validate_model', return_value=([], [], None)):
                output_results, log = exec.exec_sed_doc(exec_task, filename, working_dir, out_dir, config=config)
        self.assertEqual(output_results, None)
        self.assertEqual(log, None)
