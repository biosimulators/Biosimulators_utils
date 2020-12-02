import types

__all__ = ['are_lists_equal']


def are_lists_equal(a, b, sort_key=None):
    """ Determine if two lists are equal, optionally up to the order of the elements

    Args:
        a (:obj:`list`): first list
        b (:obj:`list`): second list
        sort_key (:obj:`types.FunctionType`): function to sort the lists

    Returns:
        :obj:`bool`: :obj:`True`, if lists are equal
    """
    if len(a) != len(b):
        return False

    if sort_key:
        a = sorted(a, key=sort_key)
        b = sorted(b, key=sort_key)

    for a_el, b_el in zip(a, b):
        if not a_el.is_equal(b_el):
            return False

    return True
