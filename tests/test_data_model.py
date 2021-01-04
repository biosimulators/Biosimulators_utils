import unittest
from biosimulators_utils import data_model


class DataModelTestCase(unittest.TestCase):
    def test_author(self):
        author1 = data_model.Person(given_name='first', family_name='last')
        self.assertEqual(author1.given_name, 'first')
        self.assertEqual(author1.family_name, 'last')
        self.assertEqual(author1.to_tuple(), ('last', None, 'first'))

        author2 = data_model.Person(given_name='first', family_name='last')
        author3 = data_model.Person(given_name='last', family_name='first')
        self.assertTrue(author1.is_equal(author2))
        self.assertFalse(author1.is_equal(author3))

        identifier1 = data_model.Identifier(namespace='KISAO', id='KISAO_0000029')
        identifier2 = data_model.Identifier(namespace='KISAO', id='KISAO_0000029')
        identifier3 = data_model.Identifier(namespace='KISAO', id='KISAO_0000028')
        self.assertTrue(identifier1.is_equal(identifier2))
        self.assertFalse(identifier1.is_equal(identifier3))
