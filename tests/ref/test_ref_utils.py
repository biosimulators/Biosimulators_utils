from biosimulators_utils.ref import utils
import Bio.Entrez
import os
import shutil
import tempfile
import unittest

Bio.Entrez.email = 'biosimulators.daemon@gmail.com'


class RefUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_get_reference_from_pubmed(self):
        ref = utils.get_reference_from_pubmed('1234')
        self.assertEqual(ref.journal, 'Drug metabolism and disposition: the biological fate of chemicals')
        self.assertEqual(ref.year, '1975')

        ref = utils.get_reference_from_pubmed('23184105')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')

        ref = utils.get_reference_from_pubmed(pubmed_id=None, doi='10.1542/peds.2012-2758')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, '23184105')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')

        ref = utils.get_reference_from_pubmed(pubmed_id=None, doi='10.1103/PhysRevLett.127.104301x')
        self.assertEqual(ref, None)

        with self.assertRaises(ValueError):
            utils.get_reference_from_pubmed('000')

    def test_get_reference_from_crossref(self):
        ref = utils.get_reference_from_crossref('10.1542/peds.2012-2758')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, None)
        self.assertEqual(ref.pubmed_central_id, None)
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')

    def test_get_reference(self):
        ref = utils.get_reference(pubmed_id='23184105')
        self.assertEqual(ref.authors, ['J. R. Roberts', 'C. J. Karr', 'COUNCIL ON ENVIRONMENTAL HEALTH'])
        self.assertEqual(ref.title, 'Pesticide exposure in children')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, '23184105')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')

        ref = utils.get_reference(doi='10.1542/peds.2012-2758')
        self.assertEqual(ref.authors, ['J. R. Roberts', 'C. J. Karr', 'COUNCIL ON ENVIRONMENTAL HEALTH'])
        self.assertEqual(ref.title, 'Pesticide exposure in children')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, '23184105')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')

        with self.assertRaises(ValueError):
            utils.get_reference()

    def test_get_pubmed_central_open_access_graphics(self):
        shutil.rmtree(self.dirname)

        self.assertEqual(utils.get_pubmed_central_open_access_graphics('PMC5813803', self.dirname), [])

        images = utils.get_pubmed_central_open_access_graphics('PMC6684142', self.dirname)
        self.assertEqual(len(images), 2)

        print(images[0].id)
        self.assertEqual(images[0].id, '10.1177_2473974X19861567/fig1-2473974X19861567')
        self.assertEqual(images[0].label, 'Figure 1')
        self.assertTrue(images[0].caption.startswith('<p xmlns:xlink'))
        self.assertTrue(os.path.isfile(images[0].filename))
