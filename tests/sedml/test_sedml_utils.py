from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml import utils
from biosimulators_utils.utils.core import are_lists_equal
from biosimulators_utils.xml.utils import get_namespaces_for_xml_doc, get_namespaces_with_prefixes
from lxml import etree
from unittest import mock
import copy
import libsedml
import numpy
import numpy.testing
import os
import shutil
import tempfile
import unittest


class SedmlUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_resolve_model(self):
        doc = data_model.SedDocument(
            models=[
                data_model.Model(id='model_0', source='model_0.xml', changes=[1, 2]),
                data_model.Model(id='model_1', source=os.path.join(self.tmp_dir, 'model_1.xml'), changes=[3, 4]),
                data_model.Model(id='model_2', source='#model_0', changes=[5]),
                data_model.Model(id='model_3', source='#model_2', changes=[6, 7]),
                data_model.Model(id='model_4', source='https://server.edu/model.xml', changes=[8]),
                data_model.Model(id='model_5', source='urn:miriam:biomodels.db:123', changes=[9]),
                data_model.Model(id='model_6', source='#model_5', changes=[10]),
            ],
        )
        with open(os.path.join(self.tmp_dir, doc.models[0].source), 'w'):
            pass
        with open(doc.models[1].source, 'w'):
            pass

        doc_2 = copy.deepcopy(doc)
        utils.resolve_model(doc_2.models[0], doc_2, working_dir=self.tmp_dir)
        self.assertEqual(doc_2.models[0].source, os.path.join(self.tmp_dir, doc.models[0].source))
        self.assertEqual(doc_2.models[0].changes, [1, 2])

        doc_2 = copy.deepcopy(doc)
        utils.resolve_model(doc_2.models[1], doc_2, working_dir=self.tmp_dir)
        self.assertEqual(doc_2.models[1].source, doc.models[1].source)
        self.assertEqual(doc_2.models[1].changes, [3, 4])

        doc_2 = copy.deepcopy(doc)
        utils.resolve_model(doc_2.models[2], doc_2, working_dir=self.tmp_dir)
        self.assertEqual(doc_2.models[2].source, os.path.join(self.tmp_dir, doc.models[0].source))
        self.assertEqual(doc_2.models[2].changes, [1, 2, 5])

        doc_2 = copy.deepcopy(doc)
        utils.resolve_model(doc_2.models[3], doc_2, working_dir=self.tmp_dir)
        self.assertEqual(doc_2.models[3].source, os.path.join(self.tmp_dir, doc.models[0].source))
        self.assertEqual(doc_2.models[3].changes, [1, 2, 5, 6, 7])

        def requests_get(url):
            assert url == 'https://server.edu/model.xml'
            return mock.Mock(raise_for_status=lambda: None, content='best model'.encode())
        doc_2 = copy.deepcopy(doc)
        with mock.patch('requests.get', side_effect=requests_get):
            utils.resolve_model(doc_2.models[4], doc_2, working_dir=self.tmp_dir)
        with open(doc_2.models[4].source, 'r') as file:
            self.assertEqual(file.read(), 'best model')
        self.assertEqual(doc_2.models[4].changes, [8])

        def requests_get(url):
            assert url == 'https://www.ebi.ac.uk/biomodels/model/download/123?filename=123_url.xml'
            return mock.Mock(raise_for_status=lambda: None, content='second best model'.encode())
        doc_2 = copy.deepcopy(doc)
        with mock.patch('requests.get', side_effect=requests_get):
            utils.resolve_model(doc_2.models[5], doc_2, working_dir=self.tmp_dir)
        with open(doc_2.models[5].source, 'r') as file:
            self.assertEqual(file.read(), 'second best model')
        self.assertEqual(doc_2.models[5].changes, [9])

        def requests_get(url):
            assert url == 'https://www.ebi.ac.uk/biomodels/model/download/123?filename=123_url.xml'
            return mock.Mock(raise_for_status=lambda: None, content='second best model'.encode())
        doc_2 = copy.deepcopy(doc)
        with mock.patch('requests.get', side_effect=requests_get):
            utils.resolve_model(doc_2.models[6], doc_2, working_dir=self.tmp_dir)
        with open(doc_2.models[6].source, 'r') as file:
            self.assertEqual(file.read(), 'second best model')
        self.assertEqual(doc_2.models[6].changes, [9, 10])

        # error handling:
        def bad_requests_get(url):
            def raise_for_status():
                raise Exception('error')
            return mock.Mock(raise_for_status=raise_for_status)
        doc_2 = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, 'could not be downloaded from BioModels'):
            with mock.patch('requests.get', side_effect=bad_requests_get):
                utils.resolve_model(doc_2.models[5], doc_2, working_dir=self.tmp_dir)

        doc_2 = copy.deepcopy(doc)
        doc_2.models[5].source = 'urn:miriam:unimplemented:123'
        with self.assertRaisesRegex(NotImplementedError, 'could be resolved'):
            utils.resolve_model(doc_2.models[5], doc_2, working_dir=self.tmp_dir)

        doc_2 = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, 'could not be downloaded'):
            with mock.patch('requests.get', side_effect=bad_requests_get):
                utils.resolve_model(doc_2.models[4], doc_2, working_dir=self.tmp_dir)

        doc_2 = copy.deepcopy(doc)
        doc_2.models[6].source = '#not-a-model'
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            utils.resolve_model(doc_2.models[6], doc_2, working_dir=self.tmp_dir)

        doc_2 = copy.deepcopy(doc)
        doc_2.models[0].source = 'not-a-file.xml'
        with self.assertRaisesRegex(FileNotFoundError, 'does not exist'):
            utils.resolve_model(doc_2.models[0], doc_2, working_dir=self.tmp_dir)

    def test_get_variables_for_task(self):
        doc = data_model.SedDocument()

        doc.models.append(data_model.Model(id='model1'))
        doc.models.append(data_model.Model(id='model2'))
        doc.tasks.append(data_model.Task(id='task1', model=doc.models[0]))
        doc.tasks.append(data_model.Task(id='task2', model=doc.models[1]))

        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(
                    id='var_1_1',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
                data_model.Variable(
                    id='var_1_2',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
            ]
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_2',
            variables=[
                data_model.Variable(
                    id='var_2_1',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
                data_model.Variable(
                    id='var_2_2',
                    task=doc.tasks[0],
                    model=doc.models[0],
                ),
            ]
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_3',
            variables=[
                data_model.Variable(
                    id='var_3_1',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
                data_model.Variable(
                    id='var_3_2',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
            ]
        ))
        doc.data_generators.append(data_model.DataGenerator(
            id='data_gen_4',
            variables=[
                data_model.Variable(
                    id='var_4_1',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
                data_model.Variable(
                    id='var_4_2',
                    task=doc.tasks[1],
                    model=doc.models[1],
                ),
            ]
        ))

        self.assertTrue(are_lists_equal(
            utils.get_variables_for_task(doc, doc.tasks[0]),
            []))
        doc.outputs.append(data_model.Report(
            data_sets=[
                data_model.DataSet(data_generator=doc.data_generators[0]),
            ]
        ))
        self.assertTrue(are_lists_equal(
            utils.get_variables_for_task(doc, doc.tasks[0]),
            [
                doc.data_generators[0].variables[0],
                doc.data_generators[0].variables[1],
            ]))
        doc.outputs.append(data_model.Report(
            data_sets=[
                data_model.DataSet(data_generator=doc.data_generators[0]),
                data_model.DataSet(data_generator=doc.data_generators[1]),
                data_model.DataSet(data_generator=doc.data_generators[2]),
                data_model.DataSet(data_generator=doc.data_generators[3]),
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
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialConcentration",
                target_namespaces=namespaces,
                new_value='1.9'),
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']/@sboTerm",
                target_namespaces=namespaces,
                new_value='SBO:0000001'),
            data_model.AddElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies",
                target_namespaces=namespaces,
                new_elements='<sbml:species xmlns:sbml="{}" id="NewSpecies" />'.format(namespaces['sbml'])),
            data_model.ReplaceElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SpeciesToReplace']",
                target_namespaces=namespaces,
                new_elements='<sbml:species xmlns:sbml="{}" id="DifferentSpecies" />'.format(namespaces['sbml'])),
            data_model.RemoveElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic']",
                target_namespaces=namespaces,
            ),
        ]
        save_changes = copy.copy(changes)
        et = etree.parse(self.FIXTURE_FILENAME)
        self.assertEqual(len(et.xpath(changes[2].target, namespaces=get_namespaces_with_prefixes(namespaces))[0].getchildren()), 4)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='NewSpecies']",
                                      namespaces=get_namespaces_with_prefixes(namespaces))), 0)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='DifferentSpecies']",
                                      namespaces=get_namespaces_with_prefixes(namespaces))), 0)
        self.assertEqual(len(et.xpath(changes[4].target, namespaces=get_namespaces_with_prefixes(namespaces))), 1)

        # apply changes
        utils.apply_changes_to_xml_model(data_model.Model(changes=changes), et, None, None)

        # check changes applied
        self.assertEqual(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                                  namespaces=get_namespaces_with_prefixes(namespaces))[0].get('initialConcentration'),
                         save_changes[0].new_value)
        self.assertEqual(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
                                  namespaces=get_namespaces_with_prefixes(namespaces))[0].get('sboTerm'),
                         save_changes[1].new_value)
        self.assertEqual(len(et.xpath(save_changes[2].target, namespaces=get_namespaces_with_prefixes(namespaces))[0].getchildren()), 4)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='NewSpecies']",
                                      namespaces=get_namespaces_with_prefixes(namespaces))), 1)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='DifferentSpecies']",
                                      namespaces=get_namespaces_with_prefixes(namespaces))), 1)
        self.assertEqual(len(et.xpath(save_changes[4].target, namespaces=get_namespaces_with_prefixes(namespaces))), 0)

        self.assertNotEqual(changes, [])

    def test_add_namespaces_to_xml_node(self):
        filename = os.path.join(os.path.dirname(__file__), '../fixtures/sedml/new-xml-with-top-level-namespace.sedml')
        doc = libsedml.readSedMLFromFile(filename)
        node = doc.getListOfModels()[0].getListOfChanges()[0].getNewXML()
        namespaces = node.getNamespaces()
        self.assertEqual(namespaces.getIndexByPrefix('sbml'), -1)
        self.assertEqual(utils.convert_xml_node_to_string(node), '<sbml:parameter id="V_mT" value="0.7"/>')

        utils.add_namespaces_to_xml_node(node, set(['sbml']), doc.getNamespaces())
        namespaces = node.getNamespaces()
        self.assertEqual(namespaces.getIndexByPrefix('sbml'), 0)
        self.assertEqual(utils.convert_xml_node_to_string(node),
                         '<sbml:parameter xmlns:{}="{}" id="V_mT" value="0.7"/>'.format(
            'sbml', 'http://www.sbml.org/sbml/level2/version3'))

    def test_add_namespaces_to_xml_node_2(self):
        changes = [
            data_model.AddElementModelChange(
                target='/sbml:sbml',
                target_namespaces={
                    'sbml': 'http://www.sbml.org/sbml/level2/version4',
                },
                new_elements='<biosimulators:insertedNode xmlns:biosimulators="https://biosimulators.org"></biosimulators:insertedNode>',
            ),
            data_model.ReplaceElementModelChange(
                target='/sbml:sbml/biosimulators:insertedNode',
                target_namespaces={
                    'sbml': 'http://www.sbml.org/sbml/level2/version4',
                    'biosimulators': "https://biosimulators.org",
                },
                new_elements=('<biosimulators2:insertedNode xmlns:biosimulators2="https://biosimulators2.org">'
                              '</biosimulators2:insertedNode>'),
            ),
            data_model.RemoveElementModelChange(
                target='/sbml:sbml/biosimulators2:insertedNode',
                target_namespaces={
                    'sbml': 'http://www.sbml.org/sbml/level2/version4',
                    'biosimulators2': "https://biosimulators2.org",
                },
            ),
        ]

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=changes[0:1]), et, None, None, validate_unique_xml_targets=True)
        namespaces = get_namespaces_for_xml_doc(et)
        self.assertEqual(len(et.xpath('/sbml:sbml/biosimulators:insertedNode', namespaces=get_namespaces_with_prefixes(namespaces))), 1)

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=changes[0:2]), et, None, None, validate_unique_xml_targets=True)
        namespaces = get_namespaces_for_xml_doc(et)
        self.assertNotIn('biosimulators', namespaces)
        namespaces['biosimulators'] = 'https://biosimulators.org'
        self.assertEqual(len(et.xpath('/sbml:sbml/biosimulators:insertedNode', namespaces=get_namespaces_with_prefixes(namespaces))), 0)
        self.assertEqual(len(et.xpath('/sbml:sbml/biosimulators2:insertedNode', namespaces=get_namespaces_with_prefixes(namespaces))), 1)

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=changes), et, None, None, validate_unique_xml_targets=True)
        namespaces = get_namespaces_for_xml_doc(et)
        self.assertNotIn('biosimulators', namespaces)
        self.assertNotIn('biosimulators2', namespaces)
        namespaces['biosimulators'] = 'https://biosimulators.org'
        namespaces['biosimulators2'] = 'https://biosimulators2.org'
        self.assertEqual(len(et.xpath('/sbml:sbml/biosimulators:insertedNode', namespaces=get_namespaces_with_prefixes(namespaces))), 0)
        self.assertEqual(len(et.xpath('/sbml:sbml/biosimulators2:insertedNode', namespaces=get_namespaces_with_prefixes(namespaces))), 0)

    def test_change_attributes_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        change = data_model.ModelAttributeChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']/@initialConcentration",
            target_namespaces={
                'sbml': 'http://www.sbml.org/sbml/level2/version4',
            },
            new_value='0.2')
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual(len(species), 3)

        # apply changes
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, validate_unique_xml_targets=True)

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, validate_unique_xml_targets=False)

        # check changes applied
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual(len(species), 0)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.2']",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual(len(species), 3)

    def test_add_multiple_elements_to_single_target(self):
        namespaces = {
            None: 'http://sed-ml.org/sed-ml/level1/version3',
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
        }

        change = data_model.AddElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies",
            target_namespaces=namespaces,
            new_elements=''.join([
                '<sbml:species xmlns:sbml="{}" id="NewSpecies1"/>'.format(namespaces['sbml']),
                '<sbml:species xmlns:sbml="{}" id="NewSpecies2"/>'.format(namespaces['sbml']),
            ]),
        )
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        num_species = len(species)
        species_ids = set([s.get('id') for s in species])

        # apply changes
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        # check changes applied
        xpath_evaluator = etree.XPathEvaluator(et, namespaces=get_namespaces_with_prefixes(namespaces))
        species = xpath_evaluator("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species")
        self.assertEqual(len(species), num_species + 2)
        self.assertEqual(set([s.get('id') for s in species]), species_ids | set(['NewSpecies1', 'NewSpecies2']))

        # check that changes can be written/read from file
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    language='language',
                    source='source',
                    changes=[change],
                ),
            ]
        )

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)
        doc2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(doc2.is_equal(doc))

    def test_add_multiple_elements_to_single_target_with_different_namespace_prefix(self):
        ####################
        # Correct namespace
        namespaces = {
            None: 'http://sed-ml.org/sed-ml/level1/version3',
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
            'newXml': 'http://www.sbml.org/sbml/level2/version4',
        }

        change = data_model.AddElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies",
            target_namespaces=namespaces,
            new_elements=''.join([
                '<newXml:species xmlns:newXml="{}" id="NewSpecies1"/>'.format(namespaces['newXml']),
                '<newXml:species xmlns:newXml="{}" id="NewSpecies2"/>'.format(namespaces['newXml']),
            ]),
        )
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        num_species = len(species)
        species_ids = set([s.get('id') for s in species])

        # apply changes
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        # check changes applied
        xpath_evaluator = etree.XPathEvaluator(et, namespaces=get_namespaces_with_prefixes(namespaces))
        species = xpath_evaluator("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species")
        self.assertEqual(len(species), num_species + 2)
        self.assertEqual(set([s.get('id') for s in species]), species_ids | set(['NewSpecies1', 'NewSpecies2']))

        # check that changes can be written/read from file
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    language='language',
                    source='source',
                    changes=[change],
                ),
            ]
        )

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)
        doc2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(doc2.is_equal(doc))

        ####################
        # Incorrect namespace
        namespaces = {
            None: 'http://sed-ml.org/sed-ml/level1/version3',
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
            'newXml': 'http://www.sbml.org/sbml/level3/version1',
        }

        change = data_model.AddElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies",
            target_namespaces=namespaces,
            new_elements=''.join([
                '<newXml:species xmlns:newXml="{}" id="NewSpecies1"/>'.format(namespaces['newXml']),
                '<newXml:species xmlns:newXml="{}" id="NewSpecies2"/>'.format(namespaces['newXml']),
            ]),
        )
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        num_species = len(species)
        species_ids = set([s.get('id') for s in species])

        # apply changes
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        # check changes applied
        xpath_evaluator = etree.XPathEvaluator(et, namespaces=get_namespaces_with_prefixes(namespaces))
        species = xpath_evaluator("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species")
        self.assertEqual(len(species), num_species)
        self.assertEqual(set([s.get('id') for s in species]), species_ids)

        # check that changes can be written/read from file
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    language='language',
                    source='source',
                    changes=[change],
                ),
            ]
        )

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)
        doc2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(doc2.is_equal(doc))

    def test_add_multiple_elements_to_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        change = data_model.AddElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
            target_namespaces=namespaces,
            new_elements=''.join([
                '<sbml:parameter xmlns:sbml="{}" id="p1" />'.format(namespaces['sbml']),
                '<sbml:parameter xmlns:sbml="{}" id="p2" />'.format(namespaces['sbml']),
            ]))
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        parameters = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/sbml:parameter",
                              namespaces=get_namespaces_with_prefixes(namespaces))
        species_ids = [s.get('id') for s in species]

        # apply changes
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, validate_unique_xml_targets=True)

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, validate_unique_xml_targets=False)

        # check changes applied
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual([s.get('id') for s in species], species_ids)

        parameters = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/sbml:parameter",
                              namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual([p.get('id') for p in parameters], ['p1', 'p2'] * len(species))

    def test_replace_multiple_elements_to_single_target(self):
        namespaces = {
            None: 'http://sed-ml.org/sed-ml/level1/version3',
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
        }

        change = data_model.ReplaceElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SpeciesToReplace']",
            target_namespaces=namespaces,
            new_elements=''.join([
                '<sbml:species xmlns:sbml="{}" id="NewSpecies1"/>'.format(namespaces['sbml']),
                '<sbml:species xmlns:sbml="{}" id="NewSpecies2"/>'.format(namespaces['sbml']),
            ]))
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        num_species = len(species)
        species_ids = set([s.get('id') for s in species])

        # apply changes
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        # check changes applied
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual(len(species), num_species + 1)
        self.assertEqual(set([s.get('id') for s in species]),
                         (species_ids | set(['NewSpecies1', 'NewSpecies2'])) - set(['SpeciesToReplace']))

        # check that changes can be written/read from file
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    language='language',
                    source='source',
                    changes=[change],
                ),
            ]
        )

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)
        doc2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(doc2.is_equal(doc))

    def test_replace_multiple_elements_to_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        change = data_model.ReplaceElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
            target_namespaces=namespaces,
            new_elements=''.join([
                '<sbml:species xmlns:sbml="{}" id="NewSpecies1" />'.format(namespaces['sbml']),
                '<sbml:species xmlns:sbml="{}" id="NewSpecies2" />'.format(namespaces['sbml']),
            ]))
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        num_species = len(species)

        # apply changes
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None,  validate_unique_xml_targets=True)

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None,  validate_unique_xml_targets=False)

        # check changes applied
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual([s.get('id') for s in species], ['NewSpecies1', 'NewSpecies2'] * num_species)

    def test_remove_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        change = data_model.RemoveElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']",
            target_namespaces=namespaces,
        )
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))

        # apply changes
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None,  validate_unique_xml_targets=True)

        et = etree.parse(self.FIXTURE_FILENAME)
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None,  validate_unique_xml_targets=False)

        # check changes applied
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                           namespaces=get_namespaces_with_prefixes(namespaces))
        self.assertEqual([s.get('id') for s in species], ['SpeciesToReplace'])

    def test_errors(self):
        change = mock.MagicMock(
            name='c1',
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialConcentration",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_value='1.9')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaises(NotImplementedError):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        change = data_model.ModelAttributeChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_value='1.9')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaises(ValueError):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        change = data_model.ModelAttributeChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/@initialConcentration",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_value='1.9')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaises(ValueError):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}
        change = data_model.ModelAttributeChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@sbml2:initialConcentration",
            target_namespaces=namespaces,
            new_value='1.9')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaises(ValueError):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        namespaces['sbml2'] = 'http://www.sbml.org/sbml/level2/version4'
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        change = data_model.AddElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_elements='<')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'invalid XML'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        change = data_model.AddElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_elements='1.9')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        change = data_model.ReplaceElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_elements='<')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'invalid XML'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

        change = data_model.ReplaceElementModelChange(
            target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
            target_namespaces={'sbml': 'http://www.sbml.org/sbml/level2/version4'},
            new_elements='1.9')
        et = etree.parse(self.FIXTURE_FILENAME)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None)

    def test_apply_compute_model_change_new_value(self):
        change = data_model.ComputeModelChange(
            target="/model/parameter[@id='p1']/@value",
            parameters=[
                data_model.Parameter(id='a', value=1.5),
                data_model.Parameter(id='b', value=2.25),
                data_model.Parameter(id='c', value=2.),
            ],
            variables=[
                data_model.Variable(id='x', model=data_model.Model(id='model_1'), target="/model/parameter[@id='x']/@value"),
                data_model.Variable(id='y', model=data_model.Model(id='model_2'), target="/model/parameter[@id='y']/@value"),
            ],
            math='a * x + b * y',
        )

        # get values of variables
        model_filename = os.path.join(self.tmp_dir, 'model_1.xml')
        with open(model_filename, 'w') as file:
            file.write('<model>')
            file.write('<parameter id="x" value="2.0" strValue="a value" qual:attrA="2.3" xmlns:qual="https://qual.sbml.org" />')
            file.write('<parameter id="y" value="3.0" />')
            file.write('</model>')
        models = {
            'model_1': etree.parse(model_filename),
            'model_2': etree.parse(model_filename),
        }

        change.variables[0].target = "/model/parameter[@id='x']"
        with self.assertRaisesRegex(ValueError, 'not a valid XPath'):
            utils.get_value_of_variable_model_xml_targets(change.variables[0], models)

        change.variables[0].target = "/model/parameter/@value"
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.get_value_of_variable_model_xml_targets(change.variables[0], models)

        change.variables[0].target = "/model/parameter[@id='x']/@value2"
        with self.assertRaisesRegex(ValueError, 'is not defined in model'):
            utils.get_value_of_variable_model_xml_targets(change.variables[0], models)

        change.variables[0].target = "/model/parameter[@id='x']/@strValue"
        with self.assertRaisesRegex(ValueError, 'must be a float'):
            utils.get_value_of_variable_model_xml_targets(change.variables[0], models)

        change.variables[0].target = "#dataDescription"
        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            utils.get_value_of_variable_model_xml_targets(change.variables[0], models)

        change.variables[0].target = None
        change.variables[0].symbol = True
        with self.assertRaisesRegex(NotImplementedError, 'must have a target'):
            utils.get_value_of_variable_model_xml_targets(change.variables[0], models)

        change.variables[0].target = "/model/parameter[@id='x']/@value"
        change.variables[0].symbol = None
        self.assertEqual(utils.get_value_of_variable_model_xml_targets(change.variables[0], models), 2.0)
        self.assertEqual(utils.get_value_of_variable_model_xml_targets(change.variables[1], models), 3.0)

        var = data_model.Variable(id='var', model=data_model.Model(id='model_1'),
                                  target="/model/parameter[@id='x']/@qual:attrA",
                                  target_namespaces={'qual': 'https://qual.sbml.org'})
        self.assertEqual(utils.get_value_of_variable_model_xml_targets(var, models), 2.3)

        doc = data_model.SedDocument(models=[change.variables[0].model, change.variables[1].model])

        change.variables[0].model.source = 'https://models.com/model_1.xml'
        change.variables[1].model.source = 'model_1.xml'
        change.variables[0].model.language = data_model.ModelLanguage.SBML.value
        change.variables[1].model.language = data_model.ModelLanguage.SBML.value
        working_dir = self.tmp_dir
        with open(model_filename, 'rb') as file:
            model_1_xml = file.read()
        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: None, content=model_1_xml)):
            variable_values = utils.get_values_of_variable_model_xml_targets_of_model_change(change, doc, {}, working_dir)
        self.assertEqual(variable_values, {
            'x': 2.,
            'y': 3.,
        })

        # calc new value
        variable_values = {}
        with self.assertRaisesRegex(ValueError, 'is not defined'):
            utils.calc_compute_model_change_new_value(change, variable_values=variable_values)

        variable_values = {
            'x': 2.,
            'y': 3.,
        }
        expected_value = 1.5 * 2. + 2.25 * 3.
        self.assertEqual(utils.calc_compute_model_change_new_value(change, variable_values=variable_values), expected_value)

        in_file = os.path.join(self.tmp_dir, 'in.xml')
        with open(in_file, 'w') as file:
            file.write('<model>')
            file.write('<parameter id="p1" value="1.0" type="parameter" />')
            file.write('<parameter id="p2" value="1.0" type="parameter" />')
            file.write('</model>')

        # apply xml changes
        et = etree.parse(in_file)
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, variable_values=variable_values)

        obj = et.xpath("/model/parameter[@id='p1']")[0]
        self.assertEqual(float(obj.get('value')), expected_value)

        change.math = 'c'
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, variable_values=variable_values)
        obj = et.xpath("/model/parameter[@id='p1']")[0]
        self.assertEqual(float(obj.get('value')), 2)
        change.math = 'a * x + b * y'

        change.target = "/model/parameter[@type='parameter']/@value"
        et = etree.parse(in_file)
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(data_model.Model(
                changes=[change]), et, None, None, variable_values=variable_values, validate_unique_xml_targets=True)

        et = etree.parse(in_file)
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None,
                                         None, variable_values=variable_values, validate_unique_xml_targets=False)
        for obj in et.xpath("/model/parameter"):
            self.assertEqual(float(obj.get('value')), expected_value)

        change.target = "/model/parameter[@type='parameter']"
        et = etree.parse(in_file)
        with self.assertRaisesRegex(ValueError, 'not a valid XPath to an attribute'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, variable_values=variable_values)

        with open(in_file, 'w') as file:
            file.write('<model>')
            file.write('<parameter id="p1" qual:value="1.0" type="parameter" xmlns:qual="https://qual.sbml.org"/>')
            file.write('<parameter id="p2" qual:value="1.0" type="parameter" xmlns:qual="https://qual.sbml.org"/>')
            file.write('</model>')
        change.target = "/model/parameter[@id='p1']/@qual:value"
        et = etree.parse(in_file)
        with self.assertRaisesRegex(ValueError, 'No namespace is defined with prefix'):
            utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, variable_values=variable_values)

        change.target_namespaces['qual'] = "https://qual.sbml.org"
        utils.apply_changes_to_xml_model(data_model.Model(changes=[change]), et, None, None, variable_values=variable_values)

    def test_set_value_calc_compute_model_change_new_value(self):
        change = data_model.SetValueComputeModelChange(
            target="/model/parameter[@id='p1']/@value",
            range=data_model.VectorRange(id='range1', values=[0.1, 0.2, 0.3]),
            parameters=[
                data_model.Parameter(id='a', value=1.5),
                data_model.Parameter(id='b', value=2.25),
            ],
            variables=[
                data_model.Variable(id='x', model=data_model.Model(id='model_1'), target="/model/parameter[@id='x']/@value"),
                data_model.Variable(id='y', model=data_model.Model(id='model_2'), target="/model/parameter[@id='y']/@value"),
            ],
            math='a * x + b * y + range1',
        )
        self.assertEqual(
            utils.calc_compute_model_change_new_value(
                change,
                variable_values={
                    'x': 2.,
                    'y': 3.,
                },
                range_values={
                    'range1': 0.1,
                },
            ),
            1.5 * 2. + 2.25 * 3. + 0.1,
        )

        with self.assertRaisesRegex(ValueError, 'is not defined'):
            utils.calc_compute_model_change_new_value(
                change,
                variable_values={
                    'x': 2.,
                    'y': 3.,
                },
                range_values={
                },
            )

    def test_calc_data_generator_results(self):
        data_gen = data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(id='var_1'),
                data_model.Variable(id='var_2'),
            ],
            parameters=[
                data_model.Parameter(id='param_1', value=2.),
            ],
            math='var_1 * var_2 + param_1',
        )
        var_results = {
            data_gen.variables[0].id: numpy.array([1, 2, 3]),
            data_gen.variables[1].id: numpy.array([2, 3, 4]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      var_results[data_gen.variables[0].id] * var_results[data_gen.variables[1].id] + 2.)

        data_gen_no_vars = data_model.DataGenerator(
            id='data_gen_1',
            parameters=[
                data_model.Parameter(id='param_1', value=2.),
            ],
            math='param_1',
        )
        var_results_no_vars = {}
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen_no_vars, var_results_no_vars),
                                      numpy.array(2.))

        # errors
        data_gen.math = 'var_1 * var_3 + param_1'
        var_results = {
            data_gen.variables[0].id: numpy.array([1, 2, 3]),
            data_gen.variables[1].id: numpy.array([2, 3, 4]),
        }
        with self.assertRaises(ValueError):
            utils.calc_data_generator_results(data_gen, var_results)

        data_gen_no_vars.math = 'param_2'
        with self.assertRaises(ValueError):
            utils.calc_data_generator_results(data_gen_no_vars, var_results_no_vars)

        var_results = {
            data_gen.variables[0].id: numpy.array([1, 2]),
            data_gen.variables[1].id: numpy.array([2, 3, 4]),
        }
        with self.assertRaises(ValueError):
            utils.calc_data_generator_results(data_gen, var_results)

        data_gen.math = 'min(var_1)'
        var_results = {
            data_gen.variables[0].id: numpy.array([1, 2]),
            data_gen.variables[1].id: numpy.array([2, 3, 4]),
        }
        with self.assertRaises(NotImplementedError):
            utils.calc_data_generator_results(data_gen, var_results)

    def test_calc_data_generator_results_diff_shapes(self):
        data_gen = data_model.DataGenerator(
            id='data_gen_1',
            variables=[
                data_model.Variable(id='var_1'),
                data_model.Variable(id='var_2'),
            ],
            math='var_1 + var_2',
        )

        var_results = {
            'var_1': numpy.array(2.),
            'var_2': numpy.array(3.),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array(5.))

        var_results = {
            'var_1': numpy.array([2.]),
            'var_2': numpy.array([3.]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([5.]))

        var_results = {
            'var_1': numpy.array([[2.]]),
            'var_2': numpy.array([[3.]]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([[5.]]))

        var_results = {
            'var_1': numpy.array(2.),
            'var_2': numpy.array([3, 5.]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([5., numpy.nan]))

        var_results = {
            'var_1': numpy.array([2.]),
            'var_2': numpy.array([3, 5.]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([5., numpy.nan]))

        var_results = {
            'var_1': numpy.array([[2.]]),
            'var_2': numpy.array([3, 5.]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([[5.], [numpy.nan]]))

        var_results = {
            'var_1': numpy.array(2.),
            'var_2': numpy.array([[3, 5., 1.], [4., 7., 1.]]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([[5., numpy.nan, numpy.nan], [numpy.nan, numpy.nan, numpy.nan]]))

        var_results = {
            'var_2': numpy.array(2.),
            'var_1': numpy.array([[3, 5., 1.], [4., 7., 1.]]),
        }
        numpy.testing.assert_allclose(utils.calc_data_generator_results(data_gen, var_results),
                                      numpy.array([[5., numpy.nan, numpy.nan], [numpy.nan, numpy.nan, numpy.nan]]))

    def test_remove_model_changes(self):
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    changes=[
                        data_model.ModelAttributeChange(),
                        data_model.ModelAttributeChange(),
                        data_model.ModelAttributeChange(),
                    ],
                ),
                data_model.Model(
                    changes=[
                        data_model.ModelAttributeChange(),
                        data_model.ModelAttributeChange(),
                        data_model.ModelAttributeChange(),
                    ],
                )
            ],
        )
        utils.remove_model_changes(doc)
        for model in doc.models:
            self.assertEqual(model.changes, [])

    def test_remove_algorithm_parameter_changes(self):
        doc = data_model.SedDocument(
            simulations=[
                data_model.UniformTimeCourseSimulation(
                    algorithm=data_model.Algorithm(
                        changes=[
                            data_model.AlgorithmParameterChange(),
                            data_model.AlgorithmParameterChange(),
                        ],
                    )
                ),
                data_model.UniformTimeCourseSimulation(
                    algorithm=data_model.Algorithm(
                        changes=[
                            data_model.AlgorithmParameterChange(),
                            data_model.AlgorithmParameterChange(),
                        ],
                    )
                ),
            ],
        )
        utils.remove_algorithm_parameter_changes(doc)
        for sim in doc.simulations:
            self.assertEqual(sim.algorithm.changes, [])

    def test_replace_complex_data_generators_with_generators_for_individual_variables(self):
        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    parameters=[
                        data_model.Parameter(),
                    ],
                    variables=[
                        data_model.Variable(id="var_1"),
                    ]
                ),
                data_model.DataGenerator(
                    parameters=[
                        data_model.Parameter(),
                    ],
                    variables=[
                        data_model.Variable(id="var_2"),
                        data_model.Variable(id="var_3"),
                    ]
                )
            ],
        )
        doc.outputs.append(data_model.Report(
            data_sets=[
                data_model.DataSet(data_generator=doc.data_generators[0]),
                data_model.DataSet(data_generator=doc.data_generators[1]),
            ]
        ))
        doc.outputs.append(data_model.Plot2D(
            curves=[
                data_model.Curve(x_data_generator=doc.data_generators[0], y_data_generator=doc.data_generators[0]),
                data_model.Curve(x_data_generator=doc.data_generators[1], y_data_generator=doc.data_generators[1]),
            ]
        ))
        doc.outputs.append(data_model.Plot3D(
            surfaces=[
                data_model.Surface(
                    x_data_generator=doc.data_generators[0],
                    y_data_generator=doc.data_generators[0],
                    z_data_generator=doc.data_generators[0],
                ),
                data_model.Surface(
                    x_data_generator=doc.data_generators[1],
                    y_data_generator=doc.data_generators[1],
                    z_data_generator=doc.data_generators[1],
                ),
            ]
        ))

        utils.replace_complex_data_generators_with_generators_for_individual_variables(doc)

        for data_gen in doc.data_generators:
            self.assertEqual(len(data_gen.variables), 1)
            self.assertEqual(data_gen.parameters, [])
            self.assertEqual(data_gen.math, data_gen.variables[0].id)
        self.assertEqual(len(set(data_gen.variables[0].id for data_gen in doc.data_generators)), 3)
        self.assertEqual(len(set(data_gen.id for data_gen in doc.data_generators)), 3)

        report = doc.outputs[0]
        self.assertEqual(len(report.data_sets), 3)
        self.assertEqual(len(set(d.id for d in report.data_sets)), 3)
        self.assertEqual(len(set(d.data_generator.id for d in report.data_sets)), 3)

        report = doc.outputs[0]
        self.assertEqual(len(report.data_sets), 3)
        self.assertEqual(len(set(d.id for d in report.data_sets)), 3)
        self.assertEqual(len(set(d.data_generator.id for d in report.data_sets)), 3)

        plot = doc.outputs[1]
        self.assertEqual(len(plot.curves), 5)
        self.assertEqual(len(set(c.id for c in plot.curves)), 5)
        self.assertEqual(len(set((c.x_data_generator.id, c.y_data_generator) for c in plot.curves)), 5)

        plot = doc.outputs[2]
        self.assertEqual(len(plot.surfaces), 9)
        self.assertEqual(len(set(s.id for s in plot.surfaces)), 9)
        self.assertEqual(len(set((s.x_data_generator.id, s.y_data_generator, s.z_data_generator) for s in plot.surfaces)), 9)

    def test_remove_plots(self):
        report = data_model.Report()
        doc = data_model.SedDocument(
            outputs=[
                report,
                data_model.Plot2D(),
                data_model.Plot3D(),
            ],
        )

        utils.remove_plots(doc)
        self.assertEqual(len(doc.outputs), 1)
        self.assertEqual(doc.outputs[0], report)

    def test_get_range_len(self):
        range1 = data_model.UniformRange(start=0., end=10., number_of_steps=10)
        self.assertEqual(utils.get_range_len(range1), 11)

        range2 = data_model.VectorRange(values=[1., 2., 3.])
        self.assertEqual(utils.get_range_len(range2), 3)

        range3 = data_model.FunctionalRange(range=range2)
        range4 = data_model.FunctionalRange(range=range3)
        self.assertEqual(utils.get_range_len(range4), 3)

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            utils.get_range_len(None)

    def test_resolve_range(self):
        range1 = data_model.UniformRange(id='range1', start=0., end=10., number_of_steps=5, type=data_model.UniformRangeType.linear)
        self.assertEqual(utils.resolve_range(range1), [0., 2., 4., 6., 8., 10.])

        range1 = data_model.UniformRange(id='range1', start=1., end=1000., number_of_steps=3, type=data_model.UniformRangeType.log)
        self.assertEqual(utils.resolve_range(range1), [1., 10., 100., 1000.])

        range1.type = mock.Mock(value='mock')
        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            utils.resolve_range(range1)

        range1 = data_model.VectorRange(id='range1', values=[2., 3., 5., 7., 11., 13.])
        self.assertEqual(utils.resolve_range(range1), [2., 3., 5., 7., 11., 13.])

        range2 = data_model.FunctionalRange(
            id='range2',
            range=range1,
            parameters=[
                data_model.Parameter(id='a', value=2.),
            ],
            math='a * range1')
        self.assertEqual(utils.resolve_range(range2), [4., 6., 10., 14., 22., 26.])

        range3 = data_model.FunctionalRange(
            id='range3',
            range=range2,
            parameters=[
                data_model.Parameter(id='b', value=3.),
            ],
            math='b * range2')
        self.assertEqual(utils.resolve_range(range3), [12., 18., 30., 42., 66., 78.])

        model_filename = os.path.join(self.tmp_dir, 'model.xml')
        with open(model_filename, 'w') as file:
            file.write('<model>')
            file.write('<parameter id="x" value="0.1" />')
            file.write('<parameter id="y" value="0.2" />')
            file.write('</model>')
        range2 = data_model.FunctionalRange(
            id='range2',
            range=range1,
            parameters=[
                data_model.Parameter(id='a', value=2.),
            ],
            variables=[
                data_model.Variable(
                    id='x',
                    model=data_model.Model(id='model', source=model_filename),
                    target="/model/parameter[@id='x']/@value",
                ),
            ],
            math='a * range1 + x')
        model_etrees = {'model': etree.parse(model_filename)}
        self.assertEqual(utils.resolve_range(range2, model_etrees), [4.1, 6.1, 10.1, 14.1, 22.1, 26.1])

        with self.assertRaisesRegex(NotImplementedError, 'non-XML-encoded models are not supported'):
            utils.resolve_range(range2, {'model': None})

        range2.variables[0].model.source = model_filename
        range2.variables[0].target = None
        range2.variables[0].symbol = 'time'
        with self.assertRaisesRegex(NotImplementedError, 'Symbols are not supported'):
            utils.resolve_range(range2, model_etrees)

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            utils.resolve_range(None, model_etrees)

    def test_get_models_referenced_by_range(self):
        self.assertEqual(utils.get_models_referenced_by_range(data_model.UniformRange()), set())
        self.assertEqual(utils.get_models_referenced_by_range(data_model.VectorRange()), set())

        model = data_model.Model(id='model1')
        range = data_model.FunctionalRange()
        range.range = data_model.FunctionalRange()
        range.range.variables.append(data_model.Variable(model=model))
        self.assertEqual(utils.get_models_referenced_by_range(range), set([model]))

    def test_get_models_referenced_by_model_change(self):
        self.assertEqual(utils.get_models_referenced_by_model_change(data_model.ModelAttributeChange()), set())
        self.assertEqual(utils.get_models_referenced_by_model_change(data_model.AddElementModelChange()), set())
        self.assertEqual(utils.get_models_referenced_by_model_change(data_model.RemoveElementModelChange()), set())
        self.assertEqual(utils.get_models_referenced_by_model_change(data_model.ReplaceElementModelChange()), set())

        models = [data_model.Model(id='model1'), data_model.Model(id='model2'), data_model.Model(id='model3')]

        change = data_model.ComputeModelChange(
            variables=[
                data_model.Variable(model=models[0]),
                data_model.Variable(model=models[1]),
            ],
        )
        self.assertEqual(utils.get_models_referenced_by_model_change(change), set(models[0:2]))

        change = data_model.SetValueComputeModelChange(
            model=models[0],
            variables=[
                data_model.Variable(model=models[1]),
            ],
            range=data_model.FunctionalRange(
                range=data_model.FunctionalRange(
                    variables=[
                        data_model.Variable(model=models[2]),
                    ],
                )
            )
        )
        self.assertEqual(utils.get_models_referenced_by_model_change(change), set(models))

    def test_get_models_referenced_by_task(self):
        models = [data_model.Model(id='model1'), data_model.Model(id='model2'),
                  data_model.Model(id='model3'), data_model.Model(id='model4'),
                  data_model.Model(id='model5'), data_model.Model(id='model6')]

        task = data_model.Task(model=models[0])
        self.assertEqual(utils.get_models_referenced_by_task(task), set(models[0:1]))

        task = data_model.RepeatedTask(
            sub_tasks=[
                data_model.SubTask(
                    task=data_model.RepeatedTask(
                        sub_tasks=[
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[0]
                                )
                            ),
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[1]
                                )
                            )
                        ]
                    )
                )
            ],
        )
        self.assertEqual(utils.get_models_referenced_by_task(task), set(models[0:2]))

        task = data_model.RepeatedTask(
            sub_tasks=[
                data_model.SubTask(
                    task=data_model.RepeatedTask(
                        range=data_model.FunctionalRange(variables=[data_model.Variable(model=models[2])]),
                        ranges=[
                            data_model.FunctionalRange(
                                range=data_model.FunctionalRange(
                                    variables=[data_model.Variable(model=models[3])]),
                            ),
                        ],
                        sub_tasks=[
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[0]
                                )
                            ),
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[1]
                                )
                            )
                        ]
                    )
                )
            ],
        )
        self.assertEqual(utils.get_models_referenced_by_task(task), set(models[0:4]))

        task = data_model.RepeatedTask(
            sub_tasks=[
                data_model.SubTask(
                    task=data_model.RepeatedTask(
                        range=data_model.FunctionalRange(variables=[data_model.Variable(model=models[2])]),
                        ranges=[
                            data_model.FunctionalRange(
                                range=data_model.FunctionalRange(
                                    variables=[data_model.Variable(model=models[3])]),
                            ),
                        ],
                        sub_tasks=[
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[0]
                                )
                            ),
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[1]
                                )
                            )
                        ],
                        changes=[
                            data_model.SetValueComputeModelChange(
                                model=models[4],
                                range=data_model.FunctionalRange(
                                    range=data_model.FunctionalRange(
                                        variables=[data_model.Variable(model=models[5])]),
                                ),
                            )
                        ]
                    )
                )
            ],
        )
        self.assertEqual(utils.get_models_referenced_by_task(task), set(models[0:6]))

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            utils.get_models_referenced_by_task(None)

    def test_get_first_last_models_executed_by_task(self):
        models = [data_model.Model(id='model1'), data_model.Model(id='model2'),
                  data_model.Model(id='model3'), data_model.Model(id='model4'),
                  data_model.Model(id='model5'), data_model.Model(id='model6')]

        task = data_model.Task(model=models[0])
        self.assertEqual(utils.get_first_last_models_executed_by_task(task), (models[0], models[0]))

        task = data_model.RepeatedTask(
            sub_tasks=[
                data_model.SubTask(
                    task=data_model.RepeatedTask(
                        sub_tasks=[
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[0]
                                ),
                                order=1,
                            ),
                            data_model.SubTask(
                                task=data_model.Task(
                                    model=models[1]
                                ),
                                order=2,
                            ),
                        ]
                    ),
                    order=1,
                ),
                data_model.SubTask(
                    task=data_model.Task(
                        model=models[2]
                    ),
                    order=2,
                ),
            ],
        )
        self.assertEqual(utils.get_first_last_models_executed_by_task(task), (models[0], models[2]))

        with self.assertRaisesRegex(NotImplementedError, 'are not supported'):
            utils.get_first_last_models_executed_by_task(None)

    def test_get_xml_node_namespace_tag_target(self):
        model_etree = etree.parse(self.FIXTURE_FILENAME).getroot()
        namespaces = {}
        uri, prefix, tag, target, target_namespaces = utils.get_xml_node_namespace_tag_target(model_etree, namespaces)
        self.assertEqual(uri, 'http://www.sbml.org/sbml/level2/version4')
        self.assertEqual(prefix, 'sbml')
        self.assertEqual(tag, 'sbml')
        self.assertEqual(target, 'sbml:sbml')
        self.assertFalse(target_namespaces is namespaces)
        self.assertEqual(target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        uri, prefix, tag, target, target_namespaces = utils.get_xml_node_namespace_tag_target(
            model_etree.getchildren()[0], target_namespaces)
        self.assertEqual(uri, 'http://www.sbml.org/sbml/level2/version4')
        self.assertEqual(prefix, 'sbml')
        self.assertEqual(tag, 'model')
        self.assertEqual(target, 'sbml:model')
        self.assertFalse(target_namespaces is namespaces)
        self.assertEqual(target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        filename = os.path.join(self.tmp_dir, 'model.xml')
        with open(filename, 'w') as file:
            file.write('<sbml>')
            file.write('  <model xmlns="http://www.sbml.org/sbml/level2/version4" />')
            file.write('</sbml>')
        model_etree = etree.parse(filename).getroot()
        uri, prefix, tag, target, target_namespaces = utils.get_xml_node_namespace_tag_target(model_etree, {})
        self.assertEqual(uri, None)
        self.assertEqual(prefix, None)
        self.assertEqual(tag, 'sbml')
        self.assertEqual(target, 'sbml')
        self.assertEqual(target_namespaces, {})

        filename = os.path.join(self.tmp_dir, 'model.xml')
        with open(filename, 'w') as file:
            file.write('<sbml:sbml xmlns:sbml="http://www.sbml.org/sbml/level2/version4">')
            file.write('  <sbml:model xmlns:sbml="http://www.sbml.org/sbml/level3/version1" />')
            file.write('</sbml:sbml>')
        model_etree = etree.parse(filename).getroot()

        uri, prefix, tag, target, target_namespaces = utils.get_xml_node_namespace_tag_target(model_etree, {})
        self.assertEqual(uri, 'http://www.sbml.org/sbml/level2/version4')
        self.assertEqual(prefix, 'sbml')
        self.assertEqual(tag, 'sbml')
        self.assertEqual(target, 'sbml:sbml')
        self.assertEqual(target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        uri, prefix, tag, target, target_namespaces = utils.get_xml_node_namespace_tag_target(
            model_etree.getchildren()[0], target_namespaces)
        self.assertEqual(uri, 'http://www.sbml.org/sbml/level3/version1')
        self.assertEqual(prefix, 'sbml2')
        self.assertEqual(tag, 'model')
        self.assertEqual(target, 'sbml2:model')
        self.assertEqual(target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
            'sbml2': 'http://www.sbml.org/sbml/level3/version1',
        })

    def test_is_model_language_encoded_in_xml(self):
        self.assertTrue(utils.is_model_language_encoded_in_xml(data_model.ModelLanguage.SBML.value))
        self.assertFalse(utils.is_model_language_encoded_in_xml(data_model.ModelLanguage.BNGL.value))

    def test_resolve_model_and_apply_xml_changes_error_handling(self):
        model = data_model.Model(
            source='model.xml',
            language=data_model.ModelLanguage.SBML.value,
        )
        sed_doc = data_model.SedDocument()

        model_filename = os.path.join(self.tmp_dir, model.source)
        with open(model_filename, 'w') as file:
            file.write('<sbml>')
            file.write('</sbml>')

        temp_model, temp_model_source, temp_model_etree = utils.resolve_model_and_apply_xml_changes(
            model, sed_doc, self.tmp_dir, save_to_file=False)

        self.assertEqual(temp_model.source, model_filename)
        self.assertEqual(temp_model_source, None)
        self.assertIsInstance(temp_model_etree, (etree._ElementTree))

        # invalid XML file
        with open(model_filename, 'w') as file:
            file.write('sbml>')
            file.write('</sbml>')
        with self.assertRaisesRegex(ValueError, 'could not be parsed'):
            utils.resolve_model_and_apply_xml_changes(
                model, sed_doc, self.tmp_dir, save_to_file=False)

        # not an XML file
        model.language = data_model.ModelLanguage.BNGL.value
        with open(model_filename, 'w') as file:
            file.write('sbml')
        temp_model, temp_model_source, temp_model_etree = utils.resolve_model_and_apply_xml_changes(
            model, sed_doc, self.tmp_dir, save_to_file=False)

        self.assertEqual(temp_model.source, model_filename)
        self.assertEqual(temp_model_source, None)
        self.assertEqual(temp_model_etree, None)

    def test_get_all_sed_objects(self):
        doc = data_model.SedDocument(
            tasks=[
                data_model.Task(
                    id='task',
                    model=data_model.Model(
                        id='model',
                        changes=[
                            data_model.ModelAttributeChange(id='modelChange'),
                        ]
                    ),
                    simulation=data_model.UniformTimeCourseSimulation(
                        id='simulation',
                        algorithm=data_model.Algorithm(
                            changes=[
                                data_model.AlgorithmParameterChange(),
                            ]
                        )
                    )
                )
            ]
        )
        expected_objs = [
            doc,
            doc.tasks[0],
            doc.tasks[0].model,
            doc.tasks[0].model.changes[0],
            doc.tasks[0].simulation,
            doc.tasks[0].simulation.algorithm,
            doc.tasks[0].simulation.algorithm.changes[0],
        ]

        objs = set(utils.get_all_sed_objects(doc))
        self.assertEqual(objs, set(expected_objs))

    def test_get_model_changes_for_task(self):
        task = data_model.Task()
        self.assertEqual(utils.get_model_changes_for_task(task), [])

        task = data_model.RepeatedTask(
            changes=[
                data_model.SetValueComputeModelChange(id='ch1'),
                data_model.SetValueComputeModelChange(id='ch2'),
            ],
            sub_tasks=[
                data_model.SubTask(
                    task=data_model.Task(),
                ),
                data_model.SubTask(
                    task=data_model.RepeatedTask(
                        changes=[
                            data_model.SetValueComputeModelChange(id='ch3'),
                        ]
                    )
                )
            ],
        )
        self.assertEqual(set([change.id for change in utils.get_model_changes_for_task(task)]), set(['ch1', 'ch2', 'ch3']))

        with self.assertRaisesRegex(NotImplementedError, 'not supported'):
            utils.get_model_changes_for_task(None)

    def test_get_task_results_shape(self):
        task = data_model.Task(
            simulation=data_model.OneStepSimulation(),
        )
        self.assertEqual(utils.get_task_results_shape(task), (2,))

        task = data_model.Task(
            simulation=data_model.SteadyStateSimulation(),
        )
        self.assertEqual(utils.get_task_results_shape(task), (1,))

        task = data_model.Task(simulation=data_model.UniformTimeCourseSimulation(number_of_steps=10))
        self.assertEqual(utils.get_task_results_shape(task), (11,))

        task = data_model.RepeatedTask(
            range=data_model.VectorRange(values=[0.1, 0.2, 0.3]),
            sub_tasks=[
                data_model.SubTask(task=data_model.Task(simulation=data_model.SteadyStateSimulation())),
                data_model.SubTask(task=data_model.Task(simulation=data_model.UniformTimeCourseSimulation(number_of_steps=10))),
            ],
        )
        self.assertEqual(utils.get_task_results_shape(task), (3, 2, 11))

        task = data_model.RepeatedTask(
            range=data_model.UniformRange(number_of_steps=4),
            sub_tasks=[
                data_model.SubTask(
                    task=data_model.RepeatedTask(
                        range=data_model.VectorRange(values=[0.1, 0.2, 0.3]),
                        sub_tasks=[
                            data_model.SubTask(task=data_model.Task(simulation=data_model.SteadyStateSimulation())),
                            data_model.SubTask(task=data_model.Task(simulation=data_model.UniformTimeCourseSimulation(number_of_steps=10))),
                        ],
                    ),
                )
            ],
        )
        self.assertEqual(utils.get_task_results_shape(task), (5, 1, 3, 2, 11))
