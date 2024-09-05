from biosimulators_utils.model_lang.rba.utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.sedml.data_model import SteadyStateSimulation
import math
import os
import unittest


class RbaUtilsTestCase(unittest.TestCase):
    FIXTURES_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'rba')

    def test_get_parameters_variables_for_simulation(self):
        filename = os.path.join(self.FIXTURES_DIRNAME, 'Escherichia-coli-K12-WT.zip')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(filename, None, SteadyStateSimulation)

        self.assertEqual(len(params), 1620)

        param = next(param for param in params if param.id == 'parameter_amino_acid_concentration_Y_MIN')
        self.assertEqual(param.name, 'Value of parameter "Y_MIN" of function "amino_acid_concentration"')
        self.assertEqual(param.target, 'parameters.functions.amino_acid_concentration.parameters.Y_MIN')
        self.assertEqual(param.new_value, '-inf')

        self.assertEqual(len(sims), 1)
        sim = sims[0]
        self.assertIsInstance(sim, SteadyStateSimulation)
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000669')
        self.assertEqual(sim.algorithm.changes, [])

        self.assertEqual(len(vars), 15766)

        self.assertEqual(vars[0].id, 'objective')
        self.assertEqual(vars[0].name, 'Value of objective')
        self.assertEqual(vars[0].target, 'objective')

        var = next(var for var in vars if var.id == 'M_pqq_p')
        self.assertEqual(var.name, 'Dual of constraint "M_pqq_p"')
        self.assertEqual(var.target, 'constraints.M_pqq_p')

        var = next(var for var in vars if var.id == 'test_process_2_machinery')
        self.assertEqual(var.name, 'Primal of variable "test_process_2_machinery"')
        self.assertEqual(var.target, 'variables.test_process_2_machinery')

    def test_get_parameters_variables_for_simulation_native_ids_data_types(self):
        filename = os.path.join(self.FIXTURES_DIRNAME, 'Escherichia-coli-K12-WT.zip')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(filename, None, SteadyStateSimulation, native_ids=True, native_data_types=True)

        self.assertEqual(len(params), 1620)

        param = next(param for param in params if param.id == 'amino_acid_concentration.Y_MIN')
        self.assertEqual(param.name, None)
        self.assertEqual(param.target, 'parameters.functions.amino_acid_concentration.parameters.Y_MIN')
        self.assertEqual(param.new_value, -math.inf)

        self.assertEqual(len(sims), 1)
        sim = sims[0]
        self.assertIsInstance(sim, SteadyStateSimulation)
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000669')
        self.assertEqual(sim.algorithm.changes, [])

        self.assertEqual(len(vars), 15766)

        self.assertEqual(vars[0].id, None)
        self.assertEqual(vars[0].name, None)
        self.assertEqual(vars[0].target, 'objective')

        var = next(var for var in vars if var.id == 'M_pqq_p')
        self.assertEqual(var.name, None)
        self.assertEqual(var.target, 'constraints.M_pqq_p')

        var = next(var for var in vars if var.id == 'test_process_2_machinery')
        self.assertEqual(var.name, None)
        self.assertEqual(var.target, 'variables.test_process_2_machinery')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaises(ValueError):
            get_parameters_variables_outputs_for_simulation(None, None, None)

        filename = os.path.join(self.FIXTURES_DIRNAME, 'Escherichia-coli-K12-WT.zip')
        with self.assertRaises(NotImplementedError):
            get_parameters_variables_outputs_for_simulation(filename, None, None)
