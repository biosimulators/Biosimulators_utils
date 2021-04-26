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

    def test_get_latest_version(self):
        self.assertGreaterEqual(utils.get_latest_version().split('.'), '2.13'.split('.'))

    def test_get_installation_dirname(self):
        self.assertIn('BioSimulatorsUtils', utils.get_installation_dirname())
        self.assertIn('kisao', utils.get_installation_dirname())

    def test_get_installation_filename(self):
        self.assertIn('BioSimulatorsUtils', utils.get_installation_filename('2.14'))
        self.assertIn('kisao', utils.get_installation_filename('2.14'))
        self.assertIn('2.14', utils.get_installation_filename('2.14'))

    def test_get_installed_versions(self):
        dirname = tempfile.mkdtemp()

        self.assertEqual(utils.get_installed_versions(dirname), [])

        with open(os.path.join(dirname, '2.14.owl'), 'w'):
            pass
        with open(os.path.join(dirname, '2.13.owl'), 'w'):
            pass

        self.assertEqual(utils.get_installed_versions(dirname), ['2.14', '2.13'])

        shutil.rmtree(dirname)

    def test_download(self):
        content = utils.download(version=2.14)
        fid, filename = tempfile.mkstemp()
        os.close(fid)
        with open(filename, 'wb') as file:
            file.write(content)

        onto = utils.read_ontology(filename)
        self.assertEqual(onto.metadata.ontology, utils.NAMESPACE)

    def test_install(self):
        dirname = tempfile.mkdtemp()
        version, filename = utils.install(version=None, dirname=dirname)
        onto = utils.read_ontology(filename)
        self.assertEqual(onto.metadata.ontology, utils.NAMESPACE)
        shutil.rmtree(dirname)

    def test_load(self):
        dirname = tempfile.mkdtemp()

        onto = utils.load(dirname=dirname)
        self.assertEqual(onto.metadata.ontology, utils.NAMESPACE)

        onto = utils.load(dirname=dirname, check_for_latest=True)
        self.assertEqual(onto.metadata.ontology, utils.NAMESPACE)

        shutil.rmtree(dirname)

    def test_get(self):
        onto = utils.get()
        self.assertEqual(onto.metadata.ontology, utils.NAMESPACE)

    def test_get_term(self):
        term = utils.get_term('KISAO_0000377')
        self.assertEqual(term.id, utils.NAMESPACE + 'KISAO_0000377')

    def test_get_child_terms(self):
        terms = utils.get_child_terms('KISAO_0000377')
        self.assertIn('KISAO_0000261', [term.id.partition('#')[2] for term in terms])

    def test_get_parent_terms(self):
        terms = utils.get_parent_terms('KISAO_0000377')
        self.assertEqual(terms[0].id, utils.NAMESPACE + 'KISAO_0000000')
