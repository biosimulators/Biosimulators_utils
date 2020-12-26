from biosimulators_utils.report.data_model import DataGeneratorVariableResults, OutputResults, ReportFormat
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import exec
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml import utils
from lxml import etree
from unittest import mock
import numpy
import numpy.testing
import os
import pandas
import shutil
import tempfile
import unittest


class ExecTaskCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(
            id='model1',
            source='model1.xml',
            language='urn:sedml:language:sbml',
        ))
        doc.models.append(data_model.Model(
            id='model2',
            source='model1.xml',
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
                data_model.DataGeneratorVariable(
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
                data_model.DataGeneratorVariable(
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
                data_model.DataGeneratorVariable(
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
                data_model.DataGeneratorVariable(
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
                    data_generator=doc.data_generators[1],
                ),
            ],
        ))

        doc.outputs.append(data_model.Report(
            id='report_2',
            data_sets=[
                data_model.DataSet(
                    id='dataset_3',
                    label='dataset_3',
                    data_generator=doc.data_generators[2],
                ),
                data_model.DataSet(
                    id='dataset_4',
                    label='dataset_4',
                    data_generator=doc.data_generators[3],
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)

        def execute_task(task, variables):
            results = DataGeneratorVariableResults()
            if task.id == 'task_1_ss':
                results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
                results[doc.data_generators[1].variables[0].id] = numpy.array((2.,))
            else:
                results[doc.data_generators[2].variables[0].id] = numpy.array((3., 4., 5., 6., 7., 8.))
                results[doc.data_generators[3].variables[0].id] = numpy.array((9., 10., 11., 12., 13., 14.))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        output_results, var_results = exec.exec_doc(filename, os.path.dirname(
            filename), execute_task, out_dir, report_formats=[ReportFormat.csv], plot_formats=[])

        expected_var_results = DataGeneratorVariableResults({
            doc.data_generators[0].variables[0].id: numpy.array((1.,)),
            doc.data_generators[1].variables[0].id: numpy.array((2.,)),
            doc.data_generators[2].variables[0].id: numpy.array((3.,  4.,  5.,  6.,  7.,  8.)),
            doc.data_generators[3].variables[0].id: numpy.array((9., 10., 11., 12., 13., 14.)),
        })
        self.assertEqual(sorted(var_results.keys()), sorted(expected_var_results.keys()))
        for key in var_results.keys():
            numpy.testing.assert_equal(var_results[key], expected_var_results[key])

        expected_output_results = OutputResults({
            doc.outputs[0].id: pandas.DataFrame(
                numpy.array([
                    numpy.array((1., )),
                    numpy.array((2., )),
                ]),
                index=['dataset_1', 'dataset_2'],
            ),
            doc.outputs[1].id: pandas.DataFrame(
                numpy.array([
                    numpy.array((3.,  4.,  5.,  6.,  7.,  8.)),
                    numpy.array((9., 10., 11., 12., 13., 14.)),
                ]),
                index=['dataset_3', 'dataset_4'],
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
        shutil.rmtree(out_dir)
        exec.exec_doc(filename, os.path.dirname(filename), execute_task, out_dir, report_formats=[ReportFormat.h5], plot_formats=[])

        df = ReportReader().run(out_dir, doc.outputs[0].id, format=ReportFormat.h5)
        self.assertTrue(output_results[doc.outputs[0].id].equals(df))

        df = ReportReader().run(out_dir, doc.outputs[1].id, format=ReportFormat.h5)
        self.assertTrue(output_results[doc.outputs[1].id].equals(df))

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
                data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            et = etree.parse(task.model.source)
            obj_xpath, _, attr = variables[0].target.rpartition('/@')
            obj = et.xpath(obj_xpath, namespaces={'sbml': 'http://www.sbml.org/sbml/level3/version2'})[0]
            results = DataGeneratorVariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((float(obj.get(attr)),))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')

        _, var_results = exec.exec_doc(filename, working_dir, execute_task, out_dir, apply_xml_model_changes=False)
        numpy.testing.assert_equal(var_results[doc.data_generators[0].variables[0].id], numpy.array((1., )))

        _, var_results = exec.exec_doc(filename, working_dir, execute_task, out_dir, apply_xml_model_changes=True)
        numpy.testing.assert_equal(var_results[doc.data_generators[0].variables[0].id], numpy.array((2., )))

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
                data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            return DataGeneratorVariableResults()

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(ValueError, 'must be generated for task'):
            exec.exec_doc(filename, os.path.dirname(filename), execute_task, out_dir)

        # error: unsupported type of task
        doc = data_model.SedDocument()
        doc.tasks.append(mock.Mock(
            id='task_1_ss',
        ))
        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            exec.exec_doc(doc, '.', execute_task, out_dir)

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
                data_model.DataGeneratorVariable(
                    id='data_gen_1_var_1',
                    target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
                data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            results = DataGeneratorVariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[0].variables[1].id] = numpy.array((1.,))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        exec.exec_doc(doc, '.', execute_task, out_dir)

        # error: inconsistent math
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            results = DataGeneratorVariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(ValueError, 'could not be evaluated'):
            exec.exec_doc(doc, '.', execute_task, out_dir)

        # error: variables have inconsistent shapes
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.DataGeneratorVariable(
                        id='data_gen_1_var_1',
                        target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:speces[@id='var_1']/@concentration",
                        task=doc.tasks[0],
                        model=doc.models[0],
                    ),
                    data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            results = DataGeneratorVariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[0].variables[1].id] = numpy.array((1., 2.))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(ValueError, 'must have consistent shape'):
            exec.exec_doc(doc, '.', execute_task, out_dir)

        # error: data generators have inconsistent shapes
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.DataGeneratorVariable(
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
                    data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            results = DataGeneratorVariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
            results[doc.data_generators[1].variables[0].id] = numpy.array((1., 2.))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(ValueError, 'must have consistent shape'):
            exec.exec_doc(doc, '.', execute_task, out_dir)

        # warning: data set labels are not unique
        doc.data_generators = [
            data_model.DataGenerator(
                id='data_gen_1',
                variables=[
                    data_model.DataGeneratorVariable(
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
                    data_model.DataGeneratorVariable(
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

        def execute_task(task, variables):
            results = DataGeneratorVariableResults()
            results[doc.data_generators[0].variables[0].id] = numpy.array((1., 2.))
            results[doc.data_generators[1].variables[0].id] = numpy.array((2., 3.))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(data_model.IllogicalSedmlWarning, 'should have unique ids'):
            exec.exec_doc(doc, '.', execute_task, out_dir)

        # error: unsupported outputs
        doc.outputs = [
            data_model.Plot2D(
                id='plot_2d',
            ),
            data_model.Plot3D(
                id='plot_3d',
            ),
        ]

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertWarnsRegex(data_model.SedmlFeatureNotSupportedWarning, 'skipped because outputs of type'):
            exec.exec_doc(doc, '.', execute_task, out_dir)

        # error: unsupported outputs
        doc.outputs = [
            None
        ]

        out_dir = os.path.join(self.tmp_dir, 'results')
        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            exec.exec_doc(doc, '.', execute_task, out_dir)
