from biosimulators_utils.data_model import Person, Identifier, OntologyTerm
from biosimulators_utils.biosimulations.data_model import Metadata, ExternalReferences, Citation
from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml import utils
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.warnings import SedmlFeatureNotSupportedWarning
from unittest import mock
import datetime
import dateutil.tz
import libsedml
import os
import re
import shutil
import tempfile
import unittest


class IoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_write_read(self):
        shutil.copy(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000075.xml'),
                    os.path.join(self.tmp_dir, 'model.sbml'))

        model1 = data_model.Model(
            id='model1',
            name='Model1',
            source='model.sbml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(
                    target='/sbml:sbml/sbml:model[id=\'a\']/@id',
                    new_value='234'
                ),
                data_model.ModelAttributeChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/@id',
                    new_value='432'
                ),
                data_model.AddElementModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters',
                    new_elements='<sbml:parameter xmlns:sbml="http://www.sbml.org/sbml/level2/version3" id="new_parameter" value="1.0"/>'
                ),
                data_model.AddElementModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters',
                    new_elements='<parameter id="new_parameter_1" value="1.0"/><parameter id="new_parameter_2" value="1.0"/>'
                ),
                data_model.ReplaceElementModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters/sbml:parameter[@id=\'p1\']',
                    new_elements='<parameter id="p1" value="1.0"/>'
                ),
                data_model.ReplaceElementModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters/sbml:parameter[@id=\'p1\']',
                    new_elements='<parameter id="p1" value="1.0"/><parameter id="p1" value="1.0"/>'
                ),
                data_model.RemoveElementModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters/sbml:parameter[@id=\'p1\']',
                ),
                data_model.ComputeModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters/sbml:parameter[@id=\'p1\']',
                    parameters=[
                        data_model.Parameter(id='a', value=1.5),
                        data_model.Parameter(id='b', value=2.25),
                    ],
                    variables=[
                        data_model.Variable(
                            id='x',
                            target='variable_target_x',
                        ),
                        data_model.Variable(
                            id='y',
                            target='variable_target_y',
                        ),
                    ],
                    math='a * x + b * y',
                ),
            ],
        )
        for var in model1.changes[-1].variables:
            var.model = model1

        model2 = data_model.Model(
            id='model2',
            name='Model2',
            source='model.sbml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(
                    target='/sbml:sbml/sbml:model[id=\'a\']/@id',
                    new_value='234',
                ),
                data_model.ModelAttributeChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/@id',
                    new_value='432'
                ),
            ],
        )

        ss_simulation = data_model.SteadyStateSimulation(
            id='simulation1',
            name='Simulation1',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000019',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000211', new_value='1.234'),
                ]),
        )

        one_step_simulation = data_model.OneStepSimulation(
            id='simulation2',
            name='Simulation2',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000019',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000211', new_value='1.234'),
                ]),
            step=10.)

        time_course_simulation = data_model.UniformTimeCourseSimulation(
            id='simulation3',
            name='Simulation3',
            algorithm=data_model.Algorithm(
                kisao_id='KISAO_0000019',
                changes=[
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000209', new_value='1.234'),
                    data_model.AlgorithmParameterChange(kisao_id='KISAO_0000211', new_value='4.321'),
                ]),
            initial_time=10.,
            output_start_time=20.,
            output_end_time=30,
            number_of_steps=10)

        task1 = data_model.Task(id='task1', name='Task1', model=model1, simulation=time_course_simulation)
        task2 = data_model.Task(id='task2', name='Task2', model=model2, simulation=time_course_simulation)
        task3 = data_model.RepeatedTask(
            id='task3',
            name='Task3',
            reset_model_for_each_iteration=True,
            changes=[],
            sub_tasks=[
                data_model.SubTask(task=task1, order=1),
                data_model.SubTask(task=task2, order=2),
            ],
            ranges=[
                data_model.UniformRange(id='range1', start=10., end=20., number_of_steps=4, type=data_model.UniformRangeType.linear),
                data_model.UniformRange(id='range2', start=10., end=20., number_of_steps=4, type=data_model.UniformRangeType.log),
                data_model.VectorRange(id='range3', values=[3., 5., 7., 11., 13.]),
            ],
        )
        task3.ranges.append(
            data_model.FunctionalRange(
                id='range4',
                range=task3.ranges[0],
                parameters=[
                    data_model.Parameter(
                        id='x2',
                        value=2.0,
                    ),
                ],
                variables=[
                    data_model.Variable(
                        id='y2',
                        model=model1,
                        target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:Parameter[@id='param_1']",
                    ),
                ],
                math='{} * {} + {}'.format(task3.ranges[0].id, 'x2', 'y2'),
            ),
        )
        task3.range = task3.ranges[1]
        task3.changes.append(
            data_model.SetValueComputeModelChange(
                model=model1,
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='p1']",
                range=task3.ranges[0],
                parameters=[],
                variables=[],
                math='range1',
            ),
        )
        task3.changes.append(
            data_model.SetValueComputeModelChange(
                model=model1,
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='p1']",
                range=task3.ranges[0],
                parameters=[],
                variables=[
                    data_model.Variable(
                        id='range1_var1',
                        model=model1,
                        target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='p1']",
                    )
                ],
                math='range1 * range1_var1',
            ),
        )
        task3.changes.append(
            data_model.SetValueComputeModelChange(
                model=model1,
                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='p1']",
                range=task3.ranges[0],
                parameters=[
                    data_model.Parameter(id='range1_p1', value=2.5),
                ],
                variables=[],
                math='range1 * range1_p1',
            ),
        )

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
                                id='DataGenVar1',
                                name='DataGenVar1',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task1,
                            )
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
                            data_model.Variable(
                                id='xDataGenVar1', name='XDataGenVar1', symbol='urn:sedml:symbol:time', task=task2)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar1 * xDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='yDataGen3',
                        name='yDataGen3',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar2',
                                name='XDataGenVar1',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam2', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam2',
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
                            data_model.Variable(
                                id='yDataGenVar1',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task1,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='YDataGenParam1', value=2.)
                        ],
                        math='yDataGenVar1 + YDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='yDataGen5',
                        name='yDataGen5',
                        variables=[
                            data_model.Variable(
                                id='yDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task1,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='YDataGenParam2', value=2.),
                        ],
                        math='yDataGenVar2 + YDataGenParam2',
                    ),
                ),
            ]
        )

        plot3d = data_model.Plot3D(
            id='plot3d',
            name='Plot3D',
            surfaces=[
                data_model.Surface(
                    id='surface1', name='Surface1',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    z_scale=data_model.AxisScale.linear,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen6',
                        name='XDataGen6',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar3',
                                name='XDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam3', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar3 * xDataGenParam3',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='xDataGen8',
                        name='XDataGen8',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar4',
                                name='XDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam4', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar4 * xDataGenParam4',
                    ),
                    z_data_generator=data_model.DataGenerator(
                        id='xDataGen9',
                        name='XDataGen9',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar5',
                                name='XDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam5', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar5 * xDataGenParam5',
                    ),
                ),
                data_model.Surface(
                    id='surface2',
                    name='Surface2',
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.log,
                    z_scale=data_model.AxisScale.log,
                    x_data_generator=data_model.DataGenerator(
                        id='xDataGen10',
                        name='XDataGen10',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar6',
                                name='XDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam6', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar6 * xDataGenParam6',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='xDataGen11',
                        name='XDataGen11',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar7',
                                name='XDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam7', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar7 * xDataGenParam7',
                    ),
                    z_data_generator=data_model.DataGenerator(
                        id='xDataGen12',
                        name='XDataGen12',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar8',
                                name='XDataGenVar2',
                                target='/sbml:sbml/sbml:model/@id',
                                task=task2,
                            )
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam8', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar8 * xDataGenParam8',
                    ),
                ),
            ]
        )

        now = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        document = data_model.SedDocument(
            level=1,
            version=3,
            models=[model1],
            simulations=[time_course_simulation],
            tasks=[task1],
            data_generators=(
                [d.data_generator for d in report.data_sets]
            ),
            outputs=[report],
            metadata=Metadata(
                description="description",
                tags=['tag-1', 'tag-2'],
                authors=[
                    Person(given_name='first', other_name='middle', family_name='last'),
                ],
                references=ExternalReferences(
                    identifiers=None,
                    citations=[
                        Citation(
                            title='creative title',
                            authors='Author-1 & Author-2',
                            journal='major journal',
                            volume='10',
                            issue='20',
                            pages='30-40',
                            year=2020,
                            identifiers=[
                                Identifier(
                                    namespace="doi",
                                    id='10.0/1.0',
                                    url="https://doi.org/10.0/1.0"
                                ),
                            ]
                        )
                    ]
                ),
                license=OntologyTerm(
                    namespace='SPDX',
                    id='MIT',
                    url='https://spdx.org/licenses/MIT.html',
                ),
                created=now,
                updated=now,
            ),
        )
        self._set_target_namespaces(document)

        filename = os.path.join(self.tmp_dir, 'test.xml')
        io.SedmlSimulationWriter().run(document, filename)

        document2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(document.is_equal(document2))

        document = data_model.SedDocument(
            level=1,
            version=3,
            models=[model1, model2],
            simulations=[ss_simulation, one_step_simulation, time_course_simulation],
            tasks=[task1, task2, task3],
            data_generators=(
                [d.data_generator for d in report.data_sets]
                + [c.x_data_generator for c in plot2d.curves]
                + [c.y_data_generator for c in plot2d.curves]
                + [s.x_data_generator for s in plot3d.surfaces]
                + [s.y_data_generator for s in plot3d.surfaces]
                + [s.z_data_generator for s in plot3d.surfaces]
            ),
            outputs=[report, plot2d, plot3d],
            metadata=Metadata(
                description="description",
                license=OntologyTerm(
                    namespace='SPDX',
                    id='MIT',
                    url='https://spdx.org/licenses/MIT.html',
                ),
            ),
        )
        self._set_target_namespaces(document)

        filename = os.path.join(self.tmp_dir, 'test.xml')
        io.SedmlSimulationWriter().run(document, filename)

        document2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(document.is_equal(document2))

        document2.metadata.license.namespace = None
        document2.metadata.license.url = None
        io.SedmlSimulationWriter().run(document2, filename)
        document3 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(document2.is_equal(document3))

        document3.metadata = None
        io.SedmlSimulationWriter().run(document3, filename)
        document4 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(document4.is_equal(document3))

        document.models[0].changes[2].new_elements = '<parameter id="new_parameter" value="1.0/>'
        document.models[0].changes[4].new_elements = '<parameter id="new_parameter" value="1.0"/>'
        with self.assertRaisesRegex(ValueError, 'invalid XML'):
            io.SedmlSimulationWriter().run(document, filename)

        document.models[0].changes[2].new_elements = '<parameter id="new_parameter" value="1.0"/>'
        document.models[0].changes[4].new_elements = '<parameter id="new_parameter" value="1.0/>'
        with self.assertRaisesRegex(ValueError, 'invalid XML'):
            io.SedmlSimulationWriter().run(document, filename)

    def _set_target_namespaces(self, document):
        namespaces = {
            None: 'http://sed-ml.org/sed-ml/level1/version3',
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
        }
        for model in document.models:
            for change in model.changes:
                change.target_namespaces = namespaces
                if isinstance(change, data_model.ComputeModelChange):
                    for variable in change.variables:
                        variable.target_namespaces = namespaces
        for task in document.tasks:
            if isinstance(task, data_model.RepeatedTask):
                for change in task.changes:
                    change.target_namespaces = namespaces
                    for variable in change.variables:
                        variable.target_namespaces = namespaces
                for range in task.ranges:
                    if isinstance(range, data_model.FunctionalRange):
                        for variable in range.variables:
                            variable.target_namespaces = namespaces
        for data_generator in document.data_generators:
            for variable in data_generator.variables:
                variable.target_namespaces = namespaces

    def test_write_read_without_semantic_validation(self):
        document = data_model.SedDocument(
            level=1,
            version=3,
            models=[
                data_model.Model(id='model', source='model.xml', language='urn:sedml:language:sbml')
            ],
            tasks=[
                data_model.RepeatedTask(
                    id='task',
                    changes=[
                        data_model.SetValueComputeModelChange(
                            model=None,
                            symbol='x',
                            target_namespaces={None: 'http://sed-ml.org/sed-ml/level1/version3'},
                            math='x'
                        )
                    ],
                )
            ],
        )
        document.tasks[0].changes[0].model = document.models[0]

        filename = os.path.join(self.tmp_dir, 'sim.sedml')
        io.SedmlSimulationWriter().run(document, filename, validate_semantics=False)
        document2 = io.SedmlSimulationReader().run(filename, validate_semantics=False)
        self.assertTrue(document2.is_equal(document))

    def test_write_error_unsupported_classes(self):
        document = data_model.SedDocument(tasks=[mock.Mock(id='task')])
        with self.assertRaisesRegex(NotImplementedError, 'is not supported.'):
            io.SedmlSimulationWriter().run(document, '')

        document = data_model.SedDocument(outputs=[mock.Mock(id='output')])
        with self.assertRaisesRegex(NotImplementedError, 'is not supported.'):
            io.SedmlSimulationWriter().run(document, '')

        document = data_model.SedDocument(outputs=[mock.Mock(id='output')])
        with self.assertRaisesRegex(NotImplementedError, 'is not supported.'):
            io.SedmlSimulationWriter().run(document, '', validate_semantics=False)

        document = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    source='model.xml',
                    language=data_model.ModelLanguage.SBML.value,
                    changes=[
                        mock.Mock(id=None, target='/sbml:sbml', target_namespaces={'sbml': 'sbml'})
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(NotImplementedError, 'is not supported.'):
            io.SedmlSimulationWriter().run(document, '', validate_models_with_languages=False)

        document = data_model.SedDocument(
            outputs=[
                data_model.Plot2D(
                    id='plot',
                    curves=[
                        data_model.Curve(
                            id='curve',
                            x_scale='sin',
                            y_scale=data_model.AxisScale.linear,
                            x_data_generator=data_model.DataGenerator(id='x_data_gen',
                                                                      parameters=[data_model.Parameter(id='x', value=1)],
                                                                      math='x'),
                            y_data_generator=data_model.DataGenerator(id='y_data_gen',
                                                                      parameters=[data_model.Parameter(id='y', value=2)],
                                                                      math='y'),
                        ),
                    ]
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(document)
        with self.assertRaisesRegex(NotImplementedError, 'is not supported.'):
            io.SedmlSimulationWriter().run(document, '')

        document = data_model.SedDocument(
            tasks=[
                data_model.RepeatedTask(
                    id='task',
                    ranges=[
                        mock.Mock(id=None),
                    ],
                    sub_tasks=[
                        data_model.SubTask(order=1, task=data_model.Task())
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'not an instance of'):
            io.SedmlSimulationWriter().run(document, '', validate_models_with_languages=False)

        task = document.tasks[0]
        writer = io.SedmlSimulationWriter()
        writer._obj_to_sed_obj_map = {task: None}
        with self.assertRaisesRegex(NotImplementedError, 'is not supported.'):
            writer._add_range_to_repeated_task(task=task, range_obj=task.ranges[0])

    def test_unsupported_uniform_range_type(self):
        document = data_model.SedDocument(
            models=[data_model.Model(id='model', language=data_model.ModelLanguage.SBML.value, source='model.xml')],
            simulations=[data_model.SteadyStateSimulation(id='sim', algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'))],
            tasks=[
                data_model.RepeatedTask(
                    id='task',
                    ranges=[
                        data_model.UniformRange(id='range', start=0., end=10., number_of_steps=10, type=mock.Mock(value='sin')),
                    ],
                    sub_tasks=[
                        data_model.SubTask(task=data_model.Task(id='task2'), order=1),
                    ],
                ),
            ],
        )
        document.tasks[0].range = document.tasks[0].ranges[0]
        document.tasks[0].sub_tasks[0].task.model = document.models[0]
        document.tasks[0].sub_tasks[0].task.simulation = document.simulations[0]
        document.tasks.append(document.tasks[0].sub_tasks[0].task)

        filename = os.path.join(self.tmp_dir, 'test.xml')
        io.SedmlSimulationWriter().run(document, filename, validate_models_with_languages=False)

        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.SedmlSimulationReader().run(filename)

    def test_read_add_xml(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'add-xml.sedml')
        doc = io.SedmlSimulationReader().run(filename, validate_models_with_languages=False)
        self.assertEqual(len(doc.models), 1)
        self.assertEqual(len(doc.tasks), 1)
        self.assertEqual(len(doc.data_generators), 1)
        self.assertEqual(len(doc.outputs), 3)

    def test_read_new_xml_with_top_level_namespace(self):
        filename = os.path.join(os.path.dirname(__file__), '../fixtures/sedml/new-xml-with-top-level-namespace.sedml')
        doc = io.SedmlSimulationReader().run(filename, validate_models_with_languages=False)
        self.assertEqual(doc.models[0].changes[0].new_elements,
                         '<sbml:parameter xmlns:{}="{}" id="V_mT" value="0.7"/>'.format(
            'sbml', 'http://www.sbml.org/sbml/level2/version3'))

    def test_read_repeated_task(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'repeated-task.sedml')
        with self.assertRaisesRegex(ValueError, 'must have at least one sub-task'):
            doc = io.SedmlSimulationReader().run(filename)

    def test_write_error_invalid_ids(self):
        document = data_model.SedDocument(models=[
            mock.Mock(id=None, source=None, language=None, changes=[]),
        ])
        with self.assertRaisesRegex(ValueError, 'missing ids'):
            io.SedmlSimulationWriter().run(document, '')

        document = data_model.SedDocument(models=[
            mock.Mock(id='model', source=None, language=None, changes=[]),
            mock.Mock(id='model', source=None, language=None, changes=[]),
        ])
        with self.assertRaisesRegex(ValueError, 'ids are repeated'):
            io.SedmlSimulationWriter().run(document, '')

    def test_write_error_libsedmls(self):
        document = data_model.SedDocument()
        with self.assertRaisesRegex(ValueError, r'libSED-ML error:'):
            writer = io.SedmlSimulationWriter()
            writer._obj_to_sed_obj_map = {}
            writer._create_doc(document)
            doc_sed = writer._obj_to_sed_obj_map[document]
            writer._call_libsedml_method(doc_sed, 'setAnnotation', '<rdf')

    def test_read_error_libsedmls(self):
        with self.assertRaises(FileNotFoundError):
            io.SedmlSimulationReader().run('')

        filename = os.path.join(self.tmp_dir, 'sim.sedml')
        with open(filename, 'w') as file:
            pass
        with self.assertRaisesRegex(ValueError, 'XML content is not well-formed'):
            io.SedmlSimulationReader().run(filename)

    def test_write_error_invalid_refs(self):
        document = data_model.SedDocument(tasks=[data_model.Task(id='task', simulation=data_model.UniformTimeCourseSimulation(id='sim'))])
        utils.append_all_nested_children_to_doc(document)
        with self.assertRaisesRegex(ValueError, 'must have a model'):
            io.SedmlSimulationWriter().run(document, '')

        document = data_model.SedDocument(tasks=[data_model.Task(id='task', model=data_model.Model(id='model', source='model.xml'))])
        utils.append_all_nested_children_to_doc(document)
        with self.assertRaisesRegex(ValueError, 'must have a simulation'):
            io.SedmlSimulationWriter().run(document, '')

        document = data_model.SedDocument(
            tasks=[
                data_model.Task(
                    id='task',
                    model=data_model.Model(id='model', source='model.xml'),
                    simulation=data_model.UniformTimeCourseSimulation(id='sim'),
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must be direct children'):
            io.SedmlSimulationWriter().run(document, '')

    def test_read_error_invalid_refs(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'no-id.sedml')
        with self.assertRaisesRegex(ValueError, 'object must have the required attributes'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'duplicate-model-ids.sedml')
        with self.assertRaisesRegex(ValueError, 'multiple models have this id'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'duplicate-simulation-ids.sedml')
        with self.assertRaisesRegex(ValueError, 'multiple simulations have this id'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'duplicate-data-generator-task-ids.sedml')
        with self.assertRaisesRegex(ValueError, 'multiple tasks have this id'):
            io.SedmlSimulationReader().run(filename)

    def test_read_warning_unsupported_classes(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'data-description.sedml')
        with self.assertWarnsRegex(SedmlFeatureNotSupportedWarning, 'data descriptions are not yet supported'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'data-description-with-variable.sedml')
        io.SedmlSimulationReader().run(filename)

    def test_read_error_simulation_times(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'initialTime-more-than-outputStartTime.sedml')
        with self.assertRaisesRegex(ValueError, 'must be at least the initial'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'outputStartTime-more-than-outputEndTime.sedml')
        with self.assertRaisesRegex(ValueError, 'must be at least the output'):
            io.SedmlSimulationReader().run(filename)

    def test_read_error_invalid_references(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'invalid-task-model-reference.sedml')
        with self.assertRaisesRegex(ValueError, 'cannot be resolved to a model'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'invalid-task-simulation-reference.sedml')
        with self.assertRaisesRegex(ValueError, 'cannot be resolved to a simulation'):
            io.SedmlSimulationReader().run(filename)

    def test_write_read_sedml_from_biomodels(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'BIOMD0000000673_sim.sedml')
        temp_filename = os.path.join(self.tmp_dir, os.path.basename(filename))
        shutil.copy(filename, temp_filename)
        with open(os.path.join(self.tmp_dir, 'BIOMD0000000673_url.xml'), 'w') as file:
            pass

        doc = io.SedmlSimulationReader().run(temp_filename, validate_models_with_languages=False)

        filename_2 = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename_2, validate_models_with_languages=False)
        doc_2 = io.SedmlSimulationReader().run(filename_2, validate_models_with_languages=False)

        self.assertTrue(doc_2.is_equal(doc))

    def test_read_unsupported_sedml_version(self):
        filename = os.path.join(self.tmp_dir, 'sim.sedml')

        document = data_model.SedDocument(level=1, version=4)
        io.SedmlSimulationWriter().run(document, filename)

        with self.assertWarnsRegex(SedmlFeatureNotSupportedWarning, 'Only features available in L1V3 are supported'):
            io.SedmlSimulationReader().run(filename)

    def test_SedmlSimulationWriter__add_namespaces_to_obj(self):
        obj = libsedml.SedModel()
        self.assertEqual(obj.getNamespaces().getLength(), 1)

        io.SedmlSimulationWriter()._add_namespaces_to_obj(obj, {'sbml': 'x', 'fbc': 'y'})
        self.assertEqual(obj.getNamespaces().getURI(obj.getNamespaces().getIndexByPrefix('sbml')), 'x')
        self.assertEqual(obj.getNamespaces().getLength(), 3)

        io.SedmlSimulationWriter()._add_namespaces_to_obj(obj, {'sbml': 'x2', 'qual': 'z'})
        self.assertEqual(obj.getNamespaces().getURI(obj.getNamespaces().getIndexByPrefix('sbml')), 'x2')
        self.assertEqual(obj.getNamespaces().getLength(), 4)

    def test_SedmlSimulationReader__get_parent_namespaces_prefixes_used_in_xml_node(self):
        node = libsedml.XMLNode()
        node.getAttributes().add('name', 'value', 'uri', 'prefix')
        self.assertEqual(node.getNamespaces().getLength(), 0)

        self.assertEqual(io.SedmlSimulationReader()._get_parent_namespaces_prefixes_used_in_xml_node(node), set(['prefix']))
