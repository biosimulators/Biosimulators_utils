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
