from biosimulators_utils.kisao import data_model
from biosimulators_utils.kisao import utils
import os
import pronto
import shutil
import tempfile
import unittest


class KisaoUtilsTestCase(unittest.TestCase):
    def test_normalize_kisao_id(self):
        self.assertEqual(utils.normalize_kisao_id('KISAO_0000029'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id('KISAO:0000029'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id('29'), 'KISAO_0000029')
        self.assertEqual(utils.normalize_kisao_id(29), 'KISAO_0000029')
        with self.assertWarnsRegex(UserWarning, 'likely not an id'):
            self.assertEqual(utils.normalize_kisao_id('X'), 'X')

    def test_get_ode_integration_kisao_term_ids(self):
        term_ids = utils.get_ode_integration_kisao_term_ids()
        self.assertIn('KISAO_0000019', term_ids)
        self.assertIn('KISAO_0000560', term_ids)
        self.assertNotIn('KISAO_0000029', term_ids)
