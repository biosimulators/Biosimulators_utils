from unittest import mock
import unittest


class GurobiLicenseManagerTestCase(unittest.TestCase):
    def test(self):
        mock_gurobipy = mock.Mock()

        class Model():
            def __init__(self, env=None):
                self.env = env

        class Env():
            def __init__(self, params=None):
                self.params = params

        mock_gurobipy.Model = Model
        mock_gurobipy.Env = Env

        with mock.patch.dict('sys.modules', gurobipy=mock_gurobipy):
            from biosimulators_utils.licensing.gurobi import GurobiLicenseManager

            import gurobipy

            model = gurobipy.Model()
            self.assertEqual(model.env, None)

            with mock.patch.dict('os.environ', {'GRB_LICENSEID': '1234'}):
                with GurobiLicenseManager():
                    model = gurobipy.Model()
                    self.assertEqual(model.env.params, {
                        'LICENSEID': 1234,
                    })

            model = gurobipy.Model()
            self.assertEqual(model.env, None)

        with mock.patch.dict('sys.modules', gurobipy=None):
            from biosimulators_utils.licensing.gurobi import GurobiLicenseManager

            with self.assertRaises(ModuleNotFoundError):
                import gurobipy

            with mock.patch.dict('os.environ', {'GRB_LICENSEID': '1234'}):
                with GurobiLicenseManager():
                    pass
