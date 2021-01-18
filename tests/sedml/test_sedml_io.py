from biosimulators_utils.data_model import Person, Identifier, OntologyTerm
from biosimulators_utils.biosimulations.data_model import Metadata, ExternalReferences, Citation
from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml import utils
from biosimulators_utils.sedml.warnings import SedmlFeatureNotSupportedWarning
from unittest import mock
import datetime
import dateutil.tz
import os
import shutil
import tempfile
import unittest


class IoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_write_read(self):
        model1 = data_model.Model(
            id='model1',
            name='Model1',
            source='model.sbml',
            language='urn:sedml:language:sbml',
            changes=[
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'a\']/@id', new_value='234'),
                data_model.ModelAttributeChange(target='/sbml:sbml/sbml:model[id=\'b\']/@id', new_value='432'),
                data_model.AddElementModelChange(
                    target='/sbml:sbml/sbml:model[id=\'b\']/sbml:listOfParameters',
                    new_elements='<parameter id="new_parameter" value="1.0"/>'
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
                                id='DataGenVar1', name='DataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task1, model=model1)
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
                                id='xDataGenVar1', name='XDataGenVar1', symbol='urn:sedml:symbol:time', task=task2, model=model2)
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
                                id='xDataGenVar1', name='XDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
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
                            data_model.Variable(
                                id='yDataGenVar1', name='YDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task1, model=model1)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='yDataGenParam1', name='YDataGenParam1', value=2.)
                        ],
                        math='yDataGenParam1 + YDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='yDataGen5',
                        name='yDataGen5',
                        variables=[
                            data_model.Variable(
                                id='yDataGenVar1', name='YDataGenVar1', target='/sbml:sbml/sbml:model/@id', task=task1, model=model1)
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
                            data_model.Variable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='xDataGen8',
                        name='XDataGen8',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    z_data_generator=data_model.DataGenerator(
                        id='xDataGen9',
                        name='XDataGen9',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
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
                            data_model.Variable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    y_data_generator=data_model.DataGenerator(
                        id='xDataGen11',
                        name='XDataGen11',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
                    ),
                    z_data_generator=data_model.DataGenerator(
                        id='xDataGen12',
                        name='XDataGen12',
                        variables=[
                            data_model.Variable(
                                id='xDataGenVar2', name='XDataGenVar2', target='/sbml:sbml/sbml:model/@id', task=task2, model=model2)
                        ],
                        parameters=[
                            data_model.Parameter(
                                id='xDataGenParam1', name='XDataGenParam1', value=2.)
                        ],
                        math='xDataGenVar2 * xDataGenParam1',
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
        with self.assertRaisesRegex(ValueError, 'not valid XML'):
            io.SedmlSimulationWriter().run(document, filename)

        document.models[0].changes[2].new_elements = '<parameter id="new_parameter" value="1.0"/>'
        document.models[0].changes[4].new_elements = '<parameter id="new_parameter" value="1.0/>'
        with self.assertRaisesRegex(ValueError, 'not valid XML'):
            io.SedmlSimulationWriter().run(document, filename)

    def test_write_error_unsupported_classes(self):
        document = data_model.SedDocument(tasks=[mock.Mock(id='task')])
        with self.assertRaises(NotImplementedError):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(outputs=[mock.Mock(id='output')])
        with self.assertRaises(NotImplementedError):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    changes=[
                        mock.Mock()
                    ],
                ),
            ],
        )
        with self.assertRaises(NotImplementedError):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(
            simulations=[
                mock.Mock(
                    id='sim',
                    algorithm=mock.Mock(
                        kisao_id='KISAO_0000001',
                        changes=[],
                    ),
                ),
            ],
        )
        with self.assertRaises(NotImplementedError):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(
            outputs=[
                data_model.Plot2D(
                    id='plot',
                    curves=[
                        data_model.Curve(
                            id='curve',
                            x_scale='sin',
                            x_data_generator=data_model.DataGenerator(id='x_data_gen', math='x'),
                            y_data_generator=data_model.DataGenerator(id='y_data_gen', math='y'),
                        ),
                    ]
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(document)
        with self.assertRaises(NotImplementedError):
            io.SedmlSimulationWriter().run(document, None)

    def test_read_add_xml(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'add-xml.sedml')
        doc = io.SedmlSimulationReader().run(filename)
        self.assertEqual(len(doc.models), 1)
        self.assertEqual(len(doc.tasks), 1)
        self.assertEqual(len(doc.data_generators), 1)
        self.assertEqual(len(doc.outputs), 3)

    @unittest.skip('Not yet implemented')
    def test_read_repeated_task(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'repeated-task.sedml')
        doc = io.SedmlSimulationReader().run(filename)
        self.assertEqual(doc.tasks, [])

    def test_write_error_invalid_ids(self):
        document = data_model.SedDocument(models=[mock.Mock(id=None)])
        with self.assertRaises(ValueError):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(models=[mock.Mock(id='model'), mock.Mock(id='model')])
        with self.assertRaises(ValueError):
            io.SedmlSimulationWriter().run(document, None)

    def test_write_error_libsedmls(self):
        document = data_model.SedDocument()
        with self.assertRaisesRegex(ValueError, r'libSED-ML error:'):
            writer = io.SedmlSimulationWriter()
            writer._obj_to_sed_obj_map = {}
            writer._create_doc(document)
            doc_sed = writer._obj_to_sed_obj_map[document]
            writer._call_libsedml_method(doc_sed, 'setAnnotation', '<rdf')

    def test_read_error_libsedmls(self):
        with self.assertRaisesRegex(ValueError, r'libSED-ML error:'):
            io.SedmlSimulationReader().run(None)

    def test_write_error_invalid_refs(self):
        document = data_model.SedDocument(tasks=[data_model.Task(id='task', simulation=data_model.UniformTimeCourseSimulation(id='sim'))])
        utils.append_all_nested_children_to_doc(document)
        with self.assertRaisesRegex(ValueError, 'must have a model'):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(tasks=[data_model.Task(id='task', model=data_model.Model(id='model'))])
        utils.append_all_nested_children_to_doc(document)
        with self.assertRaisesRegex(ValueError, 'must have a simulation'):
            io.SedmlSimulationWriter().run(document, None)

        document = data_model.SedDocument(
            tasks=[
                data_model.Task(
                    id='task',
                    model=data_model.Model(id='model'),
                    simulation=data_model.UniformTimeCourseSimulation(id='sim'),
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must be direct children'):
            io.SedmlSimulationWriter().run(document, None)

    def test_read_error_invalid_refs(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'no-id.sedml')
        with self.assertRaisesRegex(ValueError, 'object must have the required attributes'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'duplicate-model-ids.sedml')
        with self.assertRaisesRegex(ValueError, 'Document has multiple models with id'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'duplicate-simulation-ids.sedml')
        with self.assertRaisesRegex(ValueError, 'Document has multiple simulations with id'):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'duplicate-data-generator-task-ids.sedml')
        with self.assertRaisesRegex(ValueError, 'Document has multiple tasks with id'):
            io.SedmlSimulationReader().run(filename)

    def test_read_warning_unsupported_classes(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'data-description.sedml')
        with self.assertWarnsRegex(SedmlFeatureNotSupportedWarning, 'data descriptions are not yet supported'):
            io.SedmlSimulationReader().run(filename)

    def test_read_error_simulation_times(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'initialTime-more-than-outputStartTime.sedml')
        with self.assertRaises(ValueError):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'outputStartTime-more-than-outputEndTime.sedml')
        with self.assertRaises(ValueError):
            io.SedmlSimulationReader().run(filename)

    def test_read_error_invalid_references(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'invalid-task-model-reference.sedml')
        with self.assertRaises(ValueError):
            io.SedmlSimulationReader().run(filename)

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'invalid-task-simulation-reference.sedml')
        with self.assertRaises(ValueError):
            io.SedmlSimulationReader().run(filename)

    def test_write_read_sedml_from_biomodels(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml', 'BIOMD0000000673_sim.sedml')
        doc = io.SedmlSimulationReader().run(filename)

        filename_2 = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename_2)
        doc_2 = io.SedmlSimulationReader().run(filename_2)

        self.assertTrue(doc_2.is_equal(doc))
