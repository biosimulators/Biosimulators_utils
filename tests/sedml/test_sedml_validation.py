from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import utils
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.warnings import IllogicalSedmlWarning
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from lxml import etree
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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must define a target', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('invalid KiSAO id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        doc = data_model.SedDocument(
            simulations=[
                data_model.OneStepSimulation(
                    id='sim',
                    algorithm=data_model.Algorithm(
                        kisao_id='KISAO_0000029',
                        changes=[
                            data_model.AlgorithmParameterChange(
                                kisao_id='KISAO:0000488',
                            )
                        ],
                    ),
                ),
            ],
        )
        utils.append_all_nested_children_to_doc(doc)
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('invalid KiSAO id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must define a symbol or target', flatten_nested_list_of_strings(errors))
        self.assertIn('data generators do not contribute to outputs', flatten_nested_list_of_strings(warnings))

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must define a symbol or target', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have a label', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1'))
        doc.models.append(data_model.Model(id='model2'))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim', algorithm=data_model.Algorithm(kisao_id='KISAO_0000029')))
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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have a source', flatten_nested_list_of_strings(errors), flatten_nested_list_of_strings(errors))
        self.assertIn('tasks do not contribute to outputs', flatten_nested_list_of_strings(
            warnings), flatten_nested_list_of_strings(warnings))
        doc.outputs.append(data_model.Report(
            id='report',
            data_sets=[
                data_model.DataSet(id='d', label='d', data_generator=doc.data_generators[0])
            ],
        ))
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have a source', flatten_nested_list_of_strings(errors), flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        doc.models[0].source = 'model1.xml'
        doc.models[1].source = 'model2.xml'

        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have a language', flatten_nested_list_of_strings(errors), flatten_nested_list_of_strings(errors))
        self.assertIn('No validation is available', flatten_nested_list_of_strings(warnings), flatten_nested_list_of_strings(warnings))
        doc.models[0].language = data_model.ModelLanguage.SBML.value
        doc.models[1].language = data_model.ModelLanguage.SBML.value

        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))    

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
        doc.outputs.append(data_model.Report(
            id='report',
            data_sets=[
                data_model.DataSet(id='d', label='d', data_generator=doc.data_generators[0])
            ],
        ))
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('should not reference a model', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        doc.outputs.append(data_model.Report(
            id='report',
            data_sets=[
                data_model.DataSet(id='d', label='d', data_generator=doc.data_generators[0])
            ],
        ))
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have math', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

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
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', language=data_model.ModelLanguage.SBML.value, source='model1.xml'))
        doc.models[0].changes.append(data_model.ComputeModelChange(
            target='x',
            parameters=[data_model.Parameter(id='a', value=1.25)],
            variables=[data_model.Variable(id='y', target='y', model=doc.models[0])],
            math='a * y'
        ),
        )
        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].parameters[0].id = None
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].parameters[0].id = 'a'
        doc.models[0].changes[0].variables[0].id = None
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].variables[0].id = 'y'
        doc.models[0].changes[0].variables[0].target = None
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must define a target', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].variables[0].target = 'y'
        doc.models[0].changes[0].variables[0].symbol = 'y'
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must define a target, not a symbol', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].variables[0].symbol = None
        doc.models[0].changes[0].variables[0].model = None
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must reference a model', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].variables[0].model = doc.models[0]
        doc.models[0].changes[0].variables[0].task = data_model.Task(
            id='task',
            model=data_model.Model(id='model2', source=''),
            simulation=data_model.SteadyStateSimulation(id='sim'),
        )
        doc.models.append(doc.models[0].changes[0].variables[0].task.model)
        doc.simulations.append(doc.models[0].changes[0].variables[0].task.simulation)
        doc.tasks.append(doc.models[0].changes[0].variables[0].task)
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('should not reference a task', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].variables[0].task = None
        doc.models[0].changes[0].math = None
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must have math', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        # internal model sources are defined
        doc = data_model.SedDocument(models=[
            data_model.Model(id='model_1', language=data_model.ModelLanguage.SBML.value, source='model.xml'),
            data_model.Model(id='model_2', language=data_model.ModelLanguage.SBML.value, source='#model_1'),
        ])
        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        doc.models[1].source = '#model_3'
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('is not defined', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # cycles of model sources
        doc = data_model.SedDocument(models=[
            data_model.Model(id='model_1', language=data_model.ModelLanguage.SBML.value, source='model.xml'),
            data_model.Model(id='model_2', language=data_model.ModelLanguage.SBML.value, source='#model_1'),
            data_model.Model(id='model_3', language=data_model.ModelLanguage.SBML.value, source='#model_2'),
        ])
        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        doc.models[0].source = '#model_3'
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must be acyclic', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # cycles of model compute changes
        doc = data_model.SedDocument()
        model_1 = data_model.Model(id='model_1', language=data_model.ModelLanguage.SBML.value, source='model1.xml')
        model_2 = data_model.Model(id='model_2', language=data_model.ModelLanguage.SBML.value, source='model2.xml')
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
        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        doc.models[0].changes[0].variables[0].model = model_2
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertIn('must be acyclic', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

    def test_validate_doc_with_xml_file(self):
        model_filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures',
                                      'Chaouiya-BMC-Syst-Biol-2013-EGF-TNFa-signaling.xml')

        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model', source=model_filename, language=data_model.ModelLanguage.SBML.value))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim', algorithm=data_model.Algorithm(kisao_id='KISAO_0000019')))
        doc.tasks.append(data_model.Task(
            id='task',
            model=doc.models[0],
            simulation=doc.simulations[0],
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.Variable(
                    id='var1',
                    target="/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']/@qual:level",
                    target_namespaces={
                        'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                        'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
                    },
                    task=doc.tasks[0],
                )
            ],
            math='var1',
        ))
        doc.outputs.append(data_model.Report(
            id='report',
            data_sets=[
                data_model.DataSet(
                    id='d',
                    label='d',
                    data_generator=doc.data_generators[0],
                ),
            ]
        ))
        errors, warnings = validation.validate_doc(doc, self.dirname)
        self.assertEqual(errors, [], flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [], flatten_nested_list_of_strings(warnings))

        doc.data_generators[0].variables[0].target = doc.data_generators[0].variables[0].target.replace('erk', 'ERK')
        self.assertNotEqual(validation.validate_doc(doc, self.dirname), ([], []))

        doc.models[0].source = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'tellurium.json')
        self.assertNotEqual(validation.validate_doc(doc, self.dirname), ([], []))

    def test_validate_doc_with_repeated_tasks(self):
        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source='model1.xml', language=data_model.ModelLanguage.SBML))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim1', algorithm=data_model.Algorithm(kisao_id='KISAO_0000019')))
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
                            data_model.Parameter(id='b', value=1.),
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
        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks = []
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must have at least one sub-task', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks[0].task = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('Sub-task 1 must reference a task', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks[1].order = 1
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('The `order` of each sub-task should be distinct', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].sub_tasks[1].task = doc2.tasks[1]
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must be acyclic', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].range = None
        errors, warnings = validation.validate_doc(doc2, self.dirname, validate_models_with_languages=False)
        self.assertIn('Repeated task must have a main range', flatten_nested_list_of_strings(errors))
        self.assertIn('tail elements of the range will be ignored', flatten_nested_list_of_strings(warnings))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges[0].id = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges[1].id = 'range1'
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('Ranges must have unique ids', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges[1].values.append(7.)
        errors, warnings = validation.validate_doc(doc2, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertIn('will be ignored', flatten_nested_list_of_strings(warnings))

        doc2.tasks[1].ranges[0].values.append(8.)
        doc2.tasks[1].ranges[0].values.append(9.)
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must be at least as long', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].range = data_model.VectorRange(id='change_range', values=range(0, 100))
        errors, warnings = validation.validate_doc(doc2, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertIn('will be ignored', flatten_nested_list_of_strings(warnings))

        doc2.tasks[1].changes[0].range = data_model.VectorRange(id='change_range', values=range(0, 2))
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must be at least as long', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges.append(None)
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('not an instance of', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].ranges.append(
            data_model.FunctionalRange(
                id='range3',
                range=doc2.tasks[1].ranges[0],
                parameters=[
                    data_model.Parameter(id='p_2', value=3.7),
                ],
                variables=[
                    data_model.Variable(
                        id='var1',
                        model=doc2.models[0],
                        target='x',
                    ),
                ],
                math='var1',
            )
        )

        doc2.tasks[1].ranges[2].range = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must reference another range', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].range = doc2.tasks[1].ranges[0]
        doc2.tasks[1].ranges[2].parameters[0].id = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].parameters[0].id = 'p_2'
        doc2.tasks[1].ranges[2].variables[0].id = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('Variable must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].variables[0].id = 'var1'
        doc2.tasks[1].ranges[2].variables[0].model = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must reference a model', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].variables[0].model = doc2.models[0]
        doc2.tasks[1].ranges[2].variables[0].task = doc2.tasks[0]
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('should not reference a task', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].variables[0].task = None
        doc2.tasks[1].ranges[2].variables[0].target = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('should define a symbol or target', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].variables[0].target = 'x'
        doc2.tasks[1].ranges[2].variables[0].symbol = 'y'
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('should define a symbol or target, not both', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].variables[0].target = None
        errors, warnings = validation.validate_doc(doc2, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].math = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must have math', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2.tasks[1].ranges[2].math = 'var1'
        doc2.tasks[1].ranges[2].range = doc2.tasks[1].ranges[2]
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must be acyclic', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].model = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must reference a model', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].target = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must define a target', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].symbol = 'x'
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('should not define a symbol', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].parameters[0].id = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('Parameter 1 must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].id = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('Variable must have an id', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].model = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('variable must reference a model', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].task = doc2.tasks[0]
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('should not reference a task', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].target = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must define a target or a symbol', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].variables[0].symbol = 'x'
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must define a target or a symbol, not both', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

        doc2 = copy.deepcopy(doc)
        doc2.tasks[1].changes[0].math = None
        errors, warnings = validation.validate_doc(doc2, self.dirname)
        self.assertIn('must have math', flatten_nested_list_of_strings(errors))
        self.assertNotEqual(warnings, [])

    def test_validate_sub_tasks_with_different_shapes(self):
        doc = data_model.SedDocument()
        doc.models.append(data_model.Model(id='model1', source='model1.xml', language=data_model.ModelLanguage.SBML))
        doc.simulations.append(data_model.SteadyStateSimulation(id='sim1', algorithm=data_model.Algorithm(kisao_id='KISAO_0000019')))
        doc.simulations.append(data_model.OneStepSimulation(id='sim2', algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'), step=1.0))
        doc.tasks.append(data_model.Task(id='task1', model=doc.models[0], simulation=doc.simulations[0]))
        doc.tasks.append(data_model.Task(id='task2', model=doc.models[0], simulation=doc.simulations[1]))
        doc.tasks.append(
            data_model.RepeatedTask(
                id='task3',
                sub_tasks=[
                    data_model.SubTask(order=1, task=doc.tasks[0]),
                    data_model.SubTask(order=2, task=doc.tasks[1]),
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
                            data_model.Parameter(id='b', value=1.),
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
        doc.tasks[-1].range = doc.tasks[-1].ranges[0]
        doc.tasks.append(
            data_model.RepeatedTask(
                id='task4',
                sub_tasks=[
                    data_model.SubTask(order=1, task=doc.tasks[-1]),
                ],
                ranges=[
                    data_model.VectorRange(id='range3', values=[1., 2., 3.]),
                ],
                changes=[
                    data_model.SetValueComputeModelChange(
                        model=doc.models[0],
                        target='x',
                        range=None,
                        parameters=[
                            data_model.Parameter(id='c', value=1.25),
                            data_model.Parameter(id='d', value=1.),
                        ],
                        variables=[
                            data_model.Variable(
                                id='y',
                                model=doc.models[0],
                                target='y',
                            )
                        ],
                        math='c * y + d',
                    )
                ],
            ),
        )
        doc.tasks[-1].range = doc.tasks[-1].ranges[0]
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen',
            variables=[
                data_model.Variable(id='time', symbol=data_model.Symbol.time.value, task=doc.tasks[-1])
            ],
            math='time',
        ))
        doc.outputs.append(data_model.Report(
            id='report',
            data_sets=[
                data_model.DataSet(
                    id='data_set',
                    label='data_set',
                    data_generator=doc.data_generators[0],
                ),
            ],
        ))
        errors, warnings = validation.validate_doc(doc, self.dirname, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertIn("outputs of the sub-tasks have different shapes", flatten_nested_list_of_strings(warnings))

    def _validate_task(self, task, variables):
        errors = []
        warnings = []
        errors.extend(validation.validate_task(task))
        if task:
            if task.model:
                errors.extend(validation.validate_model_language(task.model.language, data_model.ModelLanguage.SBML))
                tmp_errors, tmp_warnings, _ = validation.validate_model_with_language(task.model.source, task.model.language)
                errors.extend(tmp_errors)
                warnings.extend(tmp_warnings)
                errors.extend(validation.validate_model_change_types(task.model.changes))
                temp_errors, temp_warnings = validation.validate_model_changes(task.model)
                errors.extend(temp_errors)
                warnings.extend(temp_warnings)
            if task.simulation:
                errors.extend(validation.validate_simulation_type(task.simulation, (data_model.UniformTimeCourseSimulation, )))

                temp_errors, temp_warnings = validation.validate_simulation(task.simulation)
                errors.extend(temp_errors)
                warnings.extend(temp_warnings)
        if variables:
            temp_errors, temp_warnings = validation.validate_data_generator_variables(variables)
            errors.extend(temp_errors)
            warnings.extend(temp_warnings)
        return (errors, warnings)

    def test_validate_model_source_with_abs_path(self):
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-list-of-species.xml'))
        errors, warnings = validation.validate_model_source(data_model.Model(
            source=filename, language=data_model.ModelLanguage.SBML), [], None, validate_models_with_languages=False)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_validate_model_source_with_urn(self):
        errors, warnings = validation.validate_model_source(data_model.Model(
            source='urn:miriam:biomodels.db:BIOMD0000000297',
            language=data_model.ModelLanguage.SBML), [], None)
        self.assertEqual(errors, [])
        self.assertIn('be deprecated', flatten_nested_list_of_strings(warnings))
        self.assertIn('not validated', flatten_nested_list_of_strings(warnings))

    def test_validate_model_source_with_url(self):
        errors, warnings = validation.validate_model_source(data_model.Model(
            source='https://github.com/org/repo/model.xml',
            language=data_model.ModelLanguage.SBML), [], None)
        self.assertEqual(errors, [])
        self.assertIn('not validated', flatten_nested_list_of_strings(warnings))

    def test_validate_model_with_language(self):
        # SBML
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-list-of-species.xml')
        validation.validate_model_with_language(filename, data_model.ModelLanguage.SBML)

        errors, warnings, _ = validation.validate_model_with_language(filename, '--not-supported--')
        self.assertEqual(errors, [])
        self.assertIn('No validation is available for', flatten_nested_list_of_strings(warnings))

        # BNGL
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'bngl', 'valid.bngl')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.BNGL)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'bngl', 'invalid.bngl')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.BNGL)
        self.assertNotEqual(errors, [])
        self.assertEqual(warnings, [])

        # CellML
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'cellml', 'version2.xml')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.CellML)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'cellml', 'missing-attribute.xml')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.CellML)
        self.assertNotEqual(errors, [])
        self.assertEqual(warnings, [])

        # LEMS
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'lems', 'LEMS_NML2_Ex5_DetCell.xml')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.LEMS)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'lems', 'invalid.xml')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.LEMS)
        self.assertIn("Can't read LEMS from XMLElt:", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # NeuroML
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'neuroml', 'IM.channel.nml')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.NeuroML)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'neuroml', 'invalid-model.nml')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.NeuroML)
        self.assertIn("is not valid against the schema", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # RBA
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'rba', 'Escherichia-coli-K12-WT.zip')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.RBA)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'rba', 'Escherichia-coli-K12-WT-invalid.zip')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.RBA)
        self.assertIn("expected '>'", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # Smoldyn
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'smoldyn', 'bounce1.txt')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.Smoldyn)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'smoldyn', 'invalid.txt')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.Smoldyn)
        self.assertIn("not a valid Smoldyn", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        # XPP
        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'xpp', 'wilson-cowan.ode')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.XPP)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'xpp', 'wilson-cowan-invalid.ode')
        errors, warnings, _ = validation.validate_model_with_language(filename, data_model.ModelLanguage.XPP)
        self.assertIn("ERROR compiling U'", flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_validate_model_changes_warning_handling(self):
        model = data_model.Model(
            source=os.path.join('..', 'fixtures', 'BIOMD0000000297.xml'),
            language=data_model.ModelLanguage.SBML.value,
        )
        model.changes.append(
            data_model.ComputeModelChange(
                id='change',
                target='/sbml:sbml/sbml:model',
                target_namespaces={'sbml': 'sbml'},
                variables=[
                    data_model.Variable(
                        id='var',
                        model=model,
                        target='#dataDescription',
                    ),
                ],
                math='var'
            )
        )
        errors, warnings = validation.validate_model_changes(model)
        self.assertIn('not supported', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        model.changes[0].variables[0].target = model.changes[0].target
        model.changes[0].variables[0].target_namespaces = model.changes[0].target_namespaces
        errors, warnings = validation.validate_model_changes(model)
        self.assertEqual(errors, [])
        self.assertIn('XPath could not be validated.', flatten_nested_list_of_strings(warnings))

        with mock.patch('biosimulators_utils.sedml.validation.validate_target', return_value=([], [['warning']])):
            errors, warnings = validation.validate_model_changes(model)
        self.assertEqual(errors, [])
        self.assertIn('may be invalid', flatten_nested_list_of_strings(warnings))

        with mock.patch('biosimulators_utils.sedml.validation.validate_target', return_value=([], [['warning']])):
            errors, warnings = validation.validate_model(model, [], os.path.dirname(__file__))
        self.assertEqual(errors, [])
        self.assertIn('changes of the model may be invalid', flatten_nested_list_of_strings(warnings))

    def test_validate_simulation(self):
        sim = data_model.UniformTimeCourseSimulation(
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1.,
            number_of_steps=10)
        validation.validate_simulation(sim)

        sim.number_of_steps = 10.5
        errors, warnings = validation.validate_simulation(sim)
        self.assertIn('must be an integer', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        sim.number_of_steps = 0
        errors, warnings = validation.validate_simulation(sim)
        self.assertIn('must be at least 1', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        sim.output_end_time = -1
        errors, warnings = validation.validate_simulation(sim)
        self.assertIn('must be at least the output start time', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        sim.output_start_time = -2
        errors, warnings = validation.validate_simulation(sim)
        self.assertIn('must be at least the initial time', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        sim.algorithm = data_model.Algorithm(kisao_id='KISAO_0000019')
        sim.initial_time = 0.
        sim.output_start_time = 0.
        sim.output_end_time = 1000.
        sim.number_of_points = 1001
        errors, warnings = validation.validate_simulation(sim)
        self.assertEqual(errors, [])
        self.assertIn('unusual number of steps', flatten_nested_list_of_strings(warnings))

    def test_validate_algorithm(self):
        alg = data_model.Algorithm(
            kisao_id='KISAO_0000019',
            changes=[
                data_model.AlgorithmParameterChange(kisao_id='KISAO_0000209', new_value='1e-6'),
                data_model.AlgorithmParameterChange(kisao_id='KISAO_0000211', new_value='1e-12'),
            ],
        )
        errors, warnings = validation.validate_algorithm(alg)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        alg.kisao_id = 'KISAO_0000211'
        errors, warnings = validation.validate_algorithm(alg)
        self.assertIn('Algorithm has an invalid', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        alg.changes[0].kisao_id = 'KISAO_0000019'
        errors, warnings = validation.validate_algorithm(alg)
        self.assertIn('Algorithm change ', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        alg.changes[0].kisao_id = 'KISAO_0000211'
        errors, warnings = validation.validate_algorithm(alg)
        self.assertIn('must have a unique KiSAO id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_validate_uniform_range(self):
        range = data_model.UniformRange(
            start=0.,
            end=10.,
            number_of_steps=10,
        )
        validation.validate_uniform_range(range)

        range.number_of_steps = 0
        errors = validation.validate_uniform_range(range)
        self.assertIn('must have at least one step', flatten_nested_list_of_strings(errors))

    def test_validate_task(self):
        task = None
        variables = []

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must be an instance of', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task = data_model.Task()

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must have a model', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.model = data_model.Model()

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('is not supported', flatten_nested_list_of_strings(errors))
        self.assertIn('No validation is available', flatten_nested_list_of_strings(warnings))
        task.model.language = data_model.ModelLanguage.SBML.value

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must be a path', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.model.source = os.path.join(self.dirname, 'invalid-model.xml')

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.model.source = os.path.join(self.dirname, 'valid-model.xml')
        with open(task.model.source, 'w') as file:
            file.write('!')

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must have a simulation', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation = mock.Mock(algorithm=None)

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must have an algorithm', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation.algorithm = data_model.Algorithm()

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('Algorithm has an invalid KiSAO id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation.algorithm.kisao_id = 'KISAO_0000019'
        task.simulation.algorithm.changes = [
            data_model.AlgorithmParameterChange()
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('has an invalid KiSAO id', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation.algorithm.changes[0].kisao_id = 'KISAO_0000211'
        task.model.changes = [mock.Mock(id='', target='', target_namespaces={})]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('is not supported', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.model.changes = [data_model.ModelAttributeChange()]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must define a target', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', model=task.model, target='y', symbol='y')],
                math='y',
            ),
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must define a target, not a symbol', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated', flatten_nested_list_of_strings(warnings))
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', model=task.model)],
                math='y',
            ),
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must define a target', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated', flatten_nested_list_of_strings(warnings))
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', target='y')],
                math='y',
            ),
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must reference a model', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated', flatten_nested_list_of_strings(warnings))
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(id='y', model=task.model, task=data_model.Task(), target='y')],
                math='y',
            ),
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('should not reference a task', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated', flatten_nested_list_of_strings(warnings))
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                variables=[data_model.Variable(model=task.model, target='y')],
                math='y',
            ),
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated', flatten_nested_list_of_strings(warnings))
        task.model.changes = [
            data_model.ComputeModelChange(
                target='x',
                parameters=[data_model.Parameter(value=1.25)],
                math='y',
            ),
        ]

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('XPath could not be validated', flatten_nested_list_of_strings(warnings))
        task.model.changes = []

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('is not supported. Simulation must be', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation = data_model.UniformTimeCourseSimulation(
            algorithm=data_model.Algorithm(kisao_id='KISAO_0000019'),
            initial_time=10.,
            output_start_time=-10.,
            output_end_time=-20.,
            number_of_steps=10.1,
        )

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must be at least', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation.output_start_time = 10.

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must be at least', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation.output_end_time = 20.

        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must be an integer', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])
        task.simulation.number_of_steps = 10.

        variables = [
            data_model.Variable()
        ]
        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must reference a task', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        variables = [
            data_model.Variable(task=data_model.Task(), model=data_model.Model())
        ]
        errors, warnings = self._validate_task(task, variables)
        self.assertIn('should not reference a model', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        variables = [
            data_model.Variable(task=data_model.Task())
        ]
        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must define a symbol or target', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        variables = [
            data_model.Variable(task=data_model.Task(), symbol='x', target='y')
        ]
        errors, warnings = self._validate_task(task, variables)
        self.assertIn('must define a symbol or target', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        task = data_model.Task(
            id='task',
            model=data_model.Model(
                id='model',
                source=os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml'),
                language=data_model.ModelLanguage.SBML.value,
            ),
            simulation=data_model.UniformTimeCourseSimulation(
                id='sim',
                initial_time=0.,
                output_start_time=0.,
                output_end_time=10.,
                number_of_steps=10,
                algorithm=data_model.Algorithm(
                    kisao_id='KISAO_0000019',
                )
            ),
        )
        variables = [
            data_model.Variable(id='var', target='#dataDescription')
        ]
        with mock.patch('biosimulators_utils.sedml.validation.validate_data_generator_variables',
                        return_value=([], [['could not be validated']])):
            errors, warnings = self._validate_task(task, variables)
        self.assertEqual(errors, [])
        self.assertIn('could not be validated', flatten_nested_list_of_strings(warnings))

    def test_validate_repeated_task_has_one_model(self):
        model = data_model.Model(id='0')
        task = data_model.RepeatedTask(
            sub_tasks=[
                data_model.SubTask(task=data_model.Task(model=model)),
                data_model.SubTask(task=data_model.Task(model=model)),
                data_model.SubTask(task=data_model.RepeatedTask(
                    sub_tasks=[
                        data_model.SubTask(task=data_model.Task(model=model)),
                    ]
                ))
            ]
        )
        errors, warnings = validation.validate_repeated_task_has_one_model(task)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        task.sub_tasks[0].task.model = data_model.Model(id='1')
        errors, warnings = validation.validate_repeated_task_has_one_model(task)
        self.assertEqual(errors, [])
        self.assertIn('use of multiple models', flatten_nested_list_of_strings(warnings))

    def test_validate_target_xpaths(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        model_source = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')
        model_etree = etree.parse(model_source)

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
        validation.validate_target_xpaths(variables, model_etree)

        variables = [
            data_model.Variable(target_namespaces=namespaces,
                                target="/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']"),
        ]
        with self.assertRaises(ValueError):
            validation.validate_target_xpaths(variables, model_etree)

        variables = [
            data_model.Variable(target_namespaces=namespaces,
                                target='/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species'),
        ]
        with self.assertRaises(ValueError):
            validation.validate_target_xpaths(variables, model_etree)

    def test_validate_target(self):
        self.assertEqual(validation.validate_target('/sbml:sbml/sbml:model',
                                                    {None: 'sed-ml', 'sbml': 'sbml'},
                                                    data_model.Calculation,
                                                    data_model.ModelLanguage.SBML.value,
                                                    ''), ([], [['XPath could not be validated.']]))
        self.assertEqual(validation.validate_target('/sbml:sbml/sbml:model/@sbml:value',
                                                    {None: 'sed-ml', 'sbml': 'sbml'},
                                                    data_model.Calculation,
                                                    data_model.ModelLanguage.SBML.value,
                                                    ''), ([], [['XPath could not be validated.']]))
        self.assertEqual(validation.validate_target(
            "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='A']/@qual:level",
            {
                None: 'sed-ml',
                'sbml': 'sbml',
                'qual': 'qual',
            },
            data_model.Calculation,
            data_model.ModelLanguage.SBML.value,
            '',
        ), ([], [['XPath could not be validated.']]))
        self.assertEqual(validation.validate_target(
            "/sbml/model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='A']/@qual:level",
            {
                None: 'sed-ml',
                'sbml': 'sbml',
                'qual': 'qual',
            },
            data_model.Calculation,
            data_model.ModelLanguage.SBML.value,
            '',
        ), ([], [['XPath could not be validated.']]))

        model_etree = etree.parse(os.path.join(os.path.dirname(__file__), '..', 'fixtures',
                                               'Chaouiya-BMC-Syst-Biol-2013-EGF-TNFa-signaling.xml'))
        self.assertEqual(validation.validate_target(
            "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']/@qual:compartment",
            {
                None: 'sed-ml',
                'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
            },
            data_model.Calculation,
            data_model.ModelLanguage.SBML.value,
            '',
            model_etree=model_etree,
            check_in_model_source=True,
        ), ([], []))

        self.assertEqual(validation.validate_target(
            "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']/@qual:level",
            {
                None: 'sed-ml',
                'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
            },
            data_model.DataGenerator,
            data_model.ModelLanguage.SBML.value,
            '',
            model_etree=model_etree,
            check_in_model_source=True,
        ), ([], []))

        self.assertIn('not a valid XML XPath',
                      flatten_nested_list_of_strings(validation.validate_target('/sbml:sbml@sbml:model',
                                                                                {None: 'sed-ml', 'sbml': 'sbml'},
                                                                                data_model.Calculation,
                                                                                data_model.ModelLanguage.SBML.value, '')[0]))
        self.assertIn('No namespaces are defined',
                      flatten_nested_list_of_strings(validation.validate_target('/sbml:sbml/sbml:model',
                                                                                {},
                                                                                data_model.Calculation,
                                                                                data_model.ModelLanguage.SBML.value, '')[0]))
        self.assertIn('Only the following namespaces are defined',
                      flatten_nested_list_of_strings(validation.validate_target('/sbml:sbml/sbml:model',
                                                                                {'sbml2': 'sbml'},
                                                                                data_model.Calculation,
                                                                                data_model.ModelLanguage.SBML.value, '')[0]))

        self.assertIn('does not match any elements of model',
                      flatten_nested_list_of_strings(validation.validate_target(
                          "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']/@qual:level",
                          {
                              None: 'sed-ml',
                              'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                              'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
                          },
                          data_model.Calculation,
                          data_model.ModelLanguage.SBML.value,
                          '',
                          model_etree=model_etree,
                          check_in_model_source=True,
                      )[0]))

        self.assertIn('does not match any elements of model',
                      flatten_nested_list_of_strings(validation.validate_target(
                          "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='ERK']/@qual:compartment",
                          {
                              None: 'sed-ml',
                              'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                              'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
                          },
                          data_model.Calculation,
                          data_model.ModelLanguage.SBML.value,
                          '',
                          model_etree=model_etree,
                          check_in_model_source=True,
                      )[0]))

        self.assertIn('matches multiple elements of model',
                      flatten_nested_list_of_strings(validation.validate_target(
                          "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies",
                          {
                              None: 'sed-ml',
                              'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                              'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
                          },
                          data_model.Calculation,
                          data_model.ModelLanguage.SBML.value,
                          '',
                          model_etree=model_etree,
                          check_in_model_source=True,
                      )[0]))

        # no validation for non-XML languages
        self.assertEqual(validation.validate_target('/sbml:sbml/sbml:model', {},
                                                    data_model.Calculation, data_model.ModelLanguage.BNGL.value, ''), ([], []))

        # no validation for references to data descriptions
        errors, warnings = validation.validate_target(
            '#dataDescription', {}, data_model.DataGenerator, language=data_model.ModelLanguage.SBML.value, model_id='')
        self.assertEqual(errors, [])
        self.assertIn('could not be validated', flatten_nested_list_of_strings(warnings))

        errors, warnings = validation.validate_target('#dataDescription', {}, data_model.Calculation,
                                                      language=data_model.ModelLanguage.SBML.value, model_id='')
        self.assertIn('are not supported', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_validate_calculation(self):
        calculation = data_model.DataGenerator(
            math='a * x + 1',
            variables=[data_model.Variable(id='x')],
            parameters=[data_model.Parameter(id='a', value=1.)],
        )
        self.assertEqual(validation.validate_calculation(calculation), ([], []))

        calculation = data_model.FunctionalRange(
            math='a * x + 1',
            variables=[data_model.Variable(id='x')],
            parameters=[],
            range=data_model.FunctionalRange(id='a'),
        )
        self.assertEqual(validation.validate_calculation(calculation), ([], []))

        calculation_2 = copy.copy(calculation)
        calculation_2.math = None
        self.assertIn('must have math', flatten_nested_list_of_strings(validation.validate_calculation(calculation_2)[0]))

        calculation_2 = copy.copy(calculation)
        calculation_2.math = 10.
        self.assertIn('must be a `string`', flatten_nested_list_of_strings(validation.validate_calculation(calculation_2)[0]))

        calculation_2 = copy.copy(calculation)
        calculation_2.math = 'a * '
        self.assertIn('The syntax', flatten_nested_list_of_strings(validation.validate_calculation(calculation_2)[0]))

        calculation_2 = copy.copy(calculation)
        calculation_2.math = 'a / 1'
        with mock.patch('biosimulators_utils.sedml.math.VALID_MATH_EXPRESSION_NODES', new_callable=mock.PropertyMock(return_value=[])):
            self.assertIn('is invalid', flatten_nested_list_of_strings(validation.validate_calculation(calculation_2)[0]))

        calculation_2 = copy.copy(calculation)
        calculation_2.math = 'a * x + y'
        self.assertIn('cannot be evaluated', flatten_nested_list_of_strings(validation.validate_calculation(calculation_2)[0]))

    def test_validate_unique_ids(self):
        doc = data_model.SedDocument(
            tasks=[
                data_model.Task(
                    id='task',
                    model=data_model.Model(
                        id='model',
                        changes=[
                            data_model.ModelAttributeChange(id='modelChange'),
                        ]
                    ),
                    simulation=data_model.UniformTimeCourseSimulation(
                        id='simulation',
                        algorithm=data_model.Algorithm(
                            changes=[
                                data_model.AlgorithmParameterChange(),
                            ]
                        )
                    )
                )
            ]
        )

        errors = validation.validate_unique_ids(doc)
        self.assertEqual(validation.validate_unique_ids(doc), [])

        doc.tasks[0].id = 'model'
        errors = validation.validate_unique_ids(doc)
        self.assertIn('must have a unique id', flatten_nested_list_of_strings(errors))
        self.assertIn('model', flatten_nested_list_of_strings(errors))

    def test_validate_output(self):
        # valid report
        task = data_model.Task()
        report = data_model.Report(
            data_sets=[
                data_model.DataSet(
                    id='x',
                    label='x',
                    data_generator=data_model.DataGenerator(
                        variables=[
                            data_model.Variable(
                                task=task
                            )
                        ]
                    )
                )
            ]
        )

        errors, warnings = validation.validate_output(report)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        # valid plot2d
        task = data_model.Task()
        plot2d = data_model.Plot2D(
            curves=[
                data_model.Curve(
                    id='curve',
                    x_data_generator=data_model.DataGenerator(
                        variables=[
                            data_model.Variable(
                                task=task
                            )
                        ]
                    ),
                    y_data_generator=data_model.DataGenerator(
                        variables=[
                            data_model.Variable(
                                task=task
                            )
                        ]
                    ),
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                )
            ]
        )

        errors, warnings = validation.validate_output(plot2d)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        # valid plot3d
        task = data_model.Task()
        plot3d = data_model.Plot3D(
            surfaces=[
                data_model.Surface(
                    id='surface',
                    x_data_generator=data_model.DataGenerator(
                        variables=[
                            data_model.Variable(
                                task=task
                            )
                        ]
                    ),
                    y_data_generator=data_model.DataGenerator(
                        variables=[
                            data_model.Variable(
                                task=task
                            )
                        ]
                    ),
                    z_data_generator=data_model.DataGenerator(
                        variables=[
                            data_model.Variable(
                                task=task
                            )
                        ]
                    ),
                    x_scale=data_model.AxisScale.linear,
                    y_scale=data_model.AxisScale.linear,
                    z_scale=data_model.AxisScale.linear,
                )
            ]
        )

        errors, warnings = validation.validate_output(plot3d)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        # error
        report.data_sets[0].id = None
        report.data_sets[0].label = None
        report.data_sets[0].data_generator.variables[0].task = data_model.RepeatedTask()
        errors, warnings = validation.validate_output(report)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('must have a label', flatten_nested_list_of_strings(errors))
        self.assertIn('experimental feature of SED-ML', flatten_nested_list_of_strings(warnings))

        plot2d.curves[0].id = None
        plot2d.curves[0].x_data_generator.variables[0].task = data_model.RepeatedTask()
        errors, warnings = validation.validate_output(plot2d)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('experimental feature of SED-ML', flatten_nested_list_of_strings(warnings))

        plot3d.surfaces[0].id = None
        plot3d.surfaces[0].x_data_generator.variables[0].task = data_model.RepeatedTask()
        errors, warnings = validation.validate_output(plot3d)
        self.assertIn('must have an id', flatten_nested_list_of_strings(errors))
        self.assertIn('experimental feature of SED-ML', flatten_nested_list_of_strings(warnings))

        report.data_sets = []
        errors, warnings = validation.validate_output(report)
        self.assertIn('must have at least one data set', flatten_nested_list_of_strings(errors))

        plot2d.curves = []
        errors, warnings = validation.validate_output(plot2d)
        self.assertIn('must have at least one curve', flatten_nested_list_of_strings(errors))

        plot3d.surfaces = []
        errors, warnings = validation.validate_output(plot3d)
        self.assertIn('must have at least one surface', flatten_nested_list_of_strings(errors))

        plot2d.curves = [
            data_model.Curve(id='c1',
                             x_data_generator=data_model.DataGenerator(),
                             y_data_generator=data_model.DataGenerator(),
                             x_scale=None,
                             y_scale=None,
                             ),
        ]
        errors, warnings = validation.validate_output(plot2d)
        self.assertIn('must have an x-scale', flatten_nested_list_of_strings(errors))

        plot3d.surfaces = [
            data_model.Surface(id='c1',
                               x_data_generator=data_model.DataGenerator(),
                               y_data_generator=data_model.DataGenerator(),
                               z_data_generator=data_model.DataGenerator(),
                               x_scale=None,
                               y_scale=None,
                               z_scale=None,
                               ),
        ]
        errors, warnings = validation.validate_output(plot3d)
        self.assertIn('must have an x-scale', flatten_nested_list_of_strings(errors))

        # warnings
        report.data_sets = [
            data_model.DataSet(
                id='d1',
                label='d',
                data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
            ),
            data_model.DataSet(
                id='d2',
                label='d',
                data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.RepeatedTask())]),
            ),
        ]
        errors, warnings = validation.validate_output(report)
        self.assertEqual(errors, [])
        self.assertIn('do not have unique labels', flatten_nested_list_of_strings(warnings))
        self.assertIn('do not have consistent shapes', flatten_nested_list_of_strings(warnings))

        plot2d.curves = [
            data_model.Curve(id='c1',
                             x_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
                             y_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.RepeatedTask())]),
                             x_scale=data_model.AxisScale.linear,
                             y_scale=data_model.AxisScale.linear,
                             ),
            data_model.Curve(id='c2',
                             x_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
                             y_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.RepeatedTask())]),
                             x_scale=data_model.AxisScale.log,
                             y_scale=data_model.AxisScale.log,
                             )
        ]
        errors, warnings = validation.validate_output(plot2d)
        self.assertEqual(errors, [])
        self.assertIn('Curves do not have consistent x-scales.', flatten_nested_list_of_strings(warnings))
        self.assertIn('Curves do not have consistent y-scales.', flatten_nested_list_of_strings(warnings))
        self.assertIn('do not have consistent shapes', flatten_nested_list_of_strings(warnings))

        plot3d.surfaces = [
            data_model.Surface(id='s1',
                               x_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
                               y_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
                               z_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.RepeatedTask())]),
                               x_scale=data_model.AxisScale.linear,
                               y_scale=data_model.AxisScale.linear,
                               z_scale=data_model.AxisScale.linear,
                               ),
            data_model.Surface(id='s2',
                               x_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
                               y_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.Task())]),
                               z_data_generator=data_model.DataGenerator(variables=[data_model.Variable(task=data_model.RepeatedTask())]),
                               x_scale=data_model.AxisScale.log,
                               y_scale=data_model.AxisScale.log,
                               z_scale=data_model.AxisScale.log,
                               ),
        ]
        errors, warnings = validation.validate_output(plot3d)
        self.assertEqual(errors, [])
        self.assertIn('Surfaces do not have consistent x-scales.', flatten_nested_list_of_strings(warnings))
        self.assertIn('Surfaces do not have consistent y-scales.', flatten_nested_list_of_strings(warnings))
        self.assertIn('Surfaces do not have consistent z-scales.', flatten_nested_list_of_strings(warnings))
        self.assertIn('do not have consistent shapes', flatten_nested_list_of_strings(warnings))

        errors, warnings = validation.validate_data_generator_variables([
            data_model.Variable(id='v1', symbol=data_model.Symbol.time.value, task=data_model.Task()),
            data_model.Variable(id='v2', symbol=data_model.Symbol.time.value, task=data_model.RepeatedTask()),
        ])
        self.assertEqual(errors, [])
        self.assertIn('do not have consistent shapes', flatten_nested_list_of_strings(warnings))
