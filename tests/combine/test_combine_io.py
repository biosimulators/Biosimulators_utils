import datetime
import dateutil.tz
import os
import shutil
import tempfile
import unittest
from biosimulators_utils.combine import data_model
from biosimulators_utils.combine import io


class ReadWriteTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test(self):
        author1 = data_model.CombineArchiveAuthor(given_name='first1', family_name='last1')
        author2 = data_model.CombineArchiveAuthor(given_name='first2', family_name='last2')

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = [author1, author2]
        now = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        content1 = data_model.CombineArchiveContent(
            '1.txt', format, False, description=description, authors=authors, created=now, updated=now)
        content2 = data_model.CombineArchiveContent(
            '2/2.txt', None, True, description=description, authors=authors, created=None, updated=now)

        archive1 = data_model.CombineArchive([content1, content2], description=description, authors=authors, created=now, updated=now)
        archive2 = data_model.CombineArchive([content1, content1], description=description, authors=authors, created=None, updated=now)
        archive3 = data_model.CombineArchive([content1, content1], description=description, authors=authors, created=None, updated=None)

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

        io.CombineArchiveWriter.run(archive1, in_dir, archive_file)
        archive1b = io.CombineArchiveReader.run(archive_file, out_dir)
        self.assertTrue(archive1.is_equal(archive1b))

        self.assertEqual(sorted(os.listdir(out_dir)), sorted([
            content1.location, os.path.dirname(content2.location),
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf', 'metadata_2.rdf',
        ]))
        with open(os.path.join(out_dir, content1.location), 'r') as file:
            self.assertEqual('a', file.read())
        with open(os.path.join(out_dir, content2.location), 'r') as file:
            self.assertEqual('b', file.read())

        io.CombineArchiveWriter.run(archive2, in_dir, archive_file)
        archive2b = io.CombineArchiveReader.run(archive_file, out_dir2)
        self.assertTrue(archive2.is_equal(archive2b))
        self.assertEqual(sorted(os.listdir(out_dir2)), sorted([
            content1.location,
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf',
        ]))
        with open(os.path.join(out_dir2, content1.location), 'r') as file:
            self.assertEqual('a', file.read())

        with self.assertRaisesRegex(ValueError, 'Invalid COMBINE archive'):
            io.CombineArchiveReader.run(os.path.join(self.temp_dir, 'test2.omex'), out_dir)

        with self.assertRaisesRegex(NotImplementedError, 'libcombine does not support undefined updated dates'):
            io.CombineArchiveWriter.run(archive3, in_dir, archive_file)
