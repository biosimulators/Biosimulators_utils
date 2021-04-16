import datetime
import dateutil.tz
import os
import shutil
import tempfile
import unittest
from biosimulators_utils.archive.data_model import Archive, ArchiveFile
from biosimulators_utils.archive.io import ArchiveWriter
from biosimulators_utils.combine import data_model
from biosimulators_utils.combine import io
from biosimulators_utils.data_model import Person


class ReadWriteTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test(self):
        author1 = Person(given_name='first1', family_name='last1')
        author2 = Person(given_name='first2', family_name='last2')

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

        with self.assertRaisesRegex(ValueError, 'does not exist'):
            io.CombineArchiveReader.run(os.path.join(self.temp_dir, 'test2.omex'), out_dir)

    @unittest.expectedFailure
    def test_no_updated_date(self):
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = []
        now = None
        content = data_model.CombineArchiveContent(
            '1.txt', format, False, description=description, created=None, updated=now)

        archive = data_model.CombineArchive([content], description=description, authors=authors, created=None, updated=now)

        archive_file = os.path.join(self.temp_dir, 'test.omex')
        in_dir = os.path.join(self.temp_dir, 'in')
        out_dir = os.path.join(self.temp_dir, 'out')
        os.mkdir(in_dir)
        os.mkdir(out_dir)

        with open(os.path.join(in_dir, content.location), 'w') as file:
            file.write('a')

        with self.assertRaisesRegex(NotImplementedError, 'libcombine does not support undefined updated dates'):
            io.CombineArchiveWriter.run(archive, in_dir, archive_file)

        io.CombineArchiveWriter.run(archive, in_dir, archive_file)

        archive_b = io.CombineArchiveReader.run(archive_file, out_dir)
        self.assertTrue(archive.is_equal(archive_b))

        self.assertEqual(sorted(os.listdir(out_dir)), sorted([
            content.location,
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf',
        ]))
        with open(os.path.join(out_dir, content.location), 'r') as file:
            self.assertEqual('a', file.read())

    def test_read_from_plain_zip_archive(self):
        in_dir = os.path.join(self.temp_dir, 'in')
        os.mkdir(in_dir)
        sim_path = os.path.join(in_dir, 'simulation.sedml')
        model_path = os.path.join(in_dir, 'model.xml')
        archive_filename = os.path.join(in_dir, 'archive.zip')
        with open(sim_path, 'w'):
            pass
        with open(model_path, 'w'):
            pass

        archive = Archive(files=[
            ArchiveFile(local_path=sim_path, archive_path='simulation.sedml'),
            ArchiveFile(local_path=model_path, archive_path='model.xml'),
        ])

        ArchiveWriter().run(archive, archive_filename)

        zip_out_dir = os.path.join(self.temp_dir, 'out_zip')
        combine_archive = io.CombineArchiveZipReader().run(archive_filename, zip_out_dir)

        expected_combine_archive = data_model.CombineArchive(contents=[
            data_model.CombineArchiveContent(location='simulation.sedml', format=data_model.CombineArchiveContentFormat.SED_ML.value),
            data_model.CombineArchiveContent(location='model.xml'),
        ])
        self.assertTrue(combine_archive.is_equal(expected_combine_archive))

        combine_out_dir = os.path.join(self.temp_dir, 'out_combine')
        combine_archive = io.CombineArchiveReader().run(archive_filename, combine_out_dir)
        self.assertTrue(combine_archive.is_equal(expected_combine_archive))

        # error handling
        with self.assertRaisesRegex(ValueError, 'not a valid zip archive'):
            io.CombineArchiveZipReader().run(sim_path, zip_out_dir)

        with self.assertRaisesRegex(ValueError, 'not a valid COMBINE/OMEX archive'):
            io.CombineArchiveReader().run(sim_path, zip_out_dir, try_reading_as_plain_zip_archive=True)

        with self.assertRaisesRegex(ValueError, 'not a valid COMBINE/OMEX archive'):
            io.CombineArchiveReader().run(sim_path, zip_out_dir, try_reading_as_plain_zip_archive=False)
