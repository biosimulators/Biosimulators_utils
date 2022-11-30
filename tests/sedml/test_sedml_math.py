import math
import unittest

import libsedml

from biosimulators_utils.sedml import math as sedml_math


class MathTestCase(unittest.TestCase):
    def test_log(self):
        self.assertEqual(sedml_math.log(10), 1.)
        self.assertEqual(sedml_math.log(100, 10000), 2.)

    def test_piecewise(self):
        self.assertEqual(sedml_math.piecewise(1, True, 2, False, 3), 1)
        self.assertEqual(sedml_math.piecewise(1, False, 2, True, 3), 2)
        self.assertEqual(sedml_math.piecewise(1, False, 2, False, 3), 3)
        self.assertTrue(math.isnan(sedml_math.piecewise(1, False, 2, False)))

    def test_python_infix_operator_substitutions(self):
        test_cases = {
            "2.0 ^ 3": 8.0,
            "2 ^ 3": 8.0,
            "2.0 ^ 3.0": 8.0,
            "2 ^ 3.0": 8.0,
            "0.0 && 0.0": 0.0,
            "1.0 && 0.0": 0.0,
            "1 && 1": 1.0,
            "0.0 || 0.0": 0.0,
            "1.0 || 0.0": 1.0,
            "1 || 1": 1.0
        }
        for (orig_infix, expected_value) in test_cases.items():
            # round trip to libsedml to ensure proper integration
            ast_node = libsedml.parseL3Formula(orig_infix)
            infix: str = libsedml.formulaToL3String(ast_node)
            compiled_math = sedml_math.compile_math(infix)
            self.assertEqual(sedml_math.eval_math(infix, compiled_math, {}), expected_value)

    def test_compile_eval_math(self):
        math = '1 + 2'
        workspace = {}
        compiled_math = sedml_math.compile_math(math)
        self.assertEqual(sedml_math.eval_math(math, compiled_math, workspace), 3)

        math = 'x + 2'
        workspace = {'x': 1}
        compiled_math = sedml_math.compile_math(math)
        self.assertEqual(sedml_math.eval_math(math, compiled_math, workspace), 3)

        math = 'x * 2'
        workspace = {'x': 1}
        compiled_math = sedml_math.compile_math(math)
        self.assertEqual(sedml_math.eval_math(math, compiled_math, workspace), 2.0)

        math = 'x / 2'
        workspace = {'x': 1}
        compiled_math = sedml_math.compile_math(math)
        self.assertEqual(sedml_math.eval_math(math, compiled_math, workspace), 0.5)

    def test_eval_math_error_handling(self):
        with self.assertRaisesRegex(ValueError, 'cannot have ids equal to the following reserved symbols'):
            sedml_math.eval_math('pi', 'pi', {'pi': 3.14})
