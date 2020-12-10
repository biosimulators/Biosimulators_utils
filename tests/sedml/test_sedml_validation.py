from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import utils
from biosimulators_utils.sedml import validation
from unittest import mock
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
                        data_model.DataGeneratorVariable(
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
                        data_model.DataGeneratorVariable(
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
                    variables=[
                        data_model.DataGeneratorVariable(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1'))
        doc.models.append(data_model.Model(id='model2'))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim'))
        doc.tasks.append(data_model.Task(id='task', model=doc.models[0], simulation=doc.simulations[0]))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.DataGeneratorVariable(
                    id='var',
                    target='target',
                    task=doc.tasks[0],
                    model=doc.models[1],
                )
            ],
        ))
        with self.assertRaisesRegex(ValueError, 'must be consistent'):
            validation.validate_doc(doc)

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1'))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim'))
        doc.tasks.append(data_model.Task(id='task', model=doc.models[0], simulation=doc.simulations[0]))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.DataGeneratorVariable(
                    id='var',
                    target='target',
                    task=doc.tasks[0],
                    model=doc.models[0],
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

    def _validate_task(self, task, variables):
        validation.validate_task(task)
        validation.validate_model_language(task.model.language, data_model.ModelLanguage.SBML)
        validation.validate_model_change_types(task.model.changes, (data_model.ModelAttributeChange, ))
        validation.validate_simulation_type(task.simulation, (data_model.UniformTimeCourseSimulation, ))
        validation.validate_uniform_time_course_simulation(task.simulation)
        validation.validate_data_generator_variables(variables)

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

        with self.assertRaisesRegex(NotImplementedError, 'is not supported. Model language must be'):
            self._validate_task(task, variables)
        task.model.language = data_model.ModelLanguage.SBML
        task.model.changes = [mock.Mock()]

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            self._validate_task(task, variables)
        task.model.changes = [data_model.ModelAttributeChange()]

        with self.assertRaisesRegex(ValueError, 'must define a target'):
            self._validate_task(task, variables)
        task.model.changes = []

        with self.assertRaisesRegex(NotImplementedError, 'is not supported. Simulation must be'):
            self._validate_task(task, variables)
        task.simulation = data_model.UniformTimeCourseSimulation(
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000001'),
            initial_time=10.,
            output_start_time=-10.,
            output_end_time=-20.,
            number_of_points=10.1,
        )

        with self.assertRaisesRegex(ValueError, 'must be at least'):
            self._validate_task(task, variables)
        task.simulation.output_start_time = 10.

        with self.assertRaisesRegex(ValueError, 'must be at least'):
            self._validate_task(task, variables)
        task.simulation.output_end_time = 20.

        with self.assertRaisesRegex(ValueError, 'must be an integer'):
            self._validate_task(task, variables)
        task.simulation.number_of_points = 10.

        variables = [
            data_model.DataGeneratorVariable()
        ]
        with self.assertRaisesRegex(ValueError, 'must define a symbol or target'):
            self._validate_task(task, variables)

        variables = [
            data_model.DataGeneratorVariable(symbol='x', target='y')
        ]
        with self.assertRaisesRegex(ValueError, 'must define a symbol or target'):
            self._validate_task(task, variables)
