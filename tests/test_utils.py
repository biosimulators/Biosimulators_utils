from biosimulators_utils import utils
import unittest


class TestCase(unittest.TestCase):
    def test_are_lists_equal(self):
        class Obj(str):
            def is_equal(self, other):
                return self == other

        self.assertTrue(utils.are_lists_equal([Obj('a')], [Obj('a')]))
        self.assertFalse(utils.are_lists_equal([Obj('a')], [Obj('b')]))

        self.assertTrue(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('a'), Obj('b')]))
        self.assertFalse(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('a')]))
        self.assertFalse(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('a'), Obj('c')]))

        self.assertTrue(utils.are_lists_equal([Obj('a'), Obj('b')], [Obj('b'), Obj('a')], sort_key=lambda x: x))
