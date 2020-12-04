__all__ = ['are_lists_equal']


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

    a = sorted(a, key=lambda x: x.to_tuple())
    b = sorted(b, key=lambda x: x.to_tuple())

    for a_el, b_el in zip(a, b):
        if not a_el.is_equal(b_el):
            return False

    return True
