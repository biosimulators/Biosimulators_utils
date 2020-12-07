from biosimulators_utils.kisao import utils
import unittest


class KisaoUtilsTestCase(unittest.TestCase):
    def test(self):
        self.assertEqual(utils.normalize_kisao_id('KISAO_0000029'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id('KISAO:0000029'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id('29'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id(29), 'KISAO_0000029')
        with self.assertWarnsRegex(UserWarning, 'likely not an id'):
            self.assertEqual(utils.normalize_kisao_id('X'), 'X')
