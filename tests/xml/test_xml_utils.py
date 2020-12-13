from biosimulators_utils.xml import utils
import os
import unittest


class XmlUtilsTestCase(unittest.TestCase):
    XML_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')

    def test_get_num_matches_to_xpaths(self):
        counts = utils.get_num_matches_to_xpaths(self.XML_FILENAME, [
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
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']",
        ])

        expected_counts = {
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']": 1,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']": 1,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']": 1,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']": 1,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BUD']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clb2']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']": 1,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='SBF_a']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Sic1']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cdc20_a']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Cdh1_a']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='IE_a']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1_total']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_0']": 0,
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']": 1,
            '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species': 19,
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']": 1,
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']": 0,
        }
        for key, count in counts.items():
            self.assertEqual(count, expected_counts[key], key)

    def test_validate_xpaths_ref_to_unique_objects(self):
        utils.validate_xpaths_ref_to_unique_objects(self.XML_FILENAME, [
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']",
        ])

        with self.assertRaises(ValueError):
            utils.validate_xpaths_ref_to_unique_objects(self.XML_FILENAME, [
                "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']"
            ])

        with self.assertRaises(ValueError):
            utils.validate_xpaths_ref_to_unique_objects(self.XML_FILENAME, [
                '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species'
            ])
