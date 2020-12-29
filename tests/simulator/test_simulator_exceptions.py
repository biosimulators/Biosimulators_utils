from biosimulators_utils.simulator import exceptions as simulator_exceptions
import unittest


class SimulatorExceptionsTestCase(unittest.TestCase):
    def test(self):
        simulator_exceptions.AlgorithmDoesNotSupportModelFeatureException()
