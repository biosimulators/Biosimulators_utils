from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import utils
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.warnings import IllogicalSedmlWarning
from unittest import mock
import copy
import os
import shutil
import tempfile
import unittest


class ValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_validate_doc(self):
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    source='',
                    changes=[
                        data_model.ModelAttributeChange(),
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must define a target'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            simulations=[
                data_model.OneStepSimulation(
                    id='sim',
                    algorithm=data_model.Algorithm(
                        kisao_id='KISAO:0000029',
                    ),
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(doc)
        with self.assertRaisesRegex(ValueError, 'invalid KiSAO id'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            simulations=[
                data_model.OneStepSimulation(
                    id='sim',
                    algorithm=data_model.Algorithm(
                        kisao_id='KISAO_0000029',
                        changes=[
                            data_model.AlgorithmParameterChange(
                                kisao_id='KISAO:0000001',
                            )
                        ],
                    ),
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(doc)
        with self.assertRaisesRegex(ValueError, 'invalid KiSAO id'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    id='data_gen',
                    variables=[
                        data_model.Variable(
                            id='var',
                        )
                    ],
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(doc)
        with self.assertRaisesRegex(ValueError, 'must define a target or symbol'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    id='data_gen',
                    variables=[
                        data_model.Variable(
                            id='var',
                            target="target",
                            symbol="symbol",
                        )
                    ],
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(doc)
        with self.assertRaisesRegex(ValueError, 'must define a target or symbol'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            outputs=[
                data_model.Report(
                    id='Report',
                    data_sets=[
                        data_model.DataSet(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            outputs=[
                data_model.Report(
                    id='Report',
                    data_sets=[
                        data_model.DataSet(
                            id='dataset',
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have labels'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    id='data_gen',
                    parameters=[
                        data_model.Parameter(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    id='data_gen',
                    variables=[
                        data_model.Variable(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source=''))
        doc.models.append(data_model.Model(id='model2', source=''))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim'))
        doc.tasks.append(data_model.Task(id='task', model=doc.models[0], simulation=doc.simulations[0]))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.Variable(
                    id='var',
                    target='target',
                    task=doc.tasks[0],
                    model=None,
                )
            ],
            math='var',
        ))
        validation.validate_doc(doc)

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source=''))
        doc.models.append(data_model.Model(id='model2', source=''))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim'))
        doc.tasks.append(data_model.Task(id='task', model=doc.models[0], simulation=doc.simulations[0]))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.Variable(
                    id='var',
                    target='target',
                    task=doc.tasks[0],
                    model=doc.models[1],
                )
            ],
        ))
        with self.assertRaisesRegex(ValueError, 'should be null'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source=''))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim'))
        doc.tasks.append(data_model.Task(id='task', model=doc.models[0], simulation=doc.simulations[0]))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.Variable(
                    id='var',
                    target='target',
                    task=doc.tasks[0],
                    model=None,
                )
            ],
        ))
        with self.assertRaisesRegex(ValueError, 'must have math'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            outputs=[
                data_model.Plot2D(
                    id='plot',
                    curves=[
                        data_model.Curve(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument(
            outputs=[
                data_model.Plot3D(
                    id='plot',
                    surfaces=[
                        data_model.Surface(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source=''))
        doc.models[0].changes.append(data_model.ComputeModelChange(
            target='x',
            parameters=[data_model.Parameter(id='a', value=1.25)],
            variables=[data_model.Variable(id='y', target='y', model=doc.models[0])],
            math='a * y'
        ),
        )
        validation.validate_doc(doc)

        doc.models[0].changes[0].parameters[0].id = None
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc.models[0].changes[0].parameters[0].id = 'a'
        doc.models[0].changes[0].variables[0].id = None
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc.models[0].changes[0].variables[0].id = 'y'
        doc.models[0].changes[0].variables[0].target = None
        with self.assertRaisesRegex(ValueError, 'must define a target'):
            validation.validate_doc(doc)

        doc.models[0].changes[0].variables[0].target = 'y'
        doc.models[0].changes[0].variables[0].symbol = 'y'
        with self.assertRaisesRegex(ValueError, 'must define a target, not a symbol'):
            validation.validate_doc(doc)

        doc.models[0].changes[0].variables[0].symbol = None
        doc.models[0].changes[0].variables[0].model = None
        with self.assertRaisesRegex(ValueError, 'must have a'):
            validation.validate_doc(doc)

        doc.models[0].changes[0].variables[0].model = doc.models[0]
        doc.models[0].changes[0].variables[0].task = data_model.Task(
            id='task',
            model=data_model.Model(id='model2', source=''),
            simulation=data_model.SteadyStateSimulation(id='sim'),
        )
        doc.models.append(doc.models[0].changes[0].variables[0].task.model)
        doc.simulations.append(doc.models[0].changes[0].variables[0].task.simulation)
        doc.tasks.append(doc.models[0].changes[0].variables[0].task)
        with self.assertRaisesRegex(ValueError, 'should be null'):
            validation.validate_doc(doc)

        doc.models[0].changes[0].variables[0].task = None
        doc.models[0].changes[0].math = None
        with self.assertRaisesRegex(ValueError, 'must have math'):
            validation.validate_doc(doc)

        # internal model sources are defined
        doc = data_model.SedDocument(models=[
            data_model.Model(id='model_1', source='model.xml'),
            data_model.Model(id='model_2', source='#model_1'),
        ])
        validation.validate_doc(doc)

        doc.models[1].source = '#model_3'
        with self.assertRaisesRegex(ValueError, ' is not defined'):
            validation.validate_doc(doc)

        # cycles of model sources
        doc = data_model.SedDocument(models=[
            data_model.Model(id='model_1', source='model.xml'),
            data_model.Model(id='model_2', source='#model_1'),
            data_model.Model(id='model_3', source='#model_2'),
        ])
        validation.validate_doc(doc)

        doc.models[0].source = '#model_3'
        with self.assertRaisesRegex(ValueError, 'must be acyclic'):
            validation.validate_doc(doc)

        # cycles of model compute changes
        doc = data_model.SedDocument()
        model_1 = data_model.Model(id='model_1', source='model1.xml')
        model_2 = data_model.Model(id='model_2', source='model2.xml')
        doc.models.append(model_1)
        doc.models.append(model_2)
        model_1.changes.append(
            data_model.ComputeModelChange(
                target='x',
                variables=[
                    data_model.Variable(id='y', target='y', model=model_1)
                ],
                math='y',
            )
        )
        model_2.changes.append(
            data_model.ComputeModelChange(
                target='y',
                variables=[
                    data_model.Variable(id='x', target='x', model=model_1)
                ],
                math='x',
            )
        )
        validation.validate_doc(doc)

        doc.models[0].changes[0].variables[0].model = model_2
        with self.assertRaisesRegex(ValueError, 'must be acyclic'):
            validation.validate_doc(doc)

    def test_validate_doc_with_repeated_tasks(self):
        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source='model1.xml', language=data_model.ModelLanguage.SBML))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim1', algorithm=data_model.Algorithm(kisao_id='KISAO_0000001')))
        doc.tasks.append(data_model.Task(id='task1', model=doc.models[0], simulation=doc.simulations[0]))
        doc.tasks.append(
            data_model.RepeatedTask(
                id='task2',
                sub_tasks=[
                    data_model.SubTask(order=1, task=doc.tasks[0]),
                    data_model.SubTask(order=2, task=doc.tasks[0]),
                ],
                ranges=[
                    data_model.VectorRange(id='range1', values=[1., 2., 3.]),
                    data_model.VectorRange(id='range2', values=[4., 5., 6.]),
                ],
                changes=[
                    data_model.SetValueComputeModelChange(
                        model=doc.models[0],
                        target='x',
                        range=None,
                        parameters=[
                            data_model.Parameter(id='a', value=1.25),
                        ],
                        variables=[
                            data_model.Variable(
                                id='x',
                                model=doc.models[0],
                                target='x',
                            )
                        ],
                        math='a * x + b',
                    )
                ],
            ),
        )
        doc.tasks[1].range = doc.tasks[1].ranges[0]
        validation.validate_doc(doc)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks = []
        with self.assertRaisesRegex(ValueError, 'must have at least one sub-task'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks[0].task = None
        with self.assertRaisesRegex(ValueError, 'Sub-tasks must reference tasks'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks[1].order = 1
        with self.assertRaisesRegex(ValueError, 'The `order` of each sub-task should be distinct'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks[1].task = doc2.tasks[1]
        with self.assertRaisesRegex(ValueError, 'must be acyclic'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].range = None
        with self.assertRaisesRegex(ValueError, 'Repeated tasks must have main ranges'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges[0].id = None
        with self.assertRaisesRegex(ValueError, 'Ranges must have ids'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges[1].id = 'range1'
        with self.assertRaisesRegex(ValueError, 'Ranges must have unique ids'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges[1].values.append(7.)
        with self.assertWarnsRegex(IllogicalSedmlWarning, 'will be ignored'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[0].values.append(8.)
        doc2.tasks[1].ranges[0].values.append(9.)
        with self.assertRaisesRegex(ValueError, 'must be at least as long'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].range = data_model.VectorRange(id='change_range', values=range(0, 100))
        with self.assertWarnsRegex(IllogicalSedmlWarning, 'will be ignored'):
            validation.validate_doc(doc2)

        doc2.tasks[1].changes[0].range = data_model.VectorRange(id='change_range', values=range(0, 2))
        with self.assertRaisesRegex(ValueError, 'must be at least as long'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges.append(None)
        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges.append(
            data_model.FunctionalRange(
                id='range3',
                range=doc.tasks[1].ranges[0],
                parameters=[
                    data_model.Parameter(id='p_2', value=3.7),
                ],
                variables=[
                    data_model.Variable(
                        id='var1',
                        model=doc.models[0],
                        target='x',
                    ),
                ],
                math='var1',
            )
        )

        doc2.tasks[1].ranges[2].range = None
        with self.assertRaisesRegex(ValueError, 'must reference another range'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].range = doc.tasks[1].ranges[0]
        doc2.tasks[1].ranges[2].parameters[0].id = None
        with self.assertRaisesRegex(ValueError, 'Parameters must have ids'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].parameters[0].id = 'p_2'
        doc2.tasks[1].ranges[2].variables[0].id = None
        with self.assertRaisesRegex(ValueError, 'Variables must have ids'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].variables[0].id = 'var1'
        doc2.tasks[1].ranges[2].variables[0].model = None
        with self.assertRaisesRegex(ValueError, 'must reference models'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].variables[0].model = doc.models[0]
        doc2.tasks[1].ranges[2].variables[0].task = doc.tasks[0]
        with self.assertRaisesRegex(ValueError, 'should not reference tasks'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].variables[0].task = None
        doc2.tasks[1].ranges[2].variables[0].target = None
        with self.assertRaisesRegex(ValueError, 'should define a symbol or target'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].variables[0].target = 'x'
        doc2.tasks[1].ranges[2].variables[0].symbol = 'y'
        with self.assertRaisesRegex(ValueError, 'should define a symbol or target, not both'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].variables[0].target = None
        validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].math = None
        with self.assertRaisesRegex(ValueError, 'must have math'):
            validation.validate_doc(doc2)

        doc2.tasks[1].ranges[2].math = 'var1'
        doc2.tasks[1].ranges[2].range = doc2.tasks[1].ranges[2]
        with self.assertRaisesRegex(ValueError, 'must be acyclic'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].model = None
        with self.assertRaisesRegex(ValueError, 'must reference models'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].target = None
        with self.assertRaisesRegex(ValueError, 'must define a target'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].symbol = 'x'
        with self.assertRaisesRegex(ValueError, 'should not define a symbol'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].parameters[0].id = None
        with self.assertRaisesRegex(ValueError, 'Parameters must have ids'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].id = None
        with self.assertRaisesRegex(ValueError, 'Variables must have ids'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].model = None
        with self.assertRaisesRegex(ValueError, 'variables must reference a model'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].task = doc2.tasks[0]
        with self.assertRaisesRegex(ValueError, 'should not reference a task'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].target = None
        with self.assertRaisesRegex(ValueError, 'must define a target or a symbol'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].symbol = 'x'
        with self.assertRaisesRegex(ValueError, 'must define a target or a symbol, not both'):
            validation.validate_doc(doc2)

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].math = None
        with self.assertRaisesRegex(ValueError, 'must have math'):
            validation.validate_doc(doc2)

    def _validate_task(self, task, variables):
        validation.validate_task(task)
        validation.validate_model_language(task.model.language, data_model.ModelLanguage.SBML)
        validation.validate_model_change_types(task.model.changes)
        validation.validate_model_changes(task.model.changes)
        validation.validate_simulation_type(task.simulation, (data_model.UniformTimeCourseSimulation, ))
        validation.validate_uniform_time_course_simulation(task.simulation)
        validation.validate_data_generator_variables(variables)

    def test_validate_model(self):
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-list-of-species.xml')
        validation.validate_model(filename, data_model.ModelLanguage.SBML)

        with self.assertRaisesRegex(NotImplementedError, 'No validation is available for'):
            validation.validate_model(filename, '--not-supported--')

    def test_validate_uniform_time_course_simulation(self):
        sim = data_model.UniformTimeCourseSimulation(
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1.,
            number_of_steps=10)
        validation.validate_uniform_time_course_simulation(sim)

        sim.number_of_steps = 10.5
        with self.assertRaisesRegex(ValueError, 'must be an integer'):
            validation.validate_uniform_time_course_simulation(sim)

        sim.number_of_steps = 0
        with self.assertRaisesRegex(ValueError, 'must be at least 1'):
            validation.validate_uniform_time_course_simulation(sim)

        sim.output_end_time = -1
        with self.assertRaisesRegex(ValueError, 'must be at least the output start time'):
            validation.validate_uniform_time_course_simulation(sim)

        sim.output_start_time = -2
        with self.assertRaisesRegex(ValueError, 'must be at least the initial time'):
            validation.validate_uniform_time_course_simulation(sim)

    def test_validate_uniform_range(self):
        range = data_model.UniformRange(
            start=0.,
            end=10.,
            number_of_steps=10,
        )
        validation.validate_uniform_range(range)

        range.number_of_steps = 0
        with self.assertRaisesRegex(ValueError, 'must have at least one step'):
            validation.validate_uniform_range(range)

    def test(self):
        task = None
        variables = []

        with self.assertRaisesRegex(ValueError, 'is not supported'):
            self._validate_task(task, variables)
        task = data_model.Task()

        with self.assertRaisesRegex(ValueError, 'must have a model'):
            self._validate_task(task, variables)
        task.model = data_model.Model()

        with self.assertRaisesRegex(FileNotFoundError, 'must be a file'):
            self._validate_task(task, variables)
        task.model.source = os.path.join(self.dirname, 'invalid-model.xml')

        with self.assertRaisesRegex(FileNotFoundError, 'must be a file'):
            self._validate_task(task, variables)
        task.model.source = os.path.join(self.dirname, 'valid-model.xml')
        with open(task.model.source, 'w') as file:
            file.write('!')

        with self.assertRaisesRegex(ValueError, 'must have a simulation'):
            self._validate_task(task, variables)
        task.simulation = mock.Mock(algorithm=None)

        with self.assertRaisesRegex(ValueError, 'must have an algorithm'):
            self._validate_task(task, variables)
        task.simulation.algorithm = data_model.Algorithm()

        with self.assertRaisesRegex(ValueError, 'must have a valid KiSAO id'):
            self._validate_task(task, variables)
        task.simulation.algorithm.kisao_id = 'KISAO_0000001'
        task.simulation.algorithm.changes = [
            data_model.AlgorithmParameterChange()
        ]

        with self.assertRaisesRegex(ValueError, 'must have a valid KiSAO id'):
            self._validate_task(task, variables)
        task.simulation.algorithm.changes[0].kisao_id = 'KISAO_0000001'

        with self.assertRaisesRegex(NotImplementedError, 'is not supported. Models must be in'):
            self._validate_task(task, variables)
        task.model.language = data_model.ModelLanguage.SBML
        task.model.changes = [mock.Mock()]

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            self._validate_task(task, variables)
        task.model.changes = [data_model.ModelAttributeChange()]

        with self.assertRaisesRegex(ValueError, 'must define a target'):
            self._validate_task(task, variables)
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', model=task.model, target='y', symbol='y')],
                math='y',
            ),
        ]

        with self.assertRaisesRegex(ValueError, 'must define a target, not a symbol'):
            self._validate_task(task, variables)
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', model=task.model)],
                math='y',
            ),
        ]

        with self.assertRaisesRegex(ValueError, 'must define a target'):
            self._validate_task(task, variables)
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', target='y')],
                math='y',
            ),
        ]

        with self.assertRaisesRegex(ValueError, 'must reference a model'):
            self._validate_task(task, variables)
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', model=task.model, task=data_model.Task(), target='y')],
                math='y',
            ),
        ]

        with self.assertRaisesRegex(ValueError, 'should not reference a task'):
            self._validate_task(task, variables)
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(model=task.model, target='y')],
                math='y',
            ),
        ]

        with self.assertRaisesRegex(ValueError, 'must have ids'):
            self._validate_task(task, variables)
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                parameters=[data_model.Parameter(value=1.25)],
                math='y',
            ),
        ]

        with self.assertRaisesRegex(ValueError, 'must have ids'):
            self._validate_task(task, variables)
        task.model.changes = []

        with self.assertRaisesRegex(NotImplementedError, 'is not supported. Simulation must be'):
            self._validate_task(task, variables)
        task.simulation = data_model.UniformTimeCourseSimulation(
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000001'),
            initial_time=10.,
            output_start_time=-10.,
            output_end_time=-20.,
            number_of_steps=10.1,
        )

        with self.assertRaisesRegex(ValueError, 'must be at least'):
            self._validate_task(task, variables)
        task.simulation.output_start_time = 10.

        with self.assertRaisesRegex(ValueError, 'must be at least'):
            self._validate_task(task, variables)
        task.simulation.output_end_time = 20.

        with self.assertRaisesRegex(ValueError, 'must be an integer'):
            self._validate_task(task, variables)
        task.simulation.number_of_steps = 10.

        variables = [
            data_model.Variable()
        ]
        with self.assertRaisesRegex(ValueError, 'must reference a task'):
            self._validate_task(task, variables)

        variables = [
            data_model.Variable(task=data_model.Task(), model=data_model.Model())
        ]
        with self.assertRaisesRegex(ValueError, 'should not reference a model'):
            self._validate_task(task, variables)

        variables = [
            data_model.Variable(task=data_model.Task())
        ]
        with self.assertRaisesRegex(ValueError, 'must define a symbol or target'):
            self._validate_task(task, variables)

        variables = [
            data_model.Variable(task=data_model.Task(), symbol='x', target='y')
        ]
        with self.assertRaisesRegex(ValueError, 'must define a symbol or target'):
            self._validate_task(task, variables)

    def test_validate_variable_xpaths(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        model_source = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')

        variables = [
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']"),
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']/@value"),
        ]
        validation.validate_variable_xpaths(variables, model_source)

        variables = [
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']"),
        ]
        with self.assertRaises(ValueError):
            validation.validate_variable_xpaths(variables, model_source)

        variables = [
            data_model.Variable(target_namespaces=namespaces,
                                target='/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species'),
        ]
        with self.assertRaises(ValueError):
            validation.validate_variable_xpaths(variables, model_source)
