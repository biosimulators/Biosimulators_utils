from biosimulators_utils.biosimulations.data_model import Metadata
from biosimulators_utils.sedml import data_model
from biosimulators_utils.utils.core import none_sorted
import copy
import unittest


class DataModelTestCase(unittest.TestCase):
    def test(self):
        model = data_model.Model(
            id='model1',
            name='Model1',
            source='model.sbml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'a\']/@id', new_value='234'),
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id', new_value='432'),
                data_model.AddElementModelChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id', new_elements='432'),
                data_model.ReplaceElementModelChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id', new_elements='432'),
                data_model.RemoveElementModelChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id'),
                data_model.ComputeModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/@id',
                    parameters=[
                        data_model.Parameter(id='p_1', value=1.5),
                        data_model.Parameter(id='p_2', value=2.5),
                    ],
                    variables=[
                        data_model.Variable(
                            id='v_1',
                            model=None,
                            target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='param_1']",
                        ),
                        data_model.Variable(
                            id='v_1',
                            model=None,
                            target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='param_1']",
                        ),
                    ],
                    math='p_1 * v_1 + p_2 * v_2',
                ),
            ],
        )
        for var in model.changes[-1].variables:
            var.model = model

        ss_simulation = data_model.SteadyStateSimulation(
            id='simulation1',
            name='Simulation1',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000001', new_value='1.234'),
                ]),
        )

        one_step_simulation = data_model.OneStepSimulation(
            id='simulation1',
            name='Simulation1',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000001', new_value='1.234'),
                ]),
            step=10.)

        time_course_simulation = data_model.UniformTimeCourseSimulation(
            id='simulation1',
            name='Simulation1',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000001', new_value='1.234'),
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000002', new_value='4.321'),
                ]),
            initial_time=10.,
            output_start_time=20.,
            output_end_time=30,
            number_of_steps=10)

        task = data_model.Task(id='task1', name='Task1', model=model, simulation=time_course_simulation)
        for var in model.changes[-1].variables:
            var.task = task

        report = data_model.Report(
            id='report1',
            name='Report1',
            data_sets=[
                data_model.DataSet(
                    id='dataset1',
                    name='Dataset1',
                    label='Dataset-1',
                    data_generator=data_model.DataGenerator(
                        id='dataGen1',
                        name='DataGen1',
                        variables=[
                            data_model.Variable(
                                id='DataGenVar1', name='DataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task, model=model)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='DataGenParam1', name='DataGenParam1', value=2.)
                        ],
                        math='DataGenVar1 - DataGenParam1',
                    )
                ),
            ],
        )

        plot2d = data_model.Plot2D(
            name='Plot2D',
            curves=[
                data_model.Curve(
                    id='curve1', name='Curve1',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen1',
                        name='XDataGen1',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar1', name='XDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task, model=model)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar1 * xDataGenParam1',
                    ),
                    y_data_generator=None,
                ),
                data_model.Curve(
                    id='curve2', name='Curve2',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    x_data_generator=None,
                    y_data_generator=data_model.DataGenerator(
                        id='yDataGen1',
                        name='yDataGen1',
                        variables=[
                            data_model.Variable(
                                id='yDataGenVar1', name='YDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task, model=model)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='yDataGenParam1', name='YDataGenParam1', value=2.)
                        ],
                        math='yDataGenParam1 + YDataGenParam1',
                    ),
                ),
            ]
        )

        plot3d = data_model.Plot3D(
            name='Plot3D',
            surfaces=[
                data_model.Surface(
                    id='curve1', name='Curve1',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    z_scale=data_model.AxisScale.linear,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen1',
                        name='XDataGen1',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar1', name='XDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task, model=model)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar1 * xDataGenParam1',
                    ),
                    y_data_generator=None,
                    z_data_generator=None,
                ),
                data_model.Surface(
                    id='curve2',
                    name='Curve2',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    z_scale=data_model.AxisScale.log,
                    x_data_generator=None,
                    y_data_generator=None,
                    z_data_generator=data_model.DataGenerator(
                        id='zDataGen1',
                        name='zDataGen1',
                        variables=[
                            data_model.Variable(
                                id='zDataGenVar1', name='ZDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task, model=model)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='zDataGenParam1', name='ZDataGenParam1', value=2.)
                        ],
                        math='zDataGenParam1 / ZDataGenParam1',
                    ),
                ),
            ]
        )

        document = data_model.SedDocument(
            level=1,
            version=3,
            models=[model],
            simulations=[ss_simulation, one_step_simulation, time_course_simulation],
            tasks=[task],
            data_generators=[plot2d.curves[0].x_data_generator],
            outputs=[report, plot2d, plot3d],
            metadata=Metadata(),
        )

        self.assertEqual(
            ss_simulation.to_tuple(),
            (
                ss_simulation.id,
                ss_simulation.name,
                (
                    ss_simulation.algorithm.kisao_id,
                    (
                        (
                            ss_simulation.algorithm.changes[0].kisao_id,
                            ss_simulation.algorithm.changes[0].new_value,
                        ),
                    ),
                ),
            )
        )

        self.assertEqual(
            one_step_simulation.to_tuple(),
            (
                one_step_simulation.id,
                one_step_simulation.name,
                (
                    one_step_simulation.algorithm.kisao_id,
                    (
                        (
                            one_step_simulation.algorithm.changes[0].kisao_id,
                            one_step_simulation.algorithm.changes[0].new_value,
                        ),
                    ),
                ),
                one_step_simulation.step
            )
        )

        self.assertEqual(report.to_tuple()[0], report.id)
        self.assertEqual(plot2d.to_tuple()[2][0][4], plot2d.curves[0].x_data_generator.id)

        self.assertEqual(document.to_tuple(), (
            document.level,
            document.version,
            (model.to_tuple(),),
            tuple(none_sorted((ss_simulation.to_tuple(), one_step_simulation.to_tuple(), time_course_simulation.to_tuple()))),
            (task.to_tuple(),),
            (plot2d.curves[0].x_data_generator.to_tuple(),),
            tuple(none_sorted((report.to_tuple(), plot2d.to_tuple(), plot3d.to_tuple()))),
            document.metadata.to_tuple(),
        ))

        change = model.changes[0]
        change2 = copy.deepcopy(change)
        self.assertTrue(change.is_equal(change2))
        change2.target = None
        self.assertFalse(change.is_equal(change2))

        change = model.changes[-1]
        change2 = copy.deepcopy(change)
        self.assertTrue(change.is_equal(change2))
        change2 = copy.deepcopy(change)
        change2.target = None
        self.assertFalse(change.is_equal(change2))
        change2 = copy.deepcopy(change)
        change2.parameters[0].value = -1
        self.assertFalse(change.is_equal(change2))
        change2 = copy.deepcopy(change)
        change2.variables[0].id = 'variable_1'
        self.assertFalse(change.is_equal(change2))
        change2 = copy.deepcopy(change)
        change2.variables[0].model.id = 'different_model'
        self.assertFalse(change.is_equal(change2))
        change2 = copy.deepcopy(change)
        change2.math = 'x * y'
        self.assertFalse(change.is_equal(change2))

        model2 = copy.deepcopy(model)
        self.assertTrue(model.is_equal(model2))
        model2.id = None
        self.assertFalse(model.is_equal(model2))

        alg_change = time_course_simulation.algorithm.changes[0]
        alg_change_2 = copy.deepcopy(alg_change)
        self.assertTrue(alg_change.is_equal(alg_change_2))
        alg_change_2.new_value = None
        self.assertFalse(alg_change.is_equal(alg_change_2))

        alg = time_course_simulation.algorithm
        alg2 = copy.deepcopy(alg)
        self.assertTrue(alg.is_equal(alg2))
        alg2.kisao_id = None
        self.assertFalse(alg.is_equal(alg2))

        one_step_simulation_2 = copy.deepcopy(one_step_simulation)
        self.assertTrue(one_step_simulation.is_equal(one_step_simulation_2))
        one_step_simulation_2.step = -1.
        self.assertFalse(one_step_simulation.is_equal(one_step_simulation_2))

        time_course_simulation_2 = copy.deepcopy(time_course_simulation)
        self.assertTrue(time_course_simulation.is_equal(time_course_simulation_2))
        time_course_simulation_2.initial_time = -1.
        self.assertFalse(time_course_simulation.is_equal(time_course_simulation_2))

        task2 = copy.deepcopy(task)
        self.assertTrue(task.is_equal(task2))
        task2.id = None
        self.assertFalse(task.is_equal(task2))

        var = copy.deepcopy(report.data_sets[0].data_generator.variables[0])
        var2 = copy.deepcopy(var)
        self.assertTrue(var.is_equal(var2))
        var2.target = None
        self.assertFalse(var.is_equal(var2))

        data_generator = copy.deepcopy(report.data_sets[0].data_generator)
        data_generator_2 = copy.deepcopy(data_generator)
        self.assertTrue(data_generator.is_equal(data_generator_2))
        data_generator_2.variables = []
        self.assertFalse(data_generator.is_equal(data_generator_2))

        data_set = copy.deepcopy(report.data_sets[0])
        data_set_2 = copy.deepcopy(data_set)
        self.assertTrue(data_set.is_equal(data_set_2))
        data_set_2.label = None
        self.assertFalse(data_set.is_equal(data_set_2))

        report2 = copy.deepcopy(report)
        self.assertTrue(report.is_equal(report2))
        report2.data_sets = []
        self.assertFalse(report.is_equal(report2))

        curve = copy.deepcopy(plot2d.curves[0])
        curve2 = copy.deepcopy(curve)
        self.assertTrue(curve.is_equal(curve2))
        curve2.x_scale = None
        self.assertFalse(curve.is_equal(curve2))

        surface = copy.deepcopy(plot3d.surfaces[1])
        surface2 = copy.deepcopy(surface)
        self.assertTrue(surface.is_equal(surface2))
        surface2.z_data_generator = None
        self.assertFalse(surface.is_equal(surface2))

        plot2d_2 = copy.deepcopy(plot2d)
        self.assertTrue(plot2d.is_equal(plot2d_2))
        plot2d_2.curves = []
        self.assertFalse(plot2d.is_equal(plot2d_2))

        plot3d_2 = copy.deepcopy(plot3d)
        self.assertTrue(plot3d.is_equal(plot3d_2))
        plot3d_2.name = None
        self.assertFalse(plot3d.is_equal(plot3d_2))

        document_2 = copy.deepcopy(document)
        self.assertTrue(document.is_equal(document_2))
        document_2.models = []
        self.assertFalse(document.is_equal(document_2))

    def test_uniform_time_course_number_of_points(self):
        sim = data_model.UniformTimeCourseSimulation(number_of_steps=10)
        self.assertEqual(sim.number_of_steps, 10)
        self.assertEqual(sim.number_of_points, 10)

        sim = data_model.UniformTimeCourseSimulation(number_of_points=20)
        self.assertEqual(sim.number_of_steps, 20)
        self.assertEqual(sim.number_of_points, 20)

        with self.assertRaises(ValueError):
            data_model.UniformTimeCourseSimulation(number_of_steps=10, number_of_points=20)

        sim.number_of_points = 20
        self.assertEqual(sim.number_of_steps, 20)
        sim.number_of_steps = 30
        self.assertEqual(sim.number_of_points, 30)

    def test_uniform_range_number_of_points(self):
        range = data_model.UniformRange(number_of_steps=10)
        self.assertEqual(range.number_of_steps, 10)
        self.assertEqual(range.number_of_points, 10)

        range = data_model.UniformRange(number_of_points=20)
        self.assertEqual(range.number_of_steps, 20)
        self.assertEqual(range.number_of_points, 20)

        with self.assertRaises(ValueError):
            data_model.UniformRange(number_of_steps=10, number_of_points=20)

        range.number_of_points = 20
        self.assertEqual(range.number_of_steps, 20)
        range.number_of_steps = 30
        self.assertEqual(range.number_of_points, 30)
