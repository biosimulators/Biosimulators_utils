from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import exec
from biosimulators_utils.sedml import io
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
            datasets=[
                data_model.Dataset(
                    id='dataset_1',
                    label='dataset_1',
                    data_generator=doc.data_generators[0],
                ),
                data_model.Dataset(
                    id='dataset_2',
                    label='dataset_2',
                    data_generator=doc.data_generators[1],
                ),
            ],
        ))

        doc.outputs.append(data_model.Report(
            id='report_2',
            datasets=[
                data_model.Dataset(
                    id='dataset_3',
                    label='dataset_3',
                    data_generator=doc.data_generators[2],
                ),
                data_model.Dataset(
                    id='dataset_4',
                    label='dataset_4',
                    data_generator=doc.data_generators[3],
                ),
            ],
        ))

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)

        def execute_task(task, variables):
            results = data_model.DataGeneratorVariableResults()
            if task.id == 'task_1_ss':
                results[doc.data_generators[0].variables[0].id] = numpy.array((1.,))
                results[doc.data_generators[1].variables[0].id] = numpy.array((2.,))
            else:
                results[doc.data_generators[2].variables[0].id] = numpy.array((3., 4., 5., 6., 7., 8.))
                results[doc.data_generators[3].variables[0].id] = numpy.array((9., 10., 11., 12., 13., 14.))
            return results

        out_dir = os.path.join(self.tmp_dir, 'results')
        output_results, var_results = exec.exec_doc(filename, execute_task, out_dir)

        expected_var_results = data_model.DataGeneratorVariableResults({
            doc.data_generators[0].variables[0].id: numpy.array((1.,)),
            doc.data_generators[1].variables[0].id: numpy.array((2.,)),
            doc.data_generators[2].variables[0].id: numpy.array((3.,  4.,  5.,  6.,  7.,  8.)),
            doc.data_generators[3].variables[0].id: numpy.array((9., 10., 11., 12., 13., 14.)),
        })
        self.assertEqual(sorted(var_results.keys()), sorted(expected_var_results.keys()))
        for key in var_results.keys():
            numpy.testing.assert_equal(var_results[key], expected_var_results[key])

        expected_output_results = data_model.OutputResults({
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
