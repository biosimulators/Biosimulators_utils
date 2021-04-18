""" Miscellaneous utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..data_model import ValueType, OntologyTerm
from ..warnings import warn, BioSimulatorsWarning
import json
import numpy
import re

__all__ = [
    'are_lists_equal', 'none_sorted', 'assert_exception',
    'validate_value', 'validate_str_value', 'format_value', 'parse_value',
    'patch_dict', 'pad_arrays_to_consistent_shapes',
    'flatten_nested_list_of_strings',
    'raise_errors_warnings',
]


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

        return 0  # pragma: no cover

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


def validate_value(val, type):
    """ Determine if a value is a valid instance of type :obj:`type`

    Args:
        val (:obj:`object`): value
        type (:obj:`ValueType`): type

    Returns:
        :obj:`bool`: :obj:`True`, if a value is a valid instance of type :obj:`type`
    """
    if type == ValueType.boolean:
        return isinstance(val, bool)
    if type == ValueType.integer:
        return isinstance(val, int) and not isinstance(val, bool)
    if type == ValueType.float:
        return isinstance(val, float)
    if type == ValueType.string:
        return isinstance(val, str)
    if type == ValueType.kisao_id:
        return isinstance(val, OntologyTerm) and val.namespace == 'KISAO' and re.match(r'^KISAO_\d{7}$', val.id) is not None
    if type == ValueType.list:
        return isinstance(val, list)
    if type == ValueType.object:
        return isinstance(val, dict)
    if type == ValueType.any:
        return True
    raise NotImplementedError('Type {} is not supported'.format(type))


def validate_str_value(str_val, type):
    """ Determine if a value is a valid string representation of type :obj:`type`

    Args:
        str_val (:obj:`str`): string representation of a value
        type (:obj:`ValueType`): type

    Returns:
        :obj:`bool`: :obj:`True`, if a value is a valid string representation of type :obj:`type`
    """
    if type == ValueType.boolean:
        return str_val.lower() in ['true', 'false', '0', '1']
    if type == ValueType.integer:
        try:
            int(str_val)
            return True
        except ValueError:
            return False
    if type == ValueType.float:
        try:
            float(str_val)
            return True
        except ValueError:
            return False
    if type == ValueType.string:
        return True
    if type == ValueType.kisao_id:
        return re.match(r'^KISAO_\d{7}$', str_val)
    if type == ValueType.list:
        try:
            return isinstance(json.loads(str_val), list)
        except json.JSONDecodeError:
            return False
    if type == ValueType.object:
        try:
            return isinstance(json.loads(str_val), dict)
        except json.JSONDecodeError:
            return False
    if type == ValueType.any:
        try:
            json.loads(str_val)
            return True
        except json.JSONDecodeError:
            return False
    raise NotImplementedError('Type {} is not supported'.format(type))


def format_value(val, type):
    """ Format a value as a string (e.g., for use with an attribute of an XML object)

    Args:
        val (:obj:`object`): value
        type (:obj:`ValueType`): type

    Returns:
        :obj:`str`: string representation of the value
    """
    if type == ValueType.boolean:
        return str(val).lower()
    if type == ValueType.integer or type == ValueType.float:
        return str(val)
    if type == ValueType.string:
        return val
    if type == ValueType.kisao_id:
        return val.id
    if type == ValueType.list or type == ValueType.object or type == ValueType.any:
        return json.dumps(val)
    raise NotImplementedError('Type {} is not supported'.format(type))


def parse_value(str_val, type):
    """ Parse the string representation of a value (e.g., for use with an attribute of an XML object)

    Args:
        str_val (:obj:`str`): string representation of the value
        type (:obj:`ValueType`): type

    Returns:
        :obj:`object`: Python representation of the value
    """
    if type == ValueType.boolean:
        return str_val.lower() == 'true' or str_val.lower() == '1'
    if type == ValueType.integer:
        return int(str_val)
    if type == ValueType.float:
        return float(str_val)
    if type == ValueType.string:
        return str_val
    if type == ValueType.kisao_id:
        return OntologyTerm(
            namespace='KISAO',
            id=str_val,
            url='https://www.ebi.ac.uk/ols/ontologies/kisao/terms?iri=http%3A%2F%2Fwww.biomodels.net%2Fkisao%2FKISAO%23' + str_val,
        )
    if type == ValueType.list or type == ValueType.object or type == ValueType.any:
        return json.loads(str_val)
    raise NotImplementedError('Type {} is not supported'.format(type))


def patch_dict(dictionary, patch):
    """ Recursively patch the attributes of a dictionary

    Args:
        dictionary (:obj:`dict`): dictionary
        patch (:obj:`dict`): patch
    """
    patch_queue = [(dictionary, patch)]

    while patch_queue:
        props, props_patch = patch_queue.pop()
        for key, new_val in props_patch.items():
            value = props[key]
            if isinstance(value, dict):
                patch_queue.append((props[key], new_val))

            elif isinstance(value, list) and isinstance(new_val, dict):
                patch_queue.append((props[key], new_val))

            else:
                props[key] = new_val


def pad_arrays_to_consistent_shapes(arrays):
    """ Pad a list of NumPy arrays to a consistent shape

    Args:
        arrays (:obj:`list` of :obj:`numpy.ndarray`): list of NumPy arrays

    Returns:
        :obj:`list` of :obj:`numpy.ndarray`: list of padded arrays
    """
    shapes = set()
    for array in arrays:
        if array is not None:
            shape = array.shape
            if not shape and array.size:
                shape = (1,)
            shapes.add(shape)

    if len(shapes) > 1:
        warn('Arrays do not have consistent shapes', UserWarning)

    max_shape = []
    for shape in shapes:
        max_shape = max_shape + [1 if max_shape else 0] * (len(shape) - len(max_shape))
        shape = list(shape) + [1 if shape else 0] * (len(max_shape) - len(shape))
        max_shape = [max(x, y) for x, y in zip(max_shape, shape)]

    padded_arrays = []
    for array in arrays:
        if array is None:
            array = numpy.full(max_shape, numpy.nan)

        shape = tuple(list(array.shape)
                      + [1 if array.size else 0]
                      * (len(max_shape) - array.ndim))
        array = array.astype('float64').reshape(shape)

        pad_width = tuple((0, x - y) for x, y in zip(max_shape, shape))

        if pad_width:
            array = numpy.pad(array,
                              pad_width,
                              mode='constant',
                              constant_values=numpy.nan)

        padded_arrays.append(array)

    return padded_arrays


def flatten_nested_list_of_strings(nested_list, prefix='- ', indent=' ' * 2):
    """ Flatten a nested list of strings

    Args:
        nested_list (nested :obj:`list` of :obj:`str`): nested list of string
        prefix (:obj:`str`, optional): prefix
        indentation (:obj:`str`, optional): indentation

    Returns:
        :obj:`str`: flattened string
    """
    flattened = []
    for item in nested_list:
        flattened.append(prefix + item[0].replace('\n', '\n' + ' ' * len(prefix)))
        if len(item) > 1:
            flattened.append(
                indent
                + flatten_nested_list_of_strings(item[1], prefix=prefix, indent=indent).replace('\n', '\n' + indent)
            )

    return '\n'.join(flattened)


def raise_errors_warnings(errors, warnings=None, error_summary=None, warning_summary=None):
    """ Raises errors and warnings

    Args:
        errors (nested :obj:`list` of :obj:`str`): errors
        warnings (nested :obj:`list` of :obj:`str`): warnings
        error_summary (:obj:`str`, optional): summary of errors
        warning_summary (:obj:`str`, optional): summary of warnings

    Raises:
        :obj:`ValueError`: if errors
    """
    if warnings:
        msg = flatten_nested_list_of_strings(warnings)
        if warning_summary:
            msg = warning_summary + '\n  ' + msg.replace('\n', '\n  ')
        warn(msg, BioSimulatorsWarning)

    if errors:
        msg = flatten_nested_list_of_strings(errors)
        if error_summary:
            msg = error_summary + '\n  ' + msg.replace('\n', '\n  ')
        raise ValueError(msg)
