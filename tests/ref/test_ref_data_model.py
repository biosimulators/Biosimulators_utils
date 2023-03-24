from biosimulators_utils.ref.data_model import JournalArticle
import unittest


class RefDataModeTestCase(unittest.TestCase):
    def test_JournalArticle_get_citation(self):
        ref = JournalArticle()
        self.assertEqual(ref.get_citation(), None)

        ref = JournalArticle(
            authors=['John Doe'])
        self.assertEqual(ref.get_citation(), 'John Doe.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe'])
        self.assertEqual(ref.get_citation(), 'John Doe & Jane Doe.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'])
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title?',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title?')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title?',
            journal='Journal',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title? Journal.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title',
            journal='Journal',
            volume='10',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title. Journal 10.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title',
            journal='Journal',
            volume='10',
            issue='1',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title. Journal 10, 1.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title',
            journal='Journal',
            volume='10',
            issue='1',
            pages='10-20',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title. Journal 10, 1: 10-20.')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title',
            journal='Journal',
            volume='10',
            issue='1',
            pages='10-20',
            year='2021',
        )
        self.assertEqual(ref.get_citation(), 'John Doe, Jane Doe & Jim Doe. My title. Journal 10, 1: 10-20 (2021).')

    def test_JournalArticle_get_uri(self):
        ref = JournalArticle()
        self.assertEqual(ref.get_citation(), None)

        ref = JournalArticle(
            pubmed_id='15345435',
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/pubmed/15345435')

        ref = JournalArticle(
            pubmed_central_id="PMC520924",
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/pmc/PMC520924')

        ref = JournalArticle(
            doi="10.1128/AEM.70.9.5477-5484.2004",
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/doi/10.1128/AEM.70.9.5477-5484.2004')

        ref = JournalArticle(
            pubmed_id='15345435',
            pubmed_central_id="PMC520924",
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/pubmed/15345435')

        ref = JournalArticle(
            pubmed_central_id="PMC520924",
            doi="10.1128/AEM.70.9.5477-5484.2004",
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/doi/10.1128/AEM.70.9.5477-5484.2004')

        ref = JournalArticle(
            pubmed_id='15345435',
            doi="10.1128/AEM.70.9.5477-5484.2004",
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/doi/10.1128/AEM.70.9.5477-5484.2004')

        ref = JournalArticle(
            pubmed_id='15345435',
            pubmed_central_id="PMC520924",
            doi="10.1128/AEM.70.9.5477-5484.2004",
            )
        self.assertEqual(ref.get_uri(), 'http://identifiers.org/doi/10.1128/AEM.70.9.5477-5484.2004')

        ref = JournalArticle(
            authors=['John Doe', 'Jane Doe', 'Jim Doe'],
            title='My title',
            journal='Journal',
            volume='10',
            issue='1',
            pages='10-20',
            year='2021',
        )
        self.assertEqual(ref.get_uri(), None)
