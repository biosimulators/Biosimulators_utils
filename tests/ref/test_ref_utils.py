from biosimulators_utils.ref import utils
from unittest import mock
import Bio.Entrez
import flaky
import ftplib
import os
import random
import shutil
import string
import tempfile
import time
import unittest

email_suffix = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
Bio.Entrez.email = 'biosimulators.daemon-{}@gmail.com'.format(email_suffix)


class RefUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    @unittest.skip("avoiding network requests in CI")
    def test_search_entrez_records(self):
        self.assertEqual(utils.search_entrez_records('pmc', '23184105[pmid]')['IdList'], ['5813803'])
        time.sleep(5)

        self.assertEqual(utils.search_entrez_records('pmc', 'abc[pmid]')['Count'], '0')
        time.sleep(5)

        with self.assertRaisesRegex(TypeError, 'must be a non-empty string'):
            utils.search_entrez_records('pmc', None)
        with self.assertRaisesRegex(TypeError, 'must be a non-empty string'):
            utils.search_entrez_records('pmc', '')
        with self.assertRaisesRegex(TypeError, 'must be a non-empty string'):
            utils.search_entrez_records('pmc', 23184105)

    @unittest.skip("avoiding network requests in CI")
    def test_get_entrez_record(self):
        self.assertEqual(utils.get_entrez_record('pmc', '5813803')['Id'], '5813803')
        time.sleep(5)

        with self.assertRaisesRegex(ValueError, 'is not a valid id'):
            utils.get_entrez_record('pubmed', 'abc')

        with self.assertRaisesRegex(TypeError, 'must be a string'):
            utils.get_entrez_record('pmc', None)

    @unittest.skip("avoiding network requests in CI")
    @flaky.flaky(max_runs=5, min_passes=1)
    def test_get_pubmed_central_id(self):
        self.assertEqual(utils.get_pubmed_central_id('23184105'), 'PMC5813803')
        time.sleep(5)

        self.assertEqual(utils.get_pubmed_central_id('1234'), None)
        time.sleep(5)

        self.assertEqual(utils.get_pubmed_central_id(1234), None)
        time.sleep(5)

        self.assertEqual(utils.get_pubmed_central_id('abc'), None)
        time.sleep(5)

        self.assertEqual(utils.get_pubmed_central_id(None), None)
        time.sleep(5)

    @unittest.skip("avoiding network requests in CI")
    def test_get_reference_from_pubmed(self):
        ref = utils.get_reference_from_pubmed('1234')
        self.assertEqual(ref.journal, 'Drug metabolism and disposition: the biological fate of chemicals')
        self.assertEqual(ref.year, '1975')
        time.sleep(5)

        ref = utils.get_reference_from_pubmed('23184105')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')
        time.sleep(5)

        ref = utils.get_reference_from_pubmed(pubmed_id=None, doi='10.1542/peds.2012-2758')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, '23184105')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')
        time.sleep(5)

        ref = utils.get_reference_from_pubmed(pubmed_id=None, doi='10.1103/PhysRevLett.127.104301x')
        self.assertEqual(ref, None)
        time.sleep(5)

        ref = utils.get_reference_from_pubmed(None, None)
        self.assertEqual(ref, None)
        time.sleep(5)

        with self.assertRaisesRegex(ValueError, 'not a valid id'):
            utils.get_reference_from_pubmed(pubmed_id='abc')
        time.sleep(5)

        with self.assertRaises(ValueError):
            utils.get_reference_from_pubmed('000')
        time.sleep(5)

    @unittest.skip("avoiding network requests in CI")
    def test_get_reference_from_crossref(self):
        ref = utils.get_reference_from_crossref('10.1542/peds.2012-2758')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, None)
        self.assertEqual(ref.pubmed_central_id, None)
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')

    @unittest.skip("avoiding network requests in CI")
    def test_get_reference(self):
        authors = [
            [
                'Roberts JR',
                'Karr CJ',
                'Council On Environmental Health.',
            ],
            [
                'James R. Roberts',
                'Catherine J. Karr',
                'COUNCIL ON ENVIRONMENTAL HEALTH',
                'Jerome A. Paulson',
                'Alice C. Brock-Utne',
                'Heather L. Brumberg',
                'Carla C. Campbell',
                'Bruce P. Lanphear',
                'Kevin C. Osterhoudt',
                'Megan T. Sandel',
                'Leonardo Trasande',
                'Robert O. Wright',
            ],
        ]

        ref = utils.get_reference(pubmed_id='23184105')
        self.assertIn(ref.authors, authors)
        self.assertEqual(ref.title, 'Pesticide exposure in children')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, '23184105')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')
        time.sleep(5)

        ref = utils.get_reference(doi='10.1542/peds.2012-2758')
        self.assertIn(ref.authors, authors)
        self.assertEqual(ref.title, 'Pesticide exposure in children')
        self.assertEqual(ref.year, '2012')
        self.assertEqual(ref.pubmed_id, '23184105')
        self.assertEqual(ref.pubmed_central_id, 'PMC5813803')
        self.assertEqual(ref.doi, '10.1542/peds.2012-2758')
        time.sleep(5)

        ref = utils.get_reference(pubmed_id='1234')
        self.assertEqual(ref.doi, None)
        time.sleep(5)

        with self.assertRaises(ValueError):
            utils.get_reference()

    @unittest.skip("avoiding network requests in CI")
    def test_get_pubmed_central_open_access_graphics(self):
        shutil.rmtree(self.dirname)

        self.assertEqual(utils.get_pubmed_central_open_access_graphics('PMC5813803', self.dirname), [])

        images = utils.get_pubmed_central_open_access_graphics('PMC6684142', self.dirname)
        self.assertEqual(len(images), 2)

        self.assertEqual(images[0].id, '10.1177_2473974X19861567/fig1-2473974X19861567')
        self.assertEqual(images[0].label, 'Figure 1')
        self.assertTrue(images[0].caption.startswith('<p xmlns:xlink'))
        self.assertTrue(os.path.isfile(images[0].filename))

    @unittest.skip("avoiding network requests in CI")
    def test_download_pubmed_central_record(self):
        tgz_filename = os.path.join(self.dirname, 'record.tar.gz')

        def save_tgz_file(_, writer):
            pass

        with self.assertRaisesRegex(Exception, 'could not be downloaded'):
            with mock.patch.object(ftplib.FTP, 'retrbinary', side_effect=save_tgz_file):
                utils.download_pubmed_central_record('PMC6684142', '', tgz_filename, self.dirname)
