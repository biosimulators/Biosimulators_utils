""" Utilities for working with XML documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import lxml.etree
import re


def get_num_matches_to_xpaths(filename, x_paths):
    """ Determine the number of objects that match each XPath in an XML file.

    Args:
        filename (:obj:`str`): path to XML file
        x_paths (:obj:`list` of `str`): XPaths

    Returns:
        :obj:`dict` of :obj:`str` to :obj:`int`: dictionary that maps each XPath to the
            number of objects in the XML file that match the XPath
    """
    # read XML file
    etree = lxml.etree.parse(filename)

    # get namespaces
    root = etree.getroot()
    namespaces = root.nsmap
    if None in namespaces:
        namespaces.pop(None)
        match = re.match(r'^{(.*?)}(.*?)$', root.tag)
        if match:
            namespaces[match.group(2)] = match.group(1)

    # determine number of objects that match each XPath
    x_path_counts = {}
    for x_path in x_paths:
        x_path_counts[x_path] = len(etree.xpath(x_path, namespaces=namespaces))

    # return number of objects that match each XPath
    return x_path_counts


def validate_xpaths_ref_to_unique_objects(filename, x_paths):
    """ Validate that each of a list of XPaths matches a single object in an XML file.

    Args:
        filename (:obj:`str`): path to XML file
        x_paths (:obj:`list` of `str`): XPaths

    Raises:
        :obj:`ValueError`: if one or more XPaths matches 0 or multiple objects
    """
    x_path_counts = get_num_matches_to_xpaths(filename, x_paths)

    errors = []

    no_matches = sorted([x_path for x_path, count in x_path_counts.items() if count == 0])
    if no_matches:
        errors.append('XPaths must reference unique objects. The following XPaths do not match any objects:\n  - {}'.format(
            '\n  - '.join(no_matches)))

    multiple_matches = sorted([x_path for x_path, count in x_path_counts.items() if count > 1])
    if multiple_matches:
        errors.append('XPaths must reference unique objects. The following XPaths match multiple objects:\n  - {}'.format(
            '\n  - '.join(multiple_matches)))

    if errors:
        raise ValueError('\n\n'.join(errors))
