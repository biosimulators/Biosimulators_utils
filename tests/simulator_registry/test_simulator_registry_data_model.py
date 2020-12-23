from biosimulators_utils.simulator_registry import data_model
import unittest


class DataModelTestCase(unittest.TestCase):
    def test(self):
        sim1 = data_model.SimulatorSubmission(
            id='tellurium',
            version='2.1.6',
            specifications_url='https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json',
            specifications_patch={'version': '2.1.5'},
        )
        sim2 = data_model.SimulatorSubmission(
            id='tellurium',
            version='2.1.6',
            specifications_url='https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json',
            specifications_patch={'version': '2.1.5'},
        )
        sim3 = data_model.SimulatorSubmission(
            id='tellurium',
            version='2.1.5',
            specifications_url='https://raw.githubusercontent.com/biosimulators/Biosimulators_tellurium/dev/biosimulators.json',
            specifications_patch={'version': '2.1.5'},
        )

        self.assertEqual(sim1.to_tuple(), (sim1.id, sim1.version, sim1.specifications_url, sim1.specifications_patch,
                                           sim1.validate_image, sim1.commit_simulator,
                                           ))

        self.assertTrue(sim1.is_equal(sim2))
        self.assertFalse(sim1.is_equal(sim3))
