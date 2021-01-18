from biosimulators_utils.config import get_config
from biosimulators_utils.log.data_model import (
    Status, CombineArchiveLog, SedDocumentLog, TaskLog, ReportLog)
from biosimulators_utils.report.data_model import VariableResults, OutputResults, ReportFormat
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import exec
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml.exceptions import SedmlExecutionError
from biosimulators_utils.sedml.warnings import (NoTasksWarning, NoOutputsWarning, RepeatDataSetLabelsWarning,
                                                SedmlFeatureNotSupportedWarning, InconsistentVariableShapesWarning)
from lxml import etree
from unittest import mock
import numpy
import numpy.testing
import os
import pandas
import requests
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
            language='urn:sedml:language:sbml',
        ))
        doc.models.append(data_model.Model(
            id='model2',
            source='https://models.edu/model1.xml',
            language='urn:sedml:language:cellml',
        ))

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='ss_sim',
        ))
        doc.simulations.append(data_model.UniformTimeCourseSimulation(
            id='time_course_sim',
            initial_time=10.,
            output_start_time=20.,
            output_end_time=30.,
            number_of_points=5,
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
                    task=doc.tasks[0],
                    model=doc.models[0],
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
                    task=doc.tasks[0],
                    model=doc.models[0],
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
                    task=doc.tasks[1],
                    model=doc.models[1],
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
                    task=doc.tasks[1],
                    model=doc.models[1],
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
        io.SedmlSimulationWriter().run(doc, filename)

        def execute_task(task, variables, log):
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
            output_results, _ = exec.exec_sed_doc(execute_task, filename, working_dir,
                                                  out_dir, report_formats=[ReportFormat.csv], plot_formats=[])

        expected_output_results = OutputResults({
            doc.outputs[0].id: pandas.DataFrame(
                numpy.array([
                    numpy.array((1., 2.)),
                    numpy.array((5., 6.)),
                ]),
                index=['dataset_1', 'dataset_2'],
            ),
            doc.outputs[1].id: pandas.DataFrame(
                numpy.array([
                    numpy.array((3., 4.)),
                    numpy.array((7., 8.)),
                ]),
                index=['dataset_3', 'dataset_4'],
            ),
            doc.outputs[2].id: pandas.DataFrame(
                numpy.array([
                    numpy.array((1., 2.)),
                ]),
                index=['dataset_5'],
            ),
            doc.outputs[3].id: pandas.DataFrame(
                numpy.array([
                    numpy.array((7., 8.)),
                    numpy.array((7., 8.)),
                ]),
                index=['dataset_6', 'dataset_7'],
            ),
        })
        self.assertEqual(sorted(output_results.keys()), sorted(expected_output_results.keys()))
        for key in output_results.keys():
            self.assertTrue(output_results[key].equals(expected_output_results[key]))

        df = ReportReader().run(out_dir, doc.outputs[0].id, format=ReportFormat.csv)
        self.assertTrue(output_results[doc.outputs[0].id].equals(df))

        df = ReportReader().run(out_dir, doc.outputs[1].id, format=ReportFormat.csv)
        self.assertTrue(output_results[doc.outputs[1].id].equals(df))

        # save in HDF5 format
        doc.models[1].source = doc.models[0].source
        io.SedmlSimulationWriter().run(doc, filename)
        shutil.rmtree(out_dir)
        exec.exec_sed_doc(execute_task, filename, os.path.dirname(filename), out_dir, report_formats=[ReportFormat.h5], plot_formats=[])

        df = ReportReader().run(out_dir, doc.outputs[0].id, format=ReportFormat.h5)
        self.assertTrue(output_results[doc.outputs[0].id].equals(df))

        df = ReportReader().run(out_dir, doc.outputs[1].id, format=ReportFormat.h5)
        self.assertTrue(output_results[doc.outputs[1].id].equals(df))

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
        exec.exec_sed_doc(execute_task, filename, os.path.dirname(filename), out_dir, report_formats=[ReportFormat.h5], plot_formats=[],
                          log=log)

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

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                    new_value="2.0",
                ),
            ],
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
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                    task=doc.tasks[0],
                    model=doc.models[0],
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
        working_dir = os.path.dirname(filename)
        io.SedmlSimulationWriter().run(doc, filename)

        shutil.copyfile(
            os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-three-species.xml'),
            os.path.join(working_dir, 'model1.xml'))

        def execute_task(task, variables, log):
            et = etree.parse(task.model.source)
            obj_xpath, _, attr = variables[0].target.rpartition('/@')
            obj = et.xpath(obj_xpath, namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'})[0]
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((float(obj.get(attr)),))
            return results, log

        out_dir = os.path.join(self.tmp_dir, 'results')

        report_results, _ = exec.exec_sed_doc(execute_task, filename, working_dir, out_dir, apply_xml_model_changes=False)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[0].id, :], numpy.array((1., )))

        report_results, _ = exec.exec_sed_doc(execute_task, filename, working_dir, out_dir, apply_xml_model_changes=True)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[0].id, :], numpy.array((2., )))

    def test_warnings(self):
        # no tasks
        doc = data_model.SedDocument()

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)

        def execute_task(task, variables, log):
            return VariableResults(), log

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarns(NoTasksWarning):
            exec.exec_sed_doc(execute_task, filename, os.path.dirname(filename), out_dir)

        # no outputs
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='X']/@initialConcentration",
                    new_value="2.0",
                ),
            ],
        ))

        doc.simulations.append(data_model.SteadyStateSimulation(
            id='sim1',
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
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
            ],
            math='data_gen_1_var_1',
        ))

        doc.outputs.append(data_model.Report(id='report_1', data_sets=[
            data_model.DataSet(id='data_set_1', label='data_set_1', data_generator=doc.data_generators[0]),
        ]))

        doc.outputs.append(data_model.Plot2D(id='plot_1', curves=[
            data_model.Curve(
                id='curve_1',
                x_data_generator=doc.data_generators[0],
                y_data_generator=doc.data_generators[0],
                x_scale=data_model.AxisScale.linear,
                y_scale=data_model.AxisScale.linear,
            ),
        ]))

        doc.outputs.append(data_model.Plot3D(id='plot_2', surfaces=[
            data_model.Surface(
                id='surface_1',
                x_data_generator=doc.data_generators[0],
                y_data_generator=doc.data_generators[0],
                z_data_generator=doc.data_generators[0],
                x_scale=data_model.AxisScale.linear,
                y_scale=data_model.AxisScale.linear,
                z_scale=data_model.AxisScale.linear,
            ),
        ]))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)

        def execute_task(task, variables, log):
            if task.id == 'task1':
                return VariableResults({'data_gen_1_var_1': numpy.array(1.)}), log
            else:
                return VariableResults(), log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarns(NoOutputsWarning):
            exec.exec_sed_doc(execute_task, filename, working_dir, out_dir)

    def test_errors(self):
        # error: variable not recorded
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language='urn:sedml:language:sbml',
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
                    task=doc.tasks[0],
                    model=doc.models[0],
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
        io.SedmlSimulationWriter().run(doc, filename)

        def execute_task(task, variables, log):
            return VariableResults(), log

        working_dir = os.path.dirname(filename)
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(SedmlExecutionError, 'did not generate the following expected variables'):
            exec.exec_sed_doc(execute_task, filename, working_dir, out_dir)

        # error: unsupported type of task
        doc = data_model.SedDocument()
        doc.tasks.append(mock.Mock(
            id='task_1_ss',
        ))
        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(SedmlExecutionError, 'not supported'):
            exec.exec_sed_doc(execute_task, doc, '.', out_dir)

        # error: unsupported data generators
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language='urn:sedml:language:sbml',
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
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
                data_model.Variable(
                    id='data_gen_1_var_2',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    task=doc.tasks[0],
                    model=doc.models[0],
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

        def execute_task(task, variables, log):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[0].variables[1].id] = numpy.array((1.,))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)

        # error: inconsistent math
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        task=doc.tasks[0],
                        model=doc.models[0],
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

        def execute_task(task, variables, log):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(SedmlExecutionError, 'could not be evaluated'):
            exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)

        # error: variables have inconsistent shapes
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        task=doc.tasks[0],
                        model=doc.models[0],
                    ),
                    data_model.Variable(
                        id='data_gen_1_var_2',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_2']/@concentration",
                        task=doc.tasks[0],
                        model=doc.models[0],
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

        def execute_task(task, variables, log):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[0].variables[1].id] = numpy.array((1., 2.))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(InconsistentVariableShapesWarning, 'do not have consistent shapes'):
            exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)

        # error: data generators have inconsistent shapes
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        task=doc.tasks[0],
                        model=doc.models[0],
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
                        task=doc.tasks[0],
                        model=doc.models[0],
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
                        task=doc.tasks[0],
                        model=doc.models[0],
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

        def execute_task(task, variables, log):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[1].variables[0].id] = numpy.array((1., 2.))
            results[doc.data_generators[2].variables[0].id] = numpy.array(((1., 2., 3.), (4., 5., 6.), (7., 8., 9.)))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(UserWarning, 'do not have consistent shapes'):
            report_results, _ = exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)
        numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[0].id, :], numpy.array((1., numpy.nan)))
        numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[1].id, :], numpy.array((1., 2.)))

        # doc.outputs[0].data_sets.append(
        #    data_model.DataSet(
        #        id='dataset_3',
        #        label='dataset_3',
        #        data_generator=doc.data_generators[2],
        #    ),
        # )

        # working_dir = self.tmp_dir
        # with open(os.path.join(working_dir, doc.models[0].source), 'w'):
        #    pass

        #out_dir = os.path.join(self.tmp_dir, 'results2')
        # with self.assertWarnsRegex(UserWarning, 'do not have consistent shapes'):
        #    report_results, _ = exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)
        # numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[0].id, :],
        #    numpy.array(((1., numpy.nan, numpy.nan), (numpy.nan, numpy.nan, numpy.nan), (numpy.nan, numpy.nan, numpy.nan))))
        # numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[1].id, :],
        #    numpy.array(((1., 2., numpy.nan), (numpy.nan, numpy.nan, numpy.nan), (numpy.nan, numpy.nan, numpy.nan))))
        # numpy.testing.assert_equal(report_results[doc.outputs[0].id].loc[doc.outputs[0].data_sets[2].id, :],
        #    numpy.array(((1., 2., 3.), (4., 5., 6.), (7., 8., 9.))))

        # warning: data set labels are not unique
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.Variable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        task=doc.tasks[0],
                        model=doc.models[0],
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
                        task=doc.tasks[0],
                        model=doc.models[0],
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

        def execute_task(task, variables, log):
            results = VariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1., 2.))
            results[doc.data_generators[1].variables[0].id] = numpy.array((2., 3.))
            return results, log

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(RepeatDataSetLabelsWarning, 'should have unique ids'):
            exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)

        # error: unsupported outputs
        doc.outputs = [
            data_model.Plot2D(
                id='plot_2d',
            ),
            data_model.Plot3D(
                id='plot_3d',
            ),
        ]

        working_dir = self.tmp_dir
        with open(os.path.join(working_dir, doc.models[0].source), 'w'):
            pass

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(SedmlFeatureNotSupportedWarning, 'skipped because outputs of type'):
            exec.exec_sed_doc(execute_task, doc, working_dir, out_dir)

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
            exec.exec_sed_doc(execute_task, doc, working_dir, out_dir, log=log)
