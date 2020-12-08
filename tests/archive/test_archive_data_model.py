import unittest
from biosimulators_utils.archive import data_model


class ArchiveDataModelTestCase(unittest.TestCase):
    def test(self):
        file = data_model.ArchiveFile(local_path='/local-path/to/file', archive_path='archive/path/to/file')
        self.assertEqual(file.local_path, '/local-path/to/file')
        self.assertEqual(file.archive_path, 'archive/path/to/file')
        self.assertEqual(file.to_tuple(), ('/local-path/to/file', 'archive/path/to/file'))

        file2 = data_model.ArchiveFile(local_path='/local-path/to/file', archive_path='archive/path/to/file')
        file3 = data_model.ArchiveFile(local_path='/local-path/to/file2', archive_path='archive/path/to/file')
        file4 = data_model.ArchiveFile(local_path='/local-path/to/file', archive_path='archive/path/to/file2')

        self.assertTrue(file.is_equal(file2))
        self.assertFalse(file.is_equal(file3))
        self.assertFalse(file.is_equal(file4))

        archive = data_model.Archive(files=[file, file3, file4])
        self.assertEqual(archive.files[1], file3)

        archive2 = data_model.Archive(files=[file, file3, file4])
        archive3 = data_model.Archive(files=[file, file3])
        self.assertTrue(archive.is_equal(archive2))
        self.assertFalse(archive.is_equal(archive3))

        self.assertEqual(archive.to_tuple(), (
            (
                ('/local-path/to/file', 'archive/path/to/file'),
                ('/local-path/to/file', 'archive/path/to/file2'),
                ('/local-path/to/file2', 'archive/path/to/file'),
            ),
        ))
