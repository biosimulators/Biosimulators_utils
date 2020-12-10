from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import utils
from biosimulators_utils.utils.core import are_lists_equal
from lxml import etree
from unittest import mock
import os
import shutil
import tempfile
import unittest


class SedmlUtilsTestCase(unittest.TestCase):
    def test_get_variables_for_task(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(id='model1'))
        doc.models.append(data_model.Model(id='model2'))
        doc.tasks.append(data_model.Task(id='task1', model=doc.models[0]))
        doc.tasks.append(data_model.Task(id='task2', model=doc.models[1]))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.DataGeneratorVariable(
                    id='var_1_1',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
                data_model.DataGeneratorVariable(
                    id='var_1_2',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
            ]
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_2',
            variables=[
                data_model.DataGeneratorVariable(
                    id='var_2_1',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
                data_model.DataGeneratorVariable(
                    id='var_2_2',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
            ]
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_3',
            variables=[
                data_model.DataGeneratorVariable(
                    id='var_3_1',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
                data_model.DataGeneratorVariable(
                    id='var_3_2',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
            ]
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_4',
            variables=[
                data_model.DataGeneratorVariable(
                    id='var_4_1',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
                data_model.DataGeneratorVariable(
                    id='var_4_2',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
            ]
        ))
        self.assertTrue(are_lists_equal(
            utils.get_variables_for_task(doc, doc.tasks[0]),
            [
                doc.data_generators[0].variables[0],
                doc.data_generators[0].variables[1],
                doc.data_generators[1].variables[0],
                doc.data_generators[1].variables[1],
            ],
        ))
        self.assertTrue(are_lists_equal(
            utils.get_variables_for_task(doc, doc.tasks[1]),
            [
                doc.data_generators[2].variables[0],
                doc.data_generators[2].variables[1],
                doc.data_generators[3].variables[0],
                doc.data_generators[3].variables[1],
            ],
        ))


class ApplyModelChangesTestCase(unittest.TestCase):
    FIXTURE_FILENAME = os.path.join(os.path.dirname(__file__), '../fixtures/sbml-list-of-species.xml')

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        changes = [
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialConcentration",
                new_value='1.9'),
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']/@sboTerm",
                new_value='SBO:0000001'),
        ]
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename)

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
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                new_value='1.9'),
        ]
        with self.assertRaises(ValueError):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/@initialConcentration",
                new_value='1.9'),
        ]
        with self.assertRaises(ValueError):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)
