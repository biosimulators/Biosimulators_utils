from biosimulators_utils.utils import core as utils
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
