
from biosimulators_utils.xml import utils
from lxml import etree
import os
import shutil
import tempfile
import unittest


class XmlUtilsTestCase(unittest.TestCase):
    XML_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')
    MULTIPLE_NAMESPACES_XML_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-fbc-textbook.xml')

    def setUp(self):
        self.tmp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

    def test_get_namespaces_for_xml_doc(self):
        et = etree.parse(self.XML_FILENAME)
        self.assertEqual(utils.get_namespaces_for_xml_doc(et), {
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
            'math': 'http://www.w3.org/1998/Math/MathML',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'bqmodel': 'http://biomodels.net/model-qualifiers/',
            'bqbiol': 'http://biomodels.net/biology-qualifiers/',
            'vCard': 'http://www.w3.org/2001/vcard-rdf/3.0#',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'body': 'http://www.w3.org/1999/xhtml'
        })

        xml_filename = os.path.join(self.tmp_dirname, 'file.xml')
        with open(xml_filename, 'w') as file:
            file.write('<ns1:tag1 xmlns:ns1="https://ns1.org">')
            file.write('  <ns2:tag2 xmlns:ns2="https://ns2.org">')
            file.write('  </ns2:tag2>')
            file.write('</ns1:tag1>')
        et = etree.parse(xml_filename)
        self.assertEqual(utils.get_namespaces_for_xml_doc(et), {
            'ns1': 'https://ns1.org',
            'ns2': 'https://ns2.org',
        })

        xml_filename = os.path.join(self.tmp_dirname, 'file.xml')
        with open(xml_filename, 'w') as file:
            file.write('<ns1:tag1 xmlns:ns1="https://ns1.org">')
            file.write('  <ns2:tag2 xmlns:ns2="https://ns2.org">')
            file.write('    <ns1:tag2 xmlns:ns1="https://ns3.org">')
            file.write('    </ns1:tag2>')
            file.write('  </ns2:tag2>')
            file.write('</ns1:tag1>')
        et = etree.parse(xml_filename)
        with self.assertRaisesRegex(ValueError, 'Prefixes must be used consistently'):
            utils.get_namespaces_for_xml_doc(et)

    def test_get_attributes_of_xpaths(self):
        namespaces = {
            'sbml': 'http://www.sbml.org/sbml/level2/version4',
        }

        doc = etree.parse(self.XML_FILENAME)
        ids = utils.get_attributes_of_xpaths(doc, [
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
        ], namespaces, 'id')

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

        doc = etree.parse(self.XML_FILENAME)
        ids = utils.get_attributes_of_xpaths(doc, [
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species",
        ], namespaces, 'id')
        self.assertEqual(len(ids["/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species"]), 19)

    def test_get_attributes_of_xpaths_in_namespaces(self):
        namespaces = {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'fbc': 'http://www.sbml.org/sbml/level3/version1/fbc/version2',
        }

        doc = etree.parse(self.MULTIPLE_NAMESPACES_XML_FILENAME)
        ids = utils.get_attributes_of_xpaths(doc, [
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']",
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']",
        ], namespaces, 'id')
        expected_ids = {
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']": [None],
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']": [],
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']": ['R_ACALD'],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']": ['M_13dpg_c'],
        }
        self.assertEqual(ids, expected_ids)

        doc = etree.parse(self.MULTIPLE_NAMESPACES_XML_FILENAME)
        ids = utils.get_attributes_of_xpaths(doc, [
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']",
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']",
        ], namespaces, {'namespace': {'prefix': 'fbc', 'uri': namespaces['fbc']}, 'name': 'id'})
        expected_ids = {
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']": ['obj'],
            "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='inactive_obj']": [],
            "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']": [None],
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='M_13dpg_c']": [None],
        }
        self.assertEqual(ids, expected_ids)

    def test_validate_xpaths_ref_to_unique_objects(self):
        namespaces = {'sbml': 'http://www.sbml.org/sbml/level2/version4'}

        doc = etree.parse(self.XML_FILENAME)
        utils.validate_xpaths_ref_to_unique_objects(doc, [
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='BE']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='PSwe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1M']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Swe1']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Clg']",
            "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@name='Clb2']",
            "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='BUD']",
        ],
            namespaces,
            'id')

        with self.assertRaises(ValueError):
            utils.validate_xpaths_ref_to_unique_objects(etree, [
                "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='not_exist']"
            ], namespaces, 'id')

        with self.assertRaises(ValueError):
            utils.validate_xpaths_ref_to_unique_objects(etree, [
                '/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species'
            ], namespaces, 'id')

    def test_eval_xpath(self):
        root = etree.parse(self.XML_FILENAME).getroot()

        utils.eval_xpath(root, '/sbml:sbml/sbml:model', {'sbml': 'http://www.sbml.org/sbml/level2/version4'})
        utils.eval_xpath(root, '/sbml2:sbml/sbml2:model', {'sbml2': 'http://www.sbml.org/sbml/level2/version4'})

        with self.assertRaisesRegex(etree.XPathEvalError, 'Undefined namespace prefix'):
            utils.eval_xpath(root, '/sbml2:sbml/sbml2:model', {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        with self.assertRaisesRegex(etree.XPathEvalError, 'without namespaces'):
            utils.eval_xpath(root, '/sbml2:sbml/sbml2:model', {})
