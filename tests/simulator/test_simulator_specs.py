from biosimulators_utils.sedml.data_model import Algorithm, AlgorithmParameterChange
from biosimulators_utils.simulator.specs import gen_algorithms_from_specs
import os
import unittest


class SimulatorSpecsTestCase(unittest.TestCase):
    def test(self):
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
