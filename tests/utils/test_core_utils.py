from biosimulators_utils.data_model import ValueType, OntologyTerm
from biosimulators_utils.utils import core as utils
from biosimulators_utils.warnings import BioSimulatorsWarning
import copy
import re
import unittest


class TestCase(unittest.TestCase):
    def test_are_lists_equal(self):
        class Obj(str):
            def is_equal(self, other):
                return self == other

            def to_tuple(self):
                return self

        self.assertTrue(utils.are_lists_equal([Obj('a')], [Obj('a')]))
        self.assertFalse(utils.are_lists_equal([Obj('a')], [Obj('b')]))

        self.assertTrue(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('a'), Obj('b')]))
        self.assertFalse(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('a')]))
        self.assertFalse(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('a'), Obj('c')]))

        self.assertTrue(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('b'), Obj('a')]))

    def test_assert_exception(self):
        utils.assert_exception(True, Exception('message'))
        with self.assertRaisesRegex(Exception, 'message'):
            utils.assert_exception(False, Exception('message'))

    def test_none_sort(self):
        self.assertEqual(utils.none_comparator(None, ()), -1)
        self.assertEqual(utils.none_comparator((), None), 1)
        self.assertEqual(utils.none_comparator((), (None,)), -1)
        self.assertEqual(utils.none_comparator((None,), ()), 1)
        self.assertEqual(utils.none_comparator((None,), (None,)), 0)

        self.assertEqual(utils.none_comparator(None, True), -1)
        self.assertEqual(utils.none_comparator(True, None), 1)
        self.assertEqual(utils.none_comparator(None, None), 0)

        Comparator = utils.none_sort_key_gen()
        self.assertTrue(Comparator(None) <= Comparator(None))
        self.assertTrue(Comparator(None) >= Comparator(None))
        self.assertTrue(Comparator(None) < Comparator(()))
        self.assertTrue(Comparator(()) > Comparator(None))
        self.assertTrue(Comparator(None) == Comparator(None))
        self.assertTrue(Comparator(()) == Comparator(()))
        self.assertTrue(Comparator(()) != Comparator(None))

    def test_validate_value(self):
        self.assertTrue(utils.validate_value(True, ValueType.boolean))
        self.assertTrue(utils.validate_value(False, ValueType.boolean))
        self.assertFalse(utils.validate_value(1, ValueType.boolean))
        self.assertFalse(utils.validate_value(1., ValueType.boolean))
        self.assertFalse(utils.validate_value(2, ValueType.boolean))
        self.assertFalse(utils.validate_value(1.1, ValueType.boolean))

        self.assertTrue(utils.validate_value(1, ValueType.integer))
        self.assertFalse(utils.validate_value(1., ValueType.integer))
        self.assertFalse(utils.validate_value(True, ValueType.integer))
        self.assertFalse(utils.validate_value(1.1, ValueType.integer))

        self.assertFalse(utils.validate_value(1, ValueType.float))
        self.assertFalse(utils.validate_value(True, ValueType.float))
        self.assertTrue(utils.validate_value(1., ValueType.float))
        self.assertTrue(utils.validate_value(1.1, ValueType.float))

        self.assertFalse(utils.validate_value(1.1, ValueType.string))
        self.assertTrue(utils.validate_value('1.1', ValueType.string))

        self.assertTrue(utils.validate_value(OntologyTerm(namespace='KISAO', id='KISAO_0000029'), ValueType.kisao_id))
        self.assertFalse(utils.validate_value(OntologyTerm(namespace='KISAO', id='KISAO:0000029'), ValueType.kisao_id))
        self.assertFalse(utils.validate_value('KISAO_0000029', ValueType.kisao_id))

        self.assertTrue(utils.validate_value([], ValueType.list))
        self.assertFalse(utils.validate_value('[]', ValueType.list))

        self.assertTrue(utils.validate_value({}, ValueType.object))
        self.assertFalse(utils.validate_value('{}', ValueType.object))

        self.assertTrue(utils.validate_value(True, ValueType.any))
        self.assertTrue(utils.validate_value(1, ValueType.any))
        self.assertTrue(utils.validate_value(1., ValueType.any))
        self.assertTrue(utils.validate_value('1', ValueType.any))
        self.assertTrue(utils.validate_value({}, ValueType.any))
        self.assertTrue(utils.validate_value([], ValueType.any))

        with self.assertRaises(NotImplementedError):
            utils.validate_value(None, None)

    def test_validate_str_value(self):
        self.assertTrue(utils.validate_str_value('True', ValueType.boolean))
        self.assertTrue(utils.validate_str_value('False', ValueType.boolean))
        self.assertTrue(utils.validate_str_value('1', ValueType.boolean))
        self.assertFalse(utils.validate_str_value('1.', ValueType.boolean))
        self.assertFalse(utils.validate_str_value('2', ValueType.boolean))
        self.assertFalse(utils.validate_str_value('1.1', ValueType.boolean))

        self.assertTrue(utils.validate_str_value('1', ValueType.integer))
        self.assertFalse(utils.validate_str_value('1.', ValueType.integer))
        self.assertFalse(utils.validate_str_value('True', ValueType.integer))
        self.assertFalse(utils.validate_str_value('1.1', ValueType.integer))

        self.assertTrue(utils.validate_str_value('1', ValueType.float))
        self.assertFalse(utils.validate_str_value('True', ValueType.float))
        self.assertTrue(utils.validate_str_value('1.', ValueType.float))
        self.assertTrue(utils.validate_str_value('1.1', ValueType.float))

        self.assertTrue(utils.validate_str_value('1.1', ValueType.string))

        self.assertTrue(utils.validate_str_value('KISAO_0000029', ValueType.kisao_id))
        self.assertFalse(utils.validate_str_value('KISAO:0000029', ValueType.kisao_id))

        self.assertTrue(utils.validate_str_value('[]', ValueType.list))
        self.assertFalse(utils.validate_str_value('{}', ValueType.list))
        self.assertFalse(utils.validate_str_value('[', ValueType.list))

        self.assertTrue(utils.validate_str_value('{}', ValueType.object))
        self.assertFalse(utils.validate_str_value('[]', ValueType.object))
        self.assertFalse(utils.validate_str_value('{', ValueType.object))

        self.assertTrue(utils.validate_str_value('true', ValueType.any))
        self.assertTrue(utils.validate_str_value('1', ValueType.any))
        self.assertTrue(utils.validate_str_value('1.0', ValueType.any))
        self.assertTrue(utils.validate_str_value('{}', ValueType.any))
        self.assertTrue(utils.validate_str_value('[]', ValueType.any))
        self.assertFalse(utils.validate_str_value('True', ValueType.any))
        self.assertFalse(utils.validate_str_value('1.', ValueType.any))

        with self.assertRaises(NotImplementedError):
            utils.validate_str_value(None, None)

    def test_format_value(self):
        self.assertEqual(utils.format_value(True, ValueType.boolean), 'true')
        self.assertEqual(utils.format_value(False, ValueType.boolean), 'false')

        self.assertEqual(utils.format_value(1, ValueType.integer), '1')

        self.assertEqual(utils.format_value(1., ValueType.float), '1.0')
        self.assertEqual(utils.format_value(1.1, ValueType.float), '1.1')

        self.assertEqual(utils.format_value('1.1', ValueType.string), '1.1')

        self.assertEqual(utils.format_value(OntologyTerm(namespace='KISAO', id='KISAO_0000029'), ValueType.kisao_id), 'KISAO_0000029')

        self.assertEqual(utils.format_value([1, 2], ValueType.list), '[1, 2]')

        self.assertEqual(utils.format_value({"a": 1}, ValueType.object), '{"a": 1}')

        self.assertEqual(utils.format_value(True, ValueType.any), 'true')
        self.assertEqual(utils.format_value(1, ValueType.any), '1')
        self.assertEqual(utils.format_value(1., ValueType.any), '1.0')
        self.assertEqual(utils.format_value('1', ValueType.any), '"1"')
        self.assertEqual(utils.format_value({"a": 1}, ValueType.any), '{"a": 1}')
        self.assertEqual(utils.format_value([1, 2], ValueType.any), "[1, 2]")

        with self.assertRaises(NotImplementedError):
            utils.format_value(None, None)

    def test_parse_value(self):
        self.assertEqual(utils.parse_value('True', ValueType.boolean), True)
        self.assertEqual(utils.parse_value('False', ValueType.boolean), False)
        self.assertEqual(utils.parse_value('1', ValueType.boolean), True)

        self.assertEqual(utils.parse_value('1', ValueType.integer), 1)

        self.assertEqual(utils.parse_value('1', ValueType.float), 1.)
        self.assertEqual(utils.parse_value('1.', ValueType.float), 1.)
        self.assertEqual(utils.parse_value('1.1', ValueType.float), 1.1)

        self.assertEqual(utils.parse_value('1.1', ValueType.string), '1.1')

        self.assertTrue(utils.parse_value('KISAO_0000029', ValueType.kisao_id).is_equal(
            OntologyTerm(
                namespace='KISAO',
                id='KISAO_0000029',
                url=('https://www.ebi.ac.uk/ols/ontologies/kisao/terms?iri='
                     'http%3A%2F%2Fwww.biomodels.net%2Fkisao%2FKISAO%23'
                     'KISAO_0000029'),
            ),
        ))

        self.assertEqual(utils.parse_value('[0, "a"]', ValueType.list), [0, 'a'])

        self.assertEqual(utils.parse_value('{"a": 1, "b": 2}', ValueType.object), {'a': 1, 'b': 2})

        self.assertEqual(utils.parse_value('true', ValueType.any), True)
        self.assertEqual(utils.parse_value('1', ValueType.any), 1)
        self.assertEqual(utils.parse_value('1.0', ValueType.any), 1.)
        self.assertEqual(utils.parse_value('{"a": 1, "b": 2}', ValueType.any), {'a': 1, 'b': 2})
        self.assertEqual(utils.parse_value('[0, "a"]', ValueType.any), [0, 'a'])

        with self.assertRaises(NotImplementedError):
            utils.parse_value(None, None)

    def test_roundtrip_value(self):
        self.assertEqual(utils.parse_value(utils.format_value(True, ValueType.boolean), ValueType.boolean), True)
        self.assertEqual(utils.parse_value(utils.format_value(False, ValueType.boolean), ValueType.boolean), False)

        self.assertEqual(utils.parse_value(utils.format_value(1, ValueType.integer), ValueType.integer), 1)

        self.assertEqual(utils.parse_value(utils.format_value(1., ValueType.float), ValueType.float), 1.0)
        self.assertEqual(utils.parse_value(utils.format_value(1.1, ValueType.float), ValueType.float), 1.1)

        self.assertEqual(utils.parse_value(utils.format_value('1.1', ValueType.string), ValueType.string), '1.1')

        self.assertTrue(utils.parse_value(utils.format_value(
            OntologyTerm(namespace='KISAO', id='KISAO_0000029'), ValueType.kisao_id), ValueType.kisao_id).is_equal(
            OntologyTerm(
                namespace='KISAO',
                id='KISAO_0000029',
                url=('https://www.ebi.ac.uk/ols/ontologies/kisao/terms?iri='
                     'http%3A%2F%2Fwww.biomodels.net%2Fkisao%2FKISAO%23'
                     'KISAO_0000029'))))

        self.assertEqual(utils.parse_value(utils.format_value([1, 2], ValueType.list), ValueType.list), [1, 2])

        self.assertEqual(utils.parse_value(utils.format_value({"a": 1}, ValueType.object), ValueType.object), {"a": 1})

        self.assertEqual(utils.parse_value(utils.format_value(True, ValueType.any), ValueType.any), True)
        self.assertEqual(utils.parse_value(utils.format_value(1, ValueType.any), ValueType.any), 1)
        self.assertEqual(utils.parse_value(utils.format_value(1., ValueType.any), ValueType.any), 1.0)
        self.assertEqual(utils.parse_value(utils.format_value('1', ValueType.any), ValueType.any), '1')
        self.assertEqual(utils.parse_value(utils.format_value({"a": 1}, ValueType.any), ValueType.any), {"a": 1})
        self.assertEqual(utils.parse_value(utils.format_value([1, 2], ValueType.any), ValueType.any), [1, 2])

    def test_roundtrip_value_2(self):
        self.assertEqual(utils.format_value(utils.parse_value('true', ValueType.boolean), ValueType.boolean), 'true')
        self.assertEqual(utils.format_value(utils.parse_value('false', ValueType.boolean), ValueType.boolean), 'false')

        self.assertEqual(utils.format_value(utils.parse_value('1', ValueType.integer), ValueType.integer), '1')

        self.assertEqual(utils.format_value(utils.parse_value('1.0', ValueType.float), ValueType.float), '1.0')
        self.assertEqual(utils.format_value(utils.parse_value('1.1', ValueType.float), ValueType.float), '1.1')

        self.assertEqual(utils.format_value(utils.parse_value('1.1', ValueType.string), ValueType.string), '1.1')

        self.assertEqual(utils.format_value(utils.parse_value('KISAO_0000029', ValueType.kisao_id), ValueType.kisao_id), 'KISAO_0000029')

        self.assertEqual(utils.format_value(utils.parse_value('[1, 2]', ValueType.list), ValueType.list), '[1, 2]')

        self.assertEqual(utils.format_value(utils.parse_value('{"a": 1}', ValueType.object), ValueType.object), '{"a": 1}')

        self.assertEqual(utils.format_value(utils.parse_value('true', ValueType.any), ValueType.any), 'true')
        self.assertEqual(utils.format_value(utils.parse_value('1', ValueType.any), ValueType.any), '1')
        self.assertEqual(utils.format_value(utils.parse_value('1.0', ValueType.any), ValueType.any), '1.0')
        self.assertEqual(utils.format_value(utils.parse_value('1', ValueType.any), ValueType.any), '1')
        self.assertEqual(utils.format_value(utils.parse_value('{"a": 1}', ValueType.any), ValueType.any), '{"a": 1}')
        self.assertEqual(utils.format_value(utils.parse_value('[1, 2]', ValueType.any), ValueType.any), '[1, 2]')

    def test_patch_dict(self):
        dictionary = {
            'id': 'simulator',
            'name': 'simulator',
            'version': 'x1',
            'image': {
                'url': 'y1',
                'format': {
                    'namespace': 'EDAM',
                    'id': 'format_xxxx',
                },
            },
            'algorithms': [
                {
                    'kisaoId': {
                        'namespace': 'KISAO',
                        'id': 'KISAO_0000029',
                    },
                },
                {
                    'kisaoId': {
                        'namespace': 'KISAO',
                        'id': 'KISAO_0000030',
                    },
                },
                {
                    'kisaoId': {
                        'namespace': 'KISAO',
                        'id': 'KISAO_0000031',
                    },
                },
            ],
            'authors': ['A', 'B', 'C'],
        }

        patch = {
            'version': 'x2',
            'image': {
                'url': 'y2',
                'digest': 'z2',
            },
            'algorithms': {
                1: {
                    'kisaoId': {
                        'id': 'KISAO_XXXXXXX'
                    }
                },
                4: {
                    'kisaoId': {
                        'id': 'KISAO_YYYYYYY'
                    }
                }
            },
            'authors': ['A', 'B', 'C', 'D'],
        }

        expected_dictionary = copy.deepcopy(dictionary)
        expected_dictionary['version'] = 'x2'
        expected_dictionary['image']['url'] = 'y2'
        expected_dictionary['image']['digest'] = 'z2'
        expected_dictionary['algorithms'][1]['kisaoId']['id'] = 'KISAO_XXXXXXX'
        expected_dictionary['algorithms'].append(None)
        expected_dictionary['algorithms'].append({
            'kisaoId': {
                'id': 'KISAO_YYYYYYY'
            }
        })
        expected_dictionary['authors'] = ['A', 'B', 'C', 'D']

        utils.patch_dict(dictionary, patch)

        print(dictionary['algorithms'])
        self.assertEqual(dictionary, expected_dictionary)

    def test_flatten_nested_list_of_strings(self):
        self.assertEqual(
            utils.flatten_nested_list_of_strings([['A'], ['B'], ['C']], prefix='- ', indent='  '),
            '\n'.join([
                '- A',
                '- B',
                '- C',
            ])
        )

        self.assertEqual(
            utils.flatten_nested_list_of_strings([
                ['A'],
                ['B',
                    [
                        ['1'],
                        ['2'],
                        ['3'],
                    ],
                 ],
                ['C']
            ], prefix='- ', indent='  '),
            '\n'.join([
                '- A',
                '- B',
                '  - 1',
                '  - 2',
                '  - 3',
                '- C',
            ])
        )

        self.assertEqual(
            utils.flatten_nested_list_of_strings([
                ['A'],
                ['B',
                    [
                        ['1'],
                        ['2\n3',
                            [
                                ['i'],
                                ['ii\niii'],
                            ],
                         ],
                        ['4'],
                    ],
                 ],
                ['C']
            ], prefix='- ', indent='  '),
            '\n'.join([
                '- A',
                '- B',
                '  - 1',
                '  - 2',
                '    3',
                '    - i',
                '    - ii',
                '      iii',
                '  - 4',
                '- C',
            ])
        )

    def test_raise_errors_warnings(self):
        with self.assertRaisesRegex(ValueError, 'Big error'):
            utils.raise_errors_warnings([['Big error']])

        with self.assertRaisesRegex(ValueError, re.compile('Massive\n  - Big error', re.MULTILINE)):
            with self.assertWarnsRegex(BioSimulatorsWarning, re.compile('Problem\n  - Big warning', re.MULTILINE)):
                utils.raise_errors_warnings([['Big error']], [['Big warning']], error_summary='Massive', warning_summary='Problem')
