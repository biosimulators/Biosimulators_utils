from biosimulators_utils.simulator import warnings as simulator_warnings
import unittest
import warnings


class SimulatorWarningsTestCase(unittest.TestCase):
    def test(self):
        warnings.warn('Alternate algorithm used', simulator_warnings.AlternateAlgorithmWarning)
