from biosimulators_utils.biosimulations.data_model import Metadata
from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import io
import os
import shutil
import tempfile
import unittest


class IoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        print(self.tmp_dir)
        # shutil.rmtree(self.tmp_dir)

    def test_write_read(self):
        model1 = data_model.Model(
            id='model1',
            name='Model1',
            source='model.sbml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'a\']/@id', new_value='234'),
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id', new_value='432'),
            ],
        )
        model2 = data_model.Model(
            id='model2',
            name='Model2',
            source='model.sbml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'a\']/@id', new_value='234'),
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id', new_value='432'),
            ],
        )

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
            id='simulation2',
            name='Simulation2',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000001', new_value='1.234'),
                ]),
            step=10.)

        time_course_simulation = data_model.UniformTimeCourseSimulation(
            id='simulation3',
            name='Simulation3',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000029',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000001', new_value='1.234'),
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000002', new_value='4.321'),
                ]),
            initial_time=10.,
            output_start_time=20.,
            output_end_time=30,
            number_of_points=10)

        task1 = data_model.Task(id='task1', name='Task1', model=model1, simulation=time_course_simulation)
        task2 = data_model.Task(id='task2', name='Task2', model=model2, simulation=time_course_simulation)

        report = data_model.Report(
            id='report1',
            name='Report1',
            datasets=[
                data_model.Dataset(
                    id='dataset1',
                    name='Dataset1',
                    label='Dataset-1',
                    data_generator=data_model.DataGenerator(
                        id='dataGen1',
                        name='DataGen1',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='DataGenVar1', name='DataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task1, model=model1)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='DataGenParam1', name='DataGenParam1', value=2.)
                        ],
                        math='DataGenVar1 - DataGenParam1',
                    )
                ),
            ],
        )

        plot2d = data_model.Plot2D(
            id='plot2d',
            name='Plot2D',
            curves=[
                data_model.Curve(
                    id='curve1', name='Curve1',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen2',
                        name='XDataGen2',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar1', name='XDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar1 * xDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='yDataGen3',
                        name='yDataGen3',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar1', name='XDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar1 * xDataGenParam1',
                    ),
                ),
                data_model.Curve(
                    id='curve2', name='Curve2',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    x_data_generator=data_model.DataGenerator(
                        id='yDataGen4',
                        name='yDataGen4',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='yDataGenVar1', name='YDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task1, model=model1)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='yDataGenParam1', name='YDataGenParam1', value=2.)
                        ],
                        math='yDataGenParam1 + YDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='yDataGen5',
                        name='yDataGen5',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='yDataGenVar1', name='YDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task1, model=model1)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='yDataGenParam1', name='YDataGenParam1', value=2.)
                        ],
                        math='yDataGenParam1 + YDataGenParam1',
                    ),
                ),
            ]
        )

        plot3d = data_model.Plot3D(
            id='plot3d',
            name='Plot3D',
            surfaces=[
                data_model.Surface(
                    id='curve1', name='Curve1',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    z_scale=data_model.AxisScale.linear,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen6',
                        name='XDataGen6',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='xDataGen8',
                        name='XDataGen8',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    z_data_generator=data_model.DataGenerator(
                        id='xDataGen9',
                        name='XDataGen9',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                ),
                data_model.Surface(
                    id='curve2',
                    name='Curve2',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    z_scale=data_model.AxisScale.log,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen10',
                        name='XDataGen10',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='xDataGen11',
                        name='XDataGen11',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    z_data_generator=data_model.DataGenerator(
                        id='xDataGen12',
                        name='XDataGen12',
                        variables=[
                            data_model.DataGeneratorVariable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.DataGeneratorParameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                ),
            ]
        )

        document = data_model.SedDocument(
            level=1,
            version=3,
            models=[model1],
            simulations=[time_course_simulation],
            tasks=[task1],
            data_generators=(
                [d.data_generator for d in report.datasets]
            ),
            outputs=[report],
            metadata=Metadata(
                description="description",
            ),
        )

        filename = os.path.join(self.tmp_dir, 'test.xml')
        io.SedmlSimulationWriter().run(document, filename)

        document2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(document.is_equal(document2))

        document = data_model.SedDocument(
            level=1,
            version=3,
            models=[model1, model2],
            simulations=[ss_simulation, one_step_simulation, time_course_simulation],
            tasks=[task1, task2],
            data_generators=(
                [d.data_generator for d in report.datasets]
                + [c.x_data_generator for c in plot2d.curves]
                + [c.y_data_generator for c in plot2d.curves]
                + [s.x_data_generator for s in plot3d.surfaces]
                + [s.y_data_generator for s in plot3d.surfaces]
                + [s.z_data_generator for s in plot3d.surfaces]
            ),
            outputs=[report, plot2d, plot3d],
            metadata=Metadata(
                description="description",
            ),
        )

        filename = os.path.join(self.tmp_dir, 'test.xml')
        io.SedmlSimulationWriter().run(document, filename)

        document2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(document.is_equal(document2))
