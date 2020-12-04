from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import exec
from lxml import etree
import mock
import os
import shutil
import tempfile
import unittest


class ExecTestCase(unittest.TestCase):
    FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '../fixtures/sbml-list-of-species.xml')

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        changes = [
            data_model.ModelAttributeChange(
                name='c1',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialConcentration",
                new_value='1.9'),
            data_model.ModelAttributeChange(
                name='c1',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']/@sboTerm",
                new_value='SBO:0000001'),
        ]
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        exec.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename)

        et = etree.parse(out_filename)
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}
        self.assertEqual(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                                  namespaces=namespaces)[0].get('initialConcentration'),
                         changes[0].new_value)
        self.assertEqual(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
                                  namespaces=namespaces)[0].get('sboTerm'),
                         changes[1].new_value)

    def test_errors(self):
        changes = [
            mock.MagicMock(
                name='c1',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialConcentration",
                new_value='1.9'),
        ]
        with self.assertRaises(NotImplementedError):
            exec.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.ModelAttributeChange(
                name='c1',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                new_value='1.9'),
        ]
        with self.assertRaises(ValueError):
            exec.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.ModelAttributeChange(
                name='c1',
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/@initialConcentration",
                new_value='1.9'),
        ]
        with self.assertRaises(ValueError):
            exec.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)
