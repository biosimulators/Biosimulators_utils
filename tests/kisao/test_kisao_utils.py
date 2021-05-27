from biosimulators_utils.kisao import utils
import pronto
import unittest


class KisaoUtilsTestCase(unittest.TestCase):
    def test_get_term(self):
        term = utils.get_term('KISAO_0000019')
        self.assertIsInstance(term, pronto.Term)

        term = utils.get_term('KISAO:0000019')
        self.assertEqual(term, None)

        term = utils.get_term('KISAO_9999999')
        self.assertEqual(term, None)

        term = utils.get_term('x')
        self.assertEqual(term, None)

        term = utils.get_term(None)
        self.assertEqual(term, None)

    def test_get_term_type(self):
        term_type = utils.get_term_type(utils.get_term('KISAO_0000000'))
        self.assertEqual(term_type, utils.TermType.root)

        term_type = utils.get_term_type(utils.get_term('KISAO_0000019'))
        self.assertEqual(term_type, utils.TermType.algorithm)

        term_type = utils.get_term_type(utils.get_term('KISAO_0000575'))
        self.assertEqual(term_type, utils.TermType.algorithm)

        term_type = utils.get_term_type(utils.get_term('KISAO_0000211'))
        self.assertEqual(term_type, utils.TermType.algorithm_parameter)

        term_type = utils.get_term_type(utils.get_term('KISAO_0000322'))
        self.assertEqual(term_type, utils.TermType.algorithm_characteristic)

        term_type = utils.get_term_type(utils.get_term('x'))
        self.assertEqual(term_type, None)

        term_type = utils.get_term_type(utils.get_term(None))
        self.assertEqual(term_type, None)
