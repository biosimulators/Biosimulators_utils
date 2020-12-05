import functools

__all__ = ['are_lists_equal', 'none_sorted', 'assert_exception']


def are_lists_equal(a, b):
    """ Determine if two lists are equal, optionally up to the order of the elements

    Args:
        a (:obj:`list`): first list
        b (:obj:`list`): second list

    Returns:
        :obj:`bool`: :obj:`True`, if lists are equal
    """
    if len(a) != len(b):
        return False

    a = none_sorted(a, key=lambda x: x.to_tuple())
    b = none_sorted(b, key=lambda x: x.to_tuple())

    for a_el, b_el in zip(a, b):
        if not a_el.is_equal(b_el):
            return False

    return True


def none_sort_key_gen(key=None):
    class NoneComparator(object):
        def __init__(self, obj):
            if key:
                self.obj = key(obj)
            else:
                self.obj = obj

        def __lt__(self, other):
            return none_comparator(self.obj, other.obj) < 0

        def __gt__(self, other):
            return none_comparator(self.obj, other.obj) > 0

        def __eq__(self, other):
            return none_comparator(self.obj, other.obj) == 0

        def __le__(self, other):
            return none_comparator(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return none_comparator(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return none_comparator(self.obj, other.obj) != 0
    return NoneComparator


def none_comparator(x, y):
    if x == y:
        return 0

    if isinstance(x, tuple) and not isinstance(y, tuple):
        return 1
    if not isinstance(x, tuple) and isinstance(y, tuple):
        return -1
    if isinstance(x, tuple) and isinstance(y, tuple):
        if len(x) < len(y):
            return -1
        if len(x) > len(y):
            return 1

        for x1, y1 in zip(x, y):
            cmp = none_comparator(x1, y1)
            if cmp != 0:
                return cmp

        return 0 # pragma: no cover

    if x is None:
        return -1
    if y is None:
        return 1

    if x < y:
        return -1
    if x > y:
        return 1


def none_sorted(arr, key=None):
    """ Sort an error that contains :obj:`None`

    Args:
        arr (:obj:`list`): array

    Returns:
        :obj:`list`: sorted array
    """
    return sorted(arr, key=none_sort_key_gen(key))


def assert_exception(success, exception):
    """ Raise an error if :obj:`success` is :obj:`False`

    Args:
        success (:obj:`bool`)
        exception (:obj:`Exception`)

    Raises:
        :obj:`Exception`
    """
    if not success:
        raise exception
