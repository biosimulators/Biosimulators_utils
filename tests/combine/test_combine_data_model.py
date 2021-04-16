import datetime
import unittest
from biosimulators_utils.combine import data_model
from biosimulators_utils.data_model import Person


class DataModelTestCase(unittest.TestCase):
    def test_content(self):
        author1 = Person(given_name='first1', family_name='last1')
        author2 = Person(given_name='first2', family_name='last2')

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        content = data_model.CombineArchiveContent(
            location, format,
            description=description)
        self.assertEqual(content.location, location)
        self.assertEqual(content.format, format)
        self.assertEqual(content.master, False)
        self.assertEqual(content.description, description)
        self.assertEqual(content.authors, [])
        self.assertEqual(content.created, None)
        self.assertEqual(content.updated, None)

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = [author1, author2]
        now = datetime.datetime.now()
        content = data_model.CombineArchiveContent(
            location, format,
            description=description, authors=authors, created=now, updated=now)
        self.assertEqual(content.location, location)
        self.assertEqual(content.format, format)
        self.assertEqual(content.master, False)
        self.assertEqual(content.description, description)
        self.assertEqual(content.authors, [author1, author2])
        self.assertEqual(content.created, now)
        self.assertEqual(content.updated, now)

        content2 = data_model.CombineArchiveContent(
            location, format, True,
            description=description, authors=authors, created=now, updated=now)
        self.assertEqual(content2.to_tuple(), (
            location, format, True, description, (author1.to_tuple(), author2.to_tuple()), now, now))

        content3 = data_model.CombineArchiveContent(
            location, format, True,
            description=description, authors=[author2, author1], created=now, updated=now)
        content4 = data_model.CombineArchiveContent(
            location, format, True,
            description=description, authors=[author1, author1], created=now, updated=now)
        self.assertTrue(content.is_equal(content))
        self.assertFalse(content.is_equal(content2))
        self.assertTrue(content2.is_equal(content2))
        self.assertTrue(content2.is_equal(content3))
        self.assertFalse(content2.is_equal(content4))

    def test_archive(self):
        author1 = Person(given_name='first1', family_name='last1')
        author2 = Person(given_name='first2', family_name='last2')

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = [author1, author2]
        now = datetime.datetime.now()
        content1 = data_model.CombineArchiveContent(
            location, format, False, description=description, authors=authors, created=now, updated=now)
        content2 = data_model.CombineArchiveContent(
            location, format, True, description=description, authors=authors, created=now, updated=now)

        archive = data_model.CombineArchive()
        self.assertEqual(archive.contents, [])
        self.assertEqual(archive.description, None)
        self.assertEqual(archive.authors, [])
        self.assertEqual(archive.created, None)
        self.assertEqual(archive.updated, None)

        archive = data_model.CombineArchive([content1, content2], description=description, authors=authors, created=now, updated=now)
        self.assertEqual(archive.contents, [content1, content2])
        self.assertEqual(archive.description, description)
        self.assertEqual(archive.authors, [author1, author2])
        self.assertEqual(archive.created, now)
        self.assertEqual(archive.updated, now)

        self.assertEqual(archive.to_tuple(), (
            (content1.to_tuple(), content2.to_tuple()), description, (author1.to_tuple(), author2.to_tuple()), now, now))

        archive2 = data_model.CombineArchive([content2, content1], description=description, authors=authors, created=now, updated=now)
        archive3 = data_model.CombineArchive([content1, content1], description=description, authors=authors, created=now, updated=now)
        self.assertTrue(archive.is_equal(archive2))
        self.assertFalse(archive.is_equal(archive3))

        archive4 = data_model.CombineArchive([content2, content2], description=description, authors=authors, created=now, updated=now)
        self.assertEqual(archive.get_master_content(), [content2])
        self.assertEqual(archive3.get_master_content(), [])
        self.assertEqual(archive4.get_master_content(), [content2, content2])
