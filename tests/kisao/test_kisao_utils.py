from biosimulators_utils.kisao import utils
import unittest


class KisaoUtilsTestCase(unittest.TestCase):
    def test_normalize_kisao_id(self):
        self.assertEqual(utils.normalize_kisao_id('KISAO_0000029'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id('KISAO:0000029'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id('29'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id(29), 'KISAO_0000029')
        with self.assertWarnsRegex(UserWarning, 'likely not an id'):
            self.assertEqual(utils.normalize_kisao_id('X'), 'X')

    def test_get_url_for_term(self):
        utils.get_url_for_term('KISAO_0000029')
