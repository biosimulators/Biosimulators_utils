from biosimulators_utils.xml import utils
import os
import unittest


class XmlUtilsTestCase(unittest.TestCase):
    XML_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')
    MULTIPLE_NAMESPACES_XML_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-fbc-textbook.xml')

    def test_get_attributes_of_xpaths(self):
        ids = utils.get_attributes_of_xpaths(self.XML_FILENAME, [
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BUD']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clb2']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SBF_a']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic1']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cdc20_a']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cdh1_a']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clb2']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='IE_a']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1_total']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_0']",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']",
            "/invalid:target",
            "--invalid--",
        ], 'id')

        expected_ids = {
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']": ['BE'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']": ['PSwe1M'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']": ['Swe1M'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']": ['Swe1'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BUD']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clb2']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']": ['Clg'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SBF_a']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic1']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cdc20_a']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cdh1_a']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='IE_a']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1_total']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_0']": [],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']": ['Clb'],
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']": ['BUD'],
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']": [],
            "/invalid:target": [],
            "--invalid--": [],
        }
        for target, target_ids in ids.items():
            self.assertEqual(target_ids, expected_ids[target], target)

        ids = utils.get_attributes_of_xpaths(self.XML_FILENAME, [
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
        ], 'id')
        self.assertEqual(len(ids["/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species"]), 19)

    def test_get_attributes_of_xpaths_in_namespaces(self):
        ids = utils.get_attributes_of_xpaths(self.MULTIPLE_NAMESPACES_XML_FILENAME, [
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']",
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']",
        ], 'id')
        expected_ids = {
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']": [None],
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']": [],
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']": ['R_ACALD'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']": ['M_13dpg_c'],
        }
        self.assertEqual(ids, expected_ids)

        ids = utils.get_attributes_of_xpaths(self.MULTIPLE_NAMESPACES_XML_FILENAME, [
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']",
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']",
        ], {'namespace': 'fbc', 'name': 'id'})
        expected_ids = {
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']": ['obj'],
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']": [],
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']": [None],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']": [None],
        }
        self.assertEqual(ids, expected_ids)

    def test_validate_xpaths_ref_to_unique_objects(self):
        utils.validate_xpaths_ref_to_unique_objects(self.XML_FILENAME, [
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']",
        ], 'id')

        with self.assertRaises(ValueError):
            utils.validate_xpaths_ref_to_unique_objects(self.XML_FILENAME, [
                "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']"
            ], 'id')

        with self.assertRaises(ValueError):
            utils.validate_xpaths_ref_to_unique_objects(self.XML_FILENAME, [
                '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species'
            ], 'id')
