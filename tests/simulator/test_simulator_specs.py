from biosimulators_utils.sedml.data_model import (
    SedDocument, Task, RepeatedTask, SubTask, Model, ModelLanguage,
    UniformTimeCourseSimulation, OneStepSimulation, Algorithm, AlgorithmParameterChange,
)
from biosimulators_utils.simulator.specs import (
    get_simulator_specs,
    does_simulator_have_capabilities_to_execute_sed_document,
    gen_algorithms_from_specs,
)
from kisao.data_model import AlgorithmSubstitutionPolicy
import copy
import os
import unittest


class SimulatorSpecsTestCase(unittest.TestCase):

    def test_get_simulator_specs(self):
        specs = get_simulator_specs('copasi', 'latest')
        self.assertEqual(specs['id'], 'copasi')
        self.assertIsInstance(specs['algorithms'], list)
        for alg_specs in specs['algorithms']:
            self.assertIsInstance(alg_specs, dict)

        self.assertRegex(specs['version'], r'\d+\.\d+\.\d+$')

        specs = get_simulator_specs('copasi', specs['version'])
        self.assertEqual(specs['id'], 'copasi')
        self.assertIsInstance(specs['algorithms'], list)
        for alg_specs in specs['algorithms']:
            self.assertIsInstance(alg_specs, dict)

    def test_does_simulator_have_capabilities_to_execute_sed_document(self):
        specs = get_simulator_specs('tellurium', 'latest')
        doc = SedDocument(
            tasks=[
                Task(
                    model=Model(
                        language=ModelLanguage.SBML.value,
                    ),
                    simulation=UniformTimeCourseSimulation(
                        algorithm=Algorithm(
                            kisao_id='KISAO_0000019',
                            changes=[
                                AlgorithmParameterChange(kisao_id='KISAO_0000209')
                            ]
                        )
                    )
                )
            ]
        )

        self.assertTrue(does_simulator_have_capabilities_to_execute_sed_document(doc, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        doc2 = copy.deepcopy(doc)
        doc2.tasks.append(RepeatedTask(
            sub_tasks=[
                SubTask(task=copy.deepcopy(doc2.tasks[0]))
            ],
        ))
        self.assertTrue(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        doc2 = copy.deepcopy(doc)
        doc2.tasks.append(RepeatedTask(
            sub_tasks=[
                SubTask(task=copy.deepcopy(doc2.tasks[0]))
            ],
        ))
        doc2.tasks[1].sub_tasks[0].task.model.language = ModelLanguage.CellML.value
        self.assertFalse(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].model.language = ModelLanguage.CellML.value
        self.assertFalse(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].model.language = 'urn:sedml:language:unknown'
        self.assertFalse(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].simulation.algorithm.kisao_id = 'KISAO_0000088'
        self.assertFalse(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].simulation.algorithm.kisao_id = 'KISAO_0000088'
        self.assertTrue(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_VARIABLES))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].simulation.algorithm.kisao_id = 'KISAO_0000560'
        self.assertTrue(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_VARIABLES))

        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].simulation.algorithm.changes[0].kisao_id = 'KISAO_0000019'
        self.assertFalse(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

        specs = get_simulator_specs('pysces', 'latest')
        doc2 = copy.deepcopy(doc)
        doc2.tasks[0].simulation = OneStepSimulation(algorithm=Algorithm(kisao_id='KISAO_0000019'))
        self.assertFalse(does_simulator_have_capabilities_to_execute_sed_document(doc2, specs, alg_substitution_policy=AlgorithmSubstitutionPolicy.SAME_METHOD))

    def test_gen_algorithms_from_specs(self):
        algs = gen_algorithms_from_specs(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'tellurium.json'))

        self.assertEqual(len(algs), 5)
        self.assertTrue(
            algs['KISAO_0000086'].is_equal(
                Algorithm(
                    kisao_id='KISAO_0000086',
                    changes=[
                        AlgorithmParameterChange(kisao_id='KISAO_0000107', new_value='true'),
                        AlgorithmParameterChange(kisao_id='KISAO_0000485', new_value='1e-12'),
                        AlgorithmParameterChange(kisao_id='KISAO_0000467', new_value='1.0'),
                    ],
                ),
            )
        )
