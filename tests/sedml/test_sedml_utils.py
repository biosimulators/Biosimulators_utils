from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import io
from biosimulators_utils.sedml import utils
from biosimulators_utils.utils.core import are_lists_equal
from lxml import etree
from unittest import mock
import copy
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
                new_value='1.9'),
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']/@sboTerm",
                new_value='SBO:0000001'),
            data_model.AddElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies",
                new_elements='<species id="NewSpecies" />'),
            data_model.ReplaceElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SpeciesToReplace']",
                new_elements='<species id="DifferentSpecies" />'),
            data_model.RemoveElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic']"),
        ]
        save_changes = copy.copy(changes)
        et = etree.parse(self.FIXTURE_FILENAME)
        self.assertEqual(len(et.xpath(changes[2].target, namespaces=namespaces)[0].getchildren()), 4)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='NewSpecies']",
                                      namespaces=namespaces)), 0)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='DifferentSpecies']",
                                      namespaces=namespaces)), 0)
        self.assertEqual(len(et.xpath(changes[4].target, namespaces=namespaces)), 1)

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename)

        # check changes applied
        et = etree.parse(out_filename)
        self.assertEqual(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                                  namespaces=namespaces)[0].get('initialConcentration'),
                         save_changes[0].new_value)
        self.assertEqual(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
                                  namespaces=namespaces)[0].get('sboTerm'),
                         save_changes[1].new_value)
        self.assertEqual(len(et.xpath(save_changes[2].target, namespaces=namespaces)[0].getchildren()), 4)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='NewSpecies']",
                                      namespaces=namespaces)), 1)
        self.assertEqual(len(et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='DifferentSpecies']",
                                      namespaces=namespaces)), 1)
        self.assertEqual(len(et.xpath(save_changes[4].target, namespaces=namespaces)), 0)

        self.assertEqual(changes, [])

    def test_change_attributes__multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.ModelAttributeChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']/@initialConcentration",
                new_value='0.2'),
        ]
        save_changes = copy.copy(changes)
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']", namespaces=namespaces)
        self.assertEqual(len(species), 3)

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=True)
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=False)

        # check changes applied
        et = etree.parse(out_filename)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']", namespaces=namespaces)
        self.assertEqual(len(species), 0)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.2']", namespaces=namespaces)
        self.assertEqual(len(species), 3)

    def test_add_multiple_elements_to_single_target(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.AddElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies",
                new_elements=(
                    '<species id="NewSpecies1" />'
                    '<species id="NewSpecies2" />'
                )),
        ]
        save_changes = copy.copy(changes)
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        num_species = len(species)
        species_ids = set([s.get('id') for s in species])

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename)

        # check changes applied
        et = etree.parse(out_filename)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        self.assertEqual(len(species), num_species + 2)
        self.assertEqual(set([s.get('id') for s in species]), species_ids | set(['NewSpecies1', 'NewSpecies2']))

        # check that changes can be written/read from file
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    language='language',
                    source='source',
                    changes=changes,
                ),
            ]
        )

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)
        doc2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(doc2.is_equal(doc))

    def test_add_multiple_elements_to_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.AddElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                new_elements=(
                    '<parameter id="p1" />'
                    '<parameter id="p2" />'
                )),
        ]
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        parameters = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/sbml:parameter", namespaces=namespaces)
        species_ids = [s.get('id') for s in species]
        parameter_ids = [p.get('id') for p in parameters]

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=True)
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=False)

        # check changes applied
        et = etree.parse(out_filename)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        self.assertEqual([s.get('id') for s in species], species_ids)

        parameters = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species/sbml:parameter", namespaces=namespaces)
        self.assertEqual([p.get('id') for p in parameters], ['p1', 'p2'] * len(species))

    def test_replace_multiple_elements_to_single_target(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.ReplaceElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SpeciesToReplace']",
                new_elements=(
                    '<species id="NewSpecies1" />'
                    '<species id="NewSpecies2" />'
                )),
        ]
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        num_species = len(species)
        species_ids = set([s.get('id') for s in species])

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename)

        # check changes applied
        et = etree.parse(out_filename)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
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
                    changes=changes,
                ),
            ]
        )

        filename = os.path.join(self.tmp_dir, 'test.sedml')
        io.SedmlSimulationWriter().run(doc, filename)
        doc2 = io.SedmlSimulationReader().run(filename)
        self.assertTrue(doc2.is_equal(doc))

    def test_replace_multiple_elements_to_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.ReplaceElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                new_elements=(
                    '<species id="NewSpecies1" />'
                    '<species id="NewSpecies2" />'
                )),
        ]
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        num_species = len(species)

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=True)
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=False)

        # check changes applied
        et = etree.parse(out_filename)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        self.assertEqual([s.get('id') for s in species], ['NewSpecies1', 'NewSpecies2'] * num_species)

    def test_remove_multiple_targets(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        changes = [
            data_model.RemoveElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@initialConcentration='0.1']"),
        ]
        et = etree.parse(self.FIXTURE_FILENAME)

        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)

        # apply changes
        out_filename = os.path.join(self.tmp_dir, 'test.xml')
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=True)
        utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, out_filename, validate_unique_xml_targets=False)

        # check changes applied
        et = etree.parse(out_filename)
        species = et.xpath("/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species", namespaces=namespaces)
        self.assertEqual([s.get('id') for s in species], ['SpeciesToReplace'])

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

        changes = [
            data_model.AddElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                new_elements='<'),
        ]
        with self.assertRaisesRegex(ValueError, 'not valid XML'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.AddElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                new_elements='1.9'),
        ]
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.ReplaceElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']",
                new_elements='<'),
        ]
        with self.assertRaisesRegex(ValueError, 'not valid XML'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

        changes = [
            data_model.ReplaceElementModelChange(
                target="/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
                new_elements='1.9'),
        ]
        with self.assertRaisesRegex(ValueError, 'must match a single object'):
            utils.apply_changes_to_xml_model(changes, self.FIXTURE_FILENAME, None)

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
