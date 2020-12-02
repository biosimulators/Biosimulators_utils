import datetime
import dateutil.tz
import os
import shutil
import tempfile
import unittest
from biosimulators_utils import combine


class DataModelTestCase(unittest.TestCase):
    def test_author(self):
        author1 = combine.CombineArchiveAuthor(given_name='first', family_name='last')
        self.assertEqual(author1.given_name, 'first')
        self.assertEqual(author1.family_name, 'last')
        self.assertEqual(author1.to_tuple(), ('last', 'first'))

        author2 = combine.CombineArchiveAuthor(given_name='first', family_name='last')
        author3 = combine.CombineArchiveAuthor(given_name='last', family_name='first')
        self.assertTrue(author1.is_equal(author2))
        self.assertFalse(author1.is_equal(author3))

    def test_content(self):
        author1 = combine.CombineArchiveAuthor(given_name='first1', family_name='last1')
        author2 = combine.CombineArchiveAuthor(given_name='first2', family_name='last2')

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        content = combine.CombineArchiveContent(
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
        content = combine.CombineArchiveContent(
            location, format,
            description=description, authors=authors, created=now, updated=now)
        self.assertEqual(content.location, location)
        self.assertEqual(content.format, format)
        self.assertEqual(content.master, False)
        self.assertEqual(content.description, description)
        self.assertEqual(content.authors, [author1, author2])
        self.assertEqual(content.created, now)
        self.assertEqual(content.updated, now)

        content2 = combine.CombineArchiveContent(
            location, format, True,
            description=description, authors=authors, created=now, updated=now)
        self.assertEqual(content2.to_tuple(), (
            location, format, True, description, (author1.to_tuple(), author2.to_tuple()), now, now))

        content3 = combine.CombineArchiveContent(
            location, format, True,
            description=description, authors=[author2, author1], created=now, updated=now)
        content4 = combine.CombineArchiveContent(
            location, format, True,
            description=description, authors=[author1, author1], created=now, updated=now)
        self.assertTrue(content.is_equal(content))
        self.assertFalse(content.is_equal(content2))
        self.assertTrue(content2.is_equal(content2))
        self.assertTrue(content2.is_equal(content3))
        self.assertFalse(content2.is_equal(content4))

    def test_archive(self):
        author1 = combine.CombineArchiveAuthor(given_name='first1', family_name='last1')
        author2 = combine.CombineArchiveAuthor(given_name='first2', family_name='last2')

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = [author1, author2]
        now = datetime.datetime.now()
        content1 = combine.CombineArchiveContent(
            location, format, False, description=description, authors=authors, created=now, updated=now)
        content2 = combine.CombineArchiveContent(
            location, format, True, description=description, authors=authors, created=now, updated=now)

        archive = combine.CombineArchive()
        self.assertEqual(archive.contents, [])
        self.assertEqual(archive.description, None)
        self.assertEqual(archive.authors, [])
        self.assertEqual(archive.created, None)
        self.assertEqual(archive.updated, None)

        archive = combine.CombineArchive([content1, content2], description=description, authors=authors, created=now, updated=now)
        self.assertEqual(archive.contents, [content1, content2])
        self.assertEqual(archive.description, description)
        self.assertEqual(archive.authors, [author1, author2])
        self.assertEqual(archive.created, now)
        self.assertEqual(archive.updated, now)

        self.assertEqual(archive.to_tuple(), (
            (content1.to_tuple(), content2.to_tuple()), description, (author1.to_tuple(), author2.to_tuple()), now, now))

        archive2 = combine.CombineArchive([content2, content1], description=description, authors=authors, created=now, updated=now)
        archive3 = combine.CombineArchive([content1, content1], description=description, authors=authors, created=now, updated=now)
        self.assertTrue(archive.is_equal(archive2))
        self.assertFalse(archive.is_equal(archive3))

        archive4 = combine.CombineArchive([content2, content2], description=description, authors=authors, created=now, updated=now)
        self.assertEqual(archive.get_master_content(), content2)
        self.assertEqual(archive3.get_master_content(), None)
        with self.assertRaisesRegex(ValueError, 'Multiple content items are marked as master'):
            archive4.get_master_content()


class ReadWriteTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test(self):
        author1 = combine.CombineArchiveAuthor(given_name='first1', family_name='last1')
        author2 = combine.CombineArchiveAuthor(given_name='first2', family_name='last2')

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = [author1, author2]
        now = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        content1 = combine.CombineArchiveContent(
            '1.txt', format, False, description=description, authors=authors, created=now, updated=now)
        content2 = combine.CombineArchiveContent(
            '2/2.txt', None, True, description=description, authors=authors, created=None, updated=now)

        archive1 = combine.CombineArchive([content1, content2], description=description, authors=authors, created=now, updated=now)
        archive2 = combine.CombineArchive([content1, content1], description=description, authors=authors, created=None, updated=now)
        archive3 = combine.CombineArchive([content1, content1], description=description, authors=authors, created=None, updated=None)

        archive_file = os.path.join(self.temp_dir, 'test.omex')
        in_dir = os.path.join(self.temp_dir, 'in')
        out_dir = os.path.join(self.temp_dir, 'out')
        out_dir2 = os.path.join(self.temp_dir, 'out2')
        os.mkdir(in_dir)
        os.mkdir(os.path.join(in_dir, '2'))
        os.mkdir(out_dir)

        with open(os.path.join(in_dir, content1.location), 'w') as file:
            file.write('a')
        with open(os.path.join(in_dir, content2.location), 'w') as file:
            file.write('b')

        combine.CombineArchiveWriter.run(archive1, in_dir, archive_file)
        archive1b = combine.CombineArchiveReader.run(archive_file, out_dir)
        self.assertTrue(archive1.is_equal(archive1b))

        self.assertEqual(sorted(os.listdir(out_dir)), sorted([
            content1.location, os.path.dirname(content2.location),
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf', 'metadata_2.rdf',
        ]))
        with open(os.path.join(out_dir, content1.location), 'r') as file:
            self.assertEqual('a', file.read())
        with open(os.path.join(out_dir, content2.location), 'r') as file:
            self.assertEqual('b', file.read())

        combine.CombineArchiveWriter.run(archive2, in_dir, archive_file)
        archive2b = combine.CombineArchiveReader.run(archive_file, out_dir2)
        self.assertTrue(archive2.is_equal(archive2b))
        self.assertEqual(sorted(os.listdir(out_dir2)), sorted([
            content1.location,
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf',
        ]))
        with open(os.path.join(out_dir2, content1.location), 'r') as file:
            self.assertEqual('a', file.read())

        with self.assertRaisesRegex(ValueError, 'Invalid COMBINE archive'):
            combine.CombineArchiveReader.run(os.path.join(self.temp_dir, 'test2.omex'), out_dir)

        with self.assertRaisesRegex(NotImplementedError, 'libcombine does not support undefined updated dates'):
            combine.CombineArchiveWriter.run(archive3, in_dir, archive_file)
