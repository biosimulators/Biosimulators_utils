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
