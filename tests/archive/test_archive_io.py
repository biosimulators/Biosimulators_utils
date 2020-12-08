from biosimulators_utils.archive import data_model
from biosimulators_utils.archive import io
from biosimulators_utils.archive import utils
import os
import shutil
import tempfile
import unittest


class ArchiveIoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        filename1 = os.path.join(self.tmp_dir, 'test1')
        filename2 = os.path.join(self.tmp_dir, 'test2')
        filename3 = os.path.join(self.tmp_dir, 'test3')
        with open(filename1, 'w') as file:
            file.write('ABC')
        with open(filename2, 'w') as file:
            file.write('DEF')
        with open(filename3, 'w') as file:
            file.write('GHI')

        archive = data_model.Archive(files=[
            data_model.ArchiveFile(local_path=filename1, archive_path='a/b/c/test1.txt'),
            data_model.ArchiveFile(local_path=filename2, archive_path='test2.txt'),
            data_model.ArchiveFile(local_path=filename3, archive_path='a/b/test3.txt'),
        ])

        archive_filename = os.path.join(self.tmp_dir, 'test.zip')
        io.ArchiveWriter().run(archive, archive_filename)

        archive_outdir = os.path.join(self.tmp_dir, 'out')
        archive2 = io.ArchiveReader().run(archive_filename, archive_outdir)

        file = next(file for file in archive2.files if file.archive_path == archive.files[0].archive_path)
        self.assertEqual(file.local_path, os.path.join(archive_outdir, archive.files[0].archive_path))
        with open(file.local_path, 'r') as file:
            self.assertEqual(file.read(), 'ABC')

        file = next(file for file in archive2.files if file.archive_path == archive.files[1].archive_path)
        self.assertEqual(file.local_path, os.path.join(archive_outdir, archive.files[1].archive_path))
        with open(file.local_path, 'r') as file:
            self.assertEqual(file.read(), 'DEF')

        file = next(file for file in archive2.files if file.archive_path == archive.files[2].archive_path)
        self.assertEqual(file.local_path, os.path.join(archive_outdir, archive.files[2].archive_path))
        with open(file.local_path, 'r') as file:
            self.assertEqual(file.read(), 'GHI')

        archive3 = utils.build_archive_from_paths([os.path.join(archive_outdir, '**')])
        self.assertFalse(archive2.is_equal(archive3))

        archive3 = utils.build_archive_from_paths([os.path.join(archive_outdir, '**')], archive_outdir)
        self.assertTrue(archive2.is_equal(archive3))
