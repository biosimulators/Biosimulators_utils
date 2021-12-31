import datetime
import unittest
from biosimulators_utils.combine import data_model
from biosimulators_utils.data_model import Person


class DataModelTestCase(unittest.TestCase):
    def test_content(self):
        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        content = data_model.CombineArchiveContent(
            location, format)
        self.assertEqual(content.location, location)
        self.assertEqual(content.format, format)
        self.assertEqual(content.master, False)

        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        content = data_model.CombineArchiveContent(
            location, format)
        self.assertEqual(content.location, location)
        self.assertEqual(content.format, format)
        self.assertEqual(content.master, False)

        content2 = data_model.CombineArchiveContent(
            location, format, True)
        self.assertEqual(content2.to_tuple(), (
            location, format, True))

        content3 = data_model.CombineArchiveContent(
            location, format, True)
        self.assertTrue(content.is_equal(content))
        self.assertFalse(content.is_equal(content2))
        self.assertTrue(content2.is_equal(content2))
        self.assertTrue(content2.is_equal(content3))

    def test_archive(self):
        location = 'path_to_file'
        format = 'https://spec-url-for-format'
        content1 = data_model.CombineArchiveContent(
            location, format, False)
        content2 = data_model.CombineArchiveContent(
            location, format, True)

        archive = data_model.CombineArchive()
        self.assertEqual(archive.contents, [])

        archive = data_model.CombineArchive([content1, content2])
        self.assertEqual(archive.contents, [content1, content2])

        self.assertEqual(archive.to_tuple(), (
            (content1.to_tuple(), content2.to_tuple())))

        archive2 = data_model.CombineArchive([content2, content1])
        archive3 = data_model.CombineArchive([content1, content1])
        self.assertTrue(archive.is_equal(archive2))
        self.assertFalse(archive.is_equal(archive3))

        archive4 = data_model.CombineArchive([content2, content2])
        self.assertEqual(archive.get_master_content(), [content2])
        self.assertEqual(archive3.get_master_content(), [])
        self.assertEqual(archive4.get_master_content(), [content2, content2])
