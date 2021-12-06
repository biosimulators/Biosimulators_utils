import datetime
import dateutil.tz
import libcombine
import os
import re
import shutil
import tempfile
import unittest
from biosimulators_utils.archive.data_model import Archive, ArchiveFile
from biosimulators_utils.archive.io import ArchiveWriter
from biosimulators_utils.combine import data_model
from biosimulators_utils.combine import io
from biosimulators_utils.combine import validation
from biosimulators_utils.config import Config
from biosimulators_utils.data_model import Person
from biosimulators_utils.warnings import BioSimulatorsWarning
from unittest import mock


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
            '2/2.txt', format, True, description=description, authors=authors, created=None, updated=now)

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

        io.CombineArchiveWriter().run(archive1, in_dir, archive_file)
        archive1b = io.CombineArchiveReader().run(archive_file, out_dir, include_omex_metadata_files=False)
        self.assertTrue(archive1.is_equal(archive1b))

        archive1b = io.CombineArchiveReader().run(archive_file, out_dir, include_omex_metadata_files=True)
        metadata_contents = [content.location for content in archive1b.contents
                             if re.match(data_model.CombineArchiveContentFormatPattern.OMEX_METADATA.value, content.format)]
        self.assertEqual(metadata_contents, ['metadata.rdf', 'metadata_1.rdf', 'metadata_2.rdf'])

        self.assertEqual(sorted(os.listdir(out_dir)), sorted([
            content1.location, os.path.dirname(content2.location),
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf', 'metadata_2.rdf',
        ]))
        with open(os.path.join(out_dir, content1.location), 'r') as file:
            self.assertEqual('a', file.read())
        with open(os.path.join(out_dir, content2.location), 'r') as file:
            self.assertEqual('b', file.read())

        io.CombineArchiveWriter().run(archive2, in_dir, archive_file)
        archive2b = io.CombineArchiveReader().run(archive_file, out_dir2, include_omex_metadata_files=False)
        self.assertTrue(archive2.is_equal(archive2b))
        self.assertEqual(sorted(os.listdir(out_dir2)), sorted([
            content1.location,
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf',
        ]))
        with open(os.path.join(out_dir2, content1.location), 'r') as file:
            self.assertEqual('a', file.read())

        with self.assertRaisesRegex(ValueError, 'is not a file'):
            io.CombineArchiveReader().run(os.path.join(self.temp_dir, 'test2.omex'), out_dir)

    def test_no_updated_date(self):
        format = 'https://spec-url-for-format'
        description = 'Example content'
        authors = []
        content = data_model.CombineArchiveContent(
            '1.txt', format, False, description=description, created=None, updated=None)

        archive = data_model.CombineArchive([content], description=description, authors=authors, created=None, updated=None)

        archive_file = os.path.join(self.temp_dir, 'test.omex')
        in_dir = os.path.join(self.temp_dir, 'in')
        out_dir = os.path.join(self.temp_dir, 'out')
        os.mkdir(in_dir)
        os.mkdir(out_dir)

        with open(os.path.join(in_dir, content.location), 'w') as file:
            file.write('a')

        io.CombineArchiveWriter().run(archive, in_dir, archive_file)

        archive_b = io.CombineArchiveReader().run(archive_file, out_dir)
        archive_b.contents = list(filter(
            lambda content: content.format != data_model.CombineArchiveContentFormat.OMEX_METADATA,
            archive_b.contents))
        self.assertTrue(archive.is_equal(archive_b))

        self.assertEqual(sorted(os.listdir(out_dir)), sorted([
            content.location,
            'manifest.xml', 'metadata.rdf', 'metadata_1.rdf',
        ]))
        with open(os.path.join(out_dir, content.location), 'r') as file:
            self.assertEqual('a', file.read())

    def test_multiple_updated_dates(self):
        archive_file = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'multiple-updated-dates.omex')
        archive = io.CombineArchiveReader().run(archive_file, self.temp_dir)
        self.assertEqual(archive.updated, datetime.datetime(2020, 1, 1, 1, 1, 1, tzinfo=dateutil.tz.tzutc()))

    def test_read_error_handling(self):
        archive_file = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml-validation',
                                    'invalid-omex-manifest-missing-attribute.omex')
        with self.assertRaisesRegex(ValueError, 'must have the required attributes'):
            io.CombineArchiveReader().run(archive_file, self.temp_dir)

        with self.assertWarnsRegex(BioSimulatorsWarning, 'must have the required attributes'):
            with mock.patch.object(libcombine.CaError, 'isError', return_value=False):
                io.CombineArchiveReader().run(archive_file, self.temp_dir)

    def test_write_error_handling(self):
        now = datetime.datetime(2020, 1, 2, 1, 2, 3, tzinfo=dateutil.tz.tzutc())
        content = data_model.CombineArchiveContent(
            '1.txt', 'plain/text', False, description='description', created=now, updated=now)
        with open(os.path.join(self.temp_dir, content.location), 'w') as file:
            pass
        archive = data_model.CombineArchive([content], description='description', created=now, updated=now)

        archive_file = os.path.join(self.temp_dir, 'archive.omex')
        with self.assertRaisesRegex(Exception, 'could not be saved'):
            with mock.patch.object(libcombine.CombineArchive, 'writeToFile', return_value=False):
                io.CombineArchiveWriter().run(archive, self.temp_dir, archive_file)

        with self.assertRaisesRegex(Exception, 'could not be added to the archive'):
            with mock.patch.object(libcombine.CombineArchive, 'addFile', return_value=False):
                io.CombineArchiveWriter().run(archive, self.temp_dir, archive_file)

        with self.assertRaisesRegex(ValueError, 'my error'):
            with mock.patch('biosimulators_utils.combine.io.get_combine_errors_warnings', return_value=([['my error']], [])):
                io.CombineArchiveWriter().run(archive, self.temp_dir, archive_file)

        with self.assertWarnsRegex(BioSimulatorsWarning, 'my warning'):
            with mock.patch('biosimulators_utils.combine.io.get_combine_errors_warnings', return_value=([], [['my warning']])):
                io.CombineArchiveWriter().run(archive, self.temp_dir, archive_file)

        archive_file = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'invalid-parent-format-in-manifest.omex')
        out_dir = os.path.join(self.temp_dir, 'out-1')
        with self.assertRaisesRegex(ValueError, 'format of the archive must be'):
            io.CombineArchiveReader().run(archive_file, out_dir, include_omex_metadata_files=False)

        archive_file = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'missing-parent-in-manifest.omex')
        out_dir = os.path.join(self.temp_dir, 'out-2')
        with self.assertWarnsRegex(BioSimulatorsWarning, 'Manifests should include their parent COMBINE/OMEX archives'):
            io.CombineArchiveReader().run(archive_file, out_dir, include_omex_metadata_files=False)

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
        with self.assertRaisesRegex(ValueError, 'not a valid COMBINE/OMEX archive'):
            io.CombineArchiveReader().run(archive_filename, zip_out_dir)

        config = Config(VALIDATE_OMEX_MANIFESTS=False)
        archive = io.CombineArchiveReader().run(archive_filename, zip_out_dir, config=config)

        combine_archive = io.CombineArchiveZipReader().run(archive_filename, zip_out_dir)

        expected_combine_archive = data_model.CombineArchive(contents=[
            data_model.CombineArchiveContent(location='simulation.sedml', format=data_model.CombineArchiveContentFormat.SED_ML.value),
            data_model.CombineArchiveContent(location='model.xml'),
        ])
        self.assertTrue(combine_archive.is_equal(expected_combine_archive))

        combine_out_dir = os.path.join(self.temp_dir, 'out_combine')
        config = Config(VALIDATE_OMEX_MANIFESTS=False)
        combine_archive = io.CombineArchiveReader().run(archive_filename, combine_out_dir, config=config)
        self.assertTrue(combine_archive.is_equal(expected_combine_archive))

        # error handling
        with self.assertRaisesRegex(ValueError, 'not a valid zip archive'):
            io.CombineArchiveZipReader().run(sim_path, zip_out_dir)

        config = Config(VALIDATE_OMEX_MANIFESTS=False)
        with self.assertRaisesRegex(ValueError, 'not a valid COMBINE/OMEX archive'):
            io.CombineArchiveReader().run(sim_path, zip_out_dir, config=config)

        config = Config(VALIDATE_OMEX_MANIFESTS=True)
        with self.assertRaisesRegex(ValueError, 'not a valid COMBINE/OMEX archive'):
            io.CombineArchiveReader().run(sim_path, zip_out_dir, config=config)

    def test_sedml_validation_examples(self):
        dirname = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sedml-validation')

        filename = os.path.join(dirname, 'invalid-omex-manifest-missing-attribute.omex')
        with self.assertRaisesRegex(ValueError, 'must have the required attributes'):
            io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'a'))

        filename = os.path.join(dirname, 'invalid-sedml-missing-attribute.omex')
        archive = io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'b'))
        errors, warnings = validation.validate(archive, os.path.join(self.temp_dir, 'b'))
        self.assertNotEqual(errors, [])

        filename = os.path.join(dirname, 'invalid-sedml-missing-namespace.omex')
        archive = io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'c'))
        errors, warnings = validation.validate(archive, os.path.join(self.temp_dir, 'c'))
        self.assertNotEqual(errors, [])

        filename = os.path.join(dirname, 'invalid-sedml-multiple-errors.omex')
        archive = io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'd'))
        errors, warnings = validation.validate(archive, os.path.join(self.temp_dir, 'd'))
        self.assertNotEqual(errors, [])

        filename = os.path.join(dirname, 'warnings-sedml-sbml.omex')
        archive = io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'e'))
        errors, warnings = validation.validate(archive, os.path.join(self.temp_dir, 'e'))
        self.assertEqual(errors, [])
        self.assertNotEqual(warnings, [])

        filename = os.path.join(dirname, 'valid-sedml-sbml-qual.omex')
        archive = io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'f'))
        errors, warnings = validation.validate(archive, os.path.join(self.temp_dir, 'f'))
        self.assertEqual(errors, [])

        filename = os.path.join(dirname, 'valid-sedml-bngl.omex')
        archive = io.CombineArchiveReader().run(filename, os.path.join(self.temp_dir, 'g'))
        errors, warnings = validation.validate(archive, os.path.join(self.temp_dir, 'g'))
        self.assertEqual(errors, [])

    def test_write_read_manifest(self):
        manifest_filename = os.path.join(self.temp_dir, 'test.xml')
        contents = [
            data_model.CombineArchiveContent(
                location='1.txt',
                format='http://purl.org/NET/mediatypes/plain/text',
                master=False,
            ),
            data_model.CombineArchiveContent(
                location='2.jpg',
                format='http://purl.org/NET/mediatypes/image/jpeg',
                master=True,
            ),
        ]

        io.CombineArchiveWriter().write_manifest(contents, manifest_filename)
        contents_2 = io.CombineArchiveReader().read_manifest(manifest_filename)

        archive = data_model.CombineArchive(contents=contents)
        archive_2 = data_model.CombineArchive(contents=contents_2)
        self.assertTrue(archive_2.is_equal(archive))

    def test_write_read_manifest_with_manifest(self):
        manifest_filename = os.path.join(self.temp_dir, 'test.xml')
        contents = [
            data_model.CombineArchiveContent(
                location='1.txt',
                format='http://purl.org/NET/mediatypes/plain/text',
                master=False,
            ),
            data_model.CombineArchiveContent(
                location='2.jpg',
                format='http://purl.org/NET/mediatypes/image/jpeg',
                master=True,
            ),
            data_model.CombineArchiveContent(
                location='manifest.xml',
                format=data_model.CombineArchiveContentFormat.OMEX_MANIFEST,
                master=False,
            ),
        ]

        io.CombineArchiveWriter().write_manifest(contents, manifest_filename)
        contents_2 = io.CombineArchiveReader().read_manifest(manifest_filename)

        archive = data_model.CombineArchive(contents=contents)
        archive_2 = data_model.CombineArchive(contents=contents_2)
        self.assertTrue(archive_2.is_equal(archive))

    def test_read_manifest_from_plain_zip(self):
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

        config = Config(VALIDATE_OMEX_MANIFESTS=False)
        archive = io.CombineArchiveReader().run(archive_filename, zip_out_dir, config=config)
        self.assertEqual(len(archive.contents), 2)

        config = Config(VALIDATE_OMEX_MANIFESTS=True)
        with self.assertRaisesRegex(ValueError, 'not a valid COMBINE/OMEX archive'):
            io.CombineArchiveReader().run(archive_filename, zip_out_dir, config=config)

        manifest_filename = os.path.join(in_dir, 'manifest.xml')

        config = Config(VALIDATE_OMEX_MANIFESTS=False)
        archive.contents = io.CombineArchiveReader().read_manifest(manifest_filename, archive_filename, config=config)
        self.assertEqual(len(archive.contents), 3)

        config = Config(VALIDATE_OMEX_MANIFESTS=True)
        archive.contents = io.CombineArchiveReader().read_manifest(manifest_filename, archive_filename, config=config)
        self.assertEqual(len(archive.contents), 0)
