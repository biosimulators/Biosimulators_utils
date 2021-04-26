from biosimulators_utils.kisao import core
from biosimulators_utils.kisao import data_model
from unittest import mock
import os
import pronto
import shutil
import tempfile
import unittest


class KisaoCoreTestCase(unittest.TestCase):
    def test_get_latest_version(self):
        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: None, json=lambda: [{'name': '2.14'}])):
            self.assertEqual(core.get_latest_version(), '2.14')

    def test_get_installation_dirname(self):
        self.assertIn('BioSimulatorsUtils', core.get_installation_dirname())
        self.assertIn('kisao', core.get_installation_dirname())

    def test_get_installation_filename(self):
        self.assertIn('BioSimulatorsUtils', core.get_installation_filename('2.14'))
        self.assertIn('kisao', core.get_installation_filename('2.14'))
        self.assertIn('2.14', core.get_installation_filename('2.14'))

    def test_get_installed_versions(self):
        dirname = tempfile.mkdtemp()

        self.assertEqual(core.get_installed_versions(dirname), [])

        with open(os.path.join(dirname, '2.14.owl'), 'w'):
            pass
        with open(os.path.join(dirname, '2.13.owl'), 'w'):
            pass

        self.assertEqual(core.get_installed_versions(dirname), ['2.14', '2.13'])

        shutil.rmtree(dirname)

    def test_download(self):
        with open(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'kisao-2.14.owl'), 'rb') as file:
            content = file.read()
        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: None, content=content)):
            content = core.download(version=2.14)
        fid, filename = tempfile.mkstemp()
        os.close(fid)
        with open(filename, 'wb') as file:
            file.write(content)

        onto = core.read_ontology(filename)
        self.assertEqual(onto.metadata.ontology, data_model.NAMESPACE)

    def test_install(self):
        dirname = tempfile.mkdtemp()
        shutil.rmtree(dirname)

        with open(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'kisao-2.14.owl'), 'rb') as file:
            content = file.read()
        with mock.patch('requests.get', side_effect=[
            mock.Mock(raise_for_status=lambda: None, json=lambda: [{'name': '2.14'}]),
            mock.Mock(raise_for_status=lambda: None, content=content),
        ]):
            version, filename = core.install(version=None, dirname=dirname)
        onto = core.read_ontology(filename)
        self.assertEqual(onto.metadata.ontology, data_model.NAMESPACE)

        shutil.rmtree(dirname)

    def test_load(self):
        dirname = tempfile.mkdtemp()

        with open(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'kisao-2.14.owl'), 'rb') as file:
            content214 = file.read()
        with open(os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'kisao-2.13.owl'), 'rb') as file:
            content213 = file.read()

        def requests_get(url):
            if url.startswith(core.KISAO_TAGS_ENDPOINT):
                response = mock.Mock(raise_for_status=lambda: None, json=lambda: [{'name': '2.14'}])
            elif '2.14' in url:
                response = mock.Mock(raise_for_status=lambda: None, content=content214)
            else:
                response = mock.Mock(raise_for_status=lambda: None, content=content213)
            return response

        with mock.patch('requests.get', side_effect=requests_get):
            onto = core.load(version=None, dirname=dirname)
            onto = core.load(version=None, dirname=dirname)
            core.install(version='2.13', dirname=dirname)
            onto = core.load(version='2.13', dirname=dirname)
            self.assertEqual(onto.metadata.ontology, data_model.NAMESPACE)

            onto = core.load(dirname=dirname, check_for_latest=True)
            self.assertEqual(onto.metadata.ontology, data_model.NAMESPACE)

            shutil.rmtree(dirname)

            dirname = tempfile.mkdtemp()

            core.install(version='2.13', dirname=dirname)
            onto = core.load(dirname=dirname, check_for_latest=True)
            self.assertEqual(onto.metadata.ontology, data_model.NAMESPACE)

        shutil.rmtree(dirname)

    def test_get_term_ids(self):
        children = core.get_child_terms('KISAO_0000433')
        self.assertIn('KISAO_0000019', core.get_term_ids(children))

    def test_get(self):
        onto = core.get()
        self.assertEqual(onto.metadata.ontology, data_model.NAMESPACE)

    def test_get_term(self):
        term = core.get_term('KISAO_0000377')
        self.assertEqual(term.id, data_model.NAMESPACE + 'KISAO_0000377')

    def test_get_child_terms(self):
        terms = core.get_child_terms('KISAO_0000377')
        self.assertIn('KISAO_0000261', [term.id.partition('#')[2] for term in terms])

    def test_get_parent_terms(self):
        terms = core.get_parent_terms('KISAO_0000377')
        self.assertEqual(terms[0].id, data_model.NAMESPACE + 'KISAO_0000000')
