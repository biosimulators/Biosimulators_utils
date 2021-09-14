from biosimulators_utils.model_lang.xpp.utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.sedml.data_model import UniformTimeCourseSimulation, Symbol, Plot2D, AxisScale
import os
import unittest


class XppUtilsTestCase(unittest.TestCase):
    FIXTURES_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'xpp')

    def test_get_parameters_variables_for_simulation(self):
        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan.ode')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(filename, None, UniformTimeCourseSimulation)

        self.assertEqual(len(params), 12 + 2)

        self.assertEqual(params[0].id, 'parameter_aee')
        self.assertEqual(params[0].name, 'Value of parameter "aee"')
        self.assertEqual(params[0].target, 'aee')
        self.assertEqual(params[0].new_value, '10.0')

        self.assertEqual(params[12].id, 'initial_condition_U')
        self.assertEqual(params[12].name, 'Initial condition of "U"')
        self.assertEqual(params[12].target, 'U')
        self.assertEqual(params[12].new_value, '0.1')

        self.assertEqual(len(sims), 1)
        sim = sims[0]
        self.assertEqual(sim.initial_time, 0.)
        self.assertEqual(sim.output_start_time, 0.)
        self.assertEqual(sim.output_end_time, 40.)
        self.assertEqual(sim.number_of_steps, round(40. / 0.05))
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000032')
        self.assertEqual(sim.algorithm.changes, [])

        self.assertEqual(len(vars), 3)

        self.assertEqual(vars[0].id, 'time')
        self.assertEqual(vars[0].name, 'Time')
        self.assertEqual(vars[0].symbol, Symbol.time.value)

        self.assertEqual(vars[-1].id, 'dynamics_V')
        self.assertEqual(vars[-1].name, 'Dynamics of "V"')
        self.assertEqual(vars[-1].target, 'V')

        self.assertEqual(len(plots), 1)        
        plot = plots[0]
        self.assertIsInstance(plot, Plot2D)
        self.assertEqual(len(plot.curves), 1)
        curve = plot.curves[0]
        self.assertEqual(len(curve.x_data_generator.variables), 1)
        self.assertEqual(len(curve.y_data_generator.variables), 1)
        self.assertEqual(curve.x_data_generator.variables[0].target, 'U')
        self.assertEqual(curve.y_data_generator.variables[0].target, 'V')
        self.assertEqual(curve.x_scale, AxisScale.linear)
        self.assertEqual(curve.y_scale, AxisScale.linear)

        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan-modified-2.ode')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(filename, None, UniformTimeCourseSimulation)
        sim = sims[0]
        self.assertEqual(sim.initial_time, 10.)
        self.assertEqual(sim.output_start_time, 10.)
        self.assertEqual(sim.output_end_time, 50.)
        self.assertEqual(sim.number_of_steps, round(40. / (0.1 * 10)))
        self.assertEqual(len(sim.algorithm.changes), 4)
        self.assertEqual({change.kisao_id: change.new_value for change in sim.algorithm.changes}, {
            'KISAO_0000209': '1e-8',
            'KISAO_0000211': '1e-6',
            'KISAO_0000480': '8',
            'KISAO_0000479': '12'
        })

        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan-auxiliary-variables.ode')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(filename, None, UniformTimeCourseSimulation)
        self.assertEqual(vars[-1].id, 'dynamics_dv')
        self.assertEqual(vars[-1].name, 'Dynamics of "dv"')
        self.assertEqual(vars[-1].target, 'dv')

    def test_get_parameters_variables_for_simulation_native_ids_data_types(self):
        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan.ode')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            filename, None, UniformTimeCourseSimulation,
            native_ids=True, native_data_types=True)

        self.assertEqual(len(params), 12 + 2)

        self.assertEqual(params[0].id, 'aee')
        self.assertEqual(params[0].name, None)
        self.assertEqual(params[0].target, 'aee')
        self.assertEqual(params[0].new_value, 10.0)

        self.assertEqual(params[12].id, 'U')
        self.assertEqual(params[12].name, None)
        self.assertEqual(params[12].target, 'U')
        self.assertEqual(params[12].new_value, 0.1)

        self.assertEqual(len(sims), 1)
        sim = sims[0]
        self.assertEqual(sim.initial_time, 0.)
        self.assertEqual(sim.output_start_time, 0.)
        self.assertEqual(sim.output_end_time, 40.)
        self.assertEqual(sim.number_of_steps, round(40. / 0.05))
        self.assertEqual(sim.algorithm.kisao_id, 'KISAO_0000032')
        self.assertEqual(sim.algorithm.changes, [])

        self.assertEqual(len(vars), 3)

        self.assertEqual(vars[0].id, None)
        self.assertEqual(vars[0].name, None)
        self.assertEqual(vars[0].symbol, Symbol.time.value)

        self.assertEqual(vars[-1].id, 'V')
        self.assertEqual(vars[-1].name, None)
        self.assertEqual(vars[-1].target, 'V')

        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan-modified-2.ode')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            filename, None, UniformTimeCourseSimulation,
            native_ids=True, native_data_types=True)
        sim = sims[0]
        self.assertEqual(sim.initial_time, 10.)
        self.assertEqual(sim.output_start_time, 10.)
        self.assertEqual(sim.output_end_time, 50.)
        self.assertEqual(sim.number_of_steps, round(40. / (0.1 * 10)))
        self.assertEqual(len(sim.algorithm.changes), 4)
        self.assertEqual({change.kisao_id: change.new_value for change in sim.algorithm.changes}, {
            'KISAO_0000209': 1e-8,
            'KISAO_0000211': 1e-6,
            'KISAO_0000480': 8,
            'KISAO_0000479': 12,
        })

        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan-auxiliary-variables.ode')
        params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
            filename, None, UniformTimeCourseSimulation,
            native_ids=True, native_data_types=True)
        self.assertEqual(vars[-1].id, 'dv')
        self.assertEqual(vars[-1].name, None)
        self.assertEqual(vars[-1].target, 'dv')

    def test_get_parameters_variables_for_simulation_error_handling(self):
        with self.assertRaises(ValueError):
            get_parameters_variables_outputs_for_simulation(None, None, None)

        filename = os.path.join(self.FIXTURES_DIRNAME, 'wilson-cowan.ode')
        with self.assertRaises(NotImplementedError):
            get_parameters_variables_outputs_for_simulation(filename, None, None)
