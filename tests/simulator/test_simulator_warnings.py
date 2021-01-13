from biosimulators_utils.simulator.warnings import AlgorithmSubstitutedWarning
from biosimulators_utils.warnings import warn
import unittest


class SimulatorWarningsTestCase(unittest.TestCase):
    def test(self):
        warn('Alternate algorithm used', AlgorithmSubstitutedWarning)
