from kisao import Kisao
import unittest


class KisaoCoreTestCase(unittest.TestCase):
    def test_get_ode_integration_kisao_term_ids(self):
        kisao = Kisao()
        term_ids = [term.id.partition('#')[2] for term in kisao.get_ode_algorithms()]
        self.assertIn('KISAO_0000019', term_ids)
        self.assertIn('KISAO_0000560', term_ids)
        self.assertNotIn('KISAO_0000029', term_ids)
