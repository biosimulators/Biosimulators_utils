""" Utilities for working with XML documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-13
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import copy
import lxml.etree
import re

__all__ = [
    'get_namespaces_for_xml_doc',
    'get_namespaces_for_xml_element',
    'get_attributes_of_xpaths',
    'validate_xpaths_ref_to_unique_objects',
    'eval_xpath',
    'get_namespaces_with_prefixes',
]


def get_namespaces_for_xml_doc(element_tree):
    """ Get the namespaces used by an XML document

    Args:
        et (:obj:`etree._ElementTree`)

    Returns:
        :obj:`dict`: dictionary that maps the id of each namespace to its URI
    """
    root = element_tree.getroot()
    return get_namespaces_for_xml_element(root)


def get_namespaces_for_xml_element(element_tree):
    """ Get the namespaces used by an XML document

    Args:
        et (:obj:`etree._ElementTree`)

    Returns:
        :obj:`dict`: dictionary that maps the id of each namespace to its URI
    """
    namespaces = copy.copy(element_tree.nsmap)
    if None in namespaces:
        namespaces.pop(None)
        match = re.match(r'^{(.*?)}(.*?)$', element_tree.tag)
        if match:
            namespaces[match.group(2)] = match.group(1)

    nodes_to_check = [(element_tree, element_tree.nsmap)]
    while nodes_to_check:
        node, parent_namespaces = nodes_to_check.pop()

        node_namespaces = copy.copy(node.nsmap)
        for prefix, uri in parent_namespaces.items():
            if node_namespaces.get(prefix, None) == uri:
                node_namespaces.pop(prefix)

        if None in node_namespaces:
            node_namespaces.pop(None)
            match = re.match(r'^{(.*?)}(.*?)$', node.tag)
            if match:
                node_namespaces[match.group(2)] = match.group(1)

        for prefix, uri in node_namespaces.items():
            if prefix in namespaces and namespaces[prefix] != uri:
                msg = 'Prefixes must be used consistently throughout the XML document. Prefix `{}` is not used consistently.'.format(prefix)
                raise ValueError(msg)
            namespaces[prefix] = uri

        for child in node.getchildren():
            nodes_to_check.append((child, node.nsmap))

    return namespaces


def get_attributes_of_xpaths(filename, x_paths, namespaces, attr='id'):
    """ Determine the values of the attributes of the objects that match each XPath

    Args:
        filename (:obj:`str`): path to XML file
        x_paths (:obj:`list` of `str`): XPaths
        namespaces (:obj:`dict`): dictionary that maps the prefixes of namespaces to their URIs
        attr (:obj:`str` or :obj:`dict`, optional): attribute to get values of

    Returns:
        :obj:`dict` of :obj:`str` to :obj:`list` of :obj:`str`: dictionary that maps each XPath to the
            values of the attribute of the objects in the XML file that match the XPath
    """
    # read XML file
    etree = lxml.etree.parse(filename)

    # get namespaces
    if isinstance(attr, dict):
        attr = '{{{}}}{}'.format(attr['namespace']['uri'], attr['name'])

    # determine the values of the attributes of the objects that match each XPath
    x_path_attrs = {}
    for x_path in x_paths:
        try:
            objects = etree.xpath(x_path, namespaces=get_namespaces_with_prefixes(namespaces))

            x_path_attrs[x_path] = [obj.attrib.get(attr, None) for obj in objects]
        except Exception:
            x_path_attrs[x_path] = []

    # return the values of the attributes of the objects that match each XPath
    return x_path_attrs


def validate_xpaths_ref_to_unique_objects(filename, x_paths, namespaces, attr='id'):
    """ Validate that each of a list of XPaths matches a single object in an XML file.

    Args:
        filename (:obj:`str`): path to XML file
        x_paths (:obj:`list` of `str`): XPaths
        namespaces (:obj:`dict`): dictionary that maps the prefixes of namespaces to their URIs
        attr (:obj:`str` or :obj:`dict`, optional): attribute to get values of

    Returns:
        :obj:`dict` of :obj:`str` to :obj:`str`: dictionary that maps each XPath to the
            value of the attribute of the object in the XML file that matches the XPath

    Raises:
        :obj:`ValueError`: if one or more XPaths matches 0 or multiple objects
    """
    x_path_attr_vals = get_attributes_of_xpaths(filename, x_paths, namespaces, attr=attr)

    errors = []

    no_matches = sorted([x_path for x_path, attr_vals in x_path_attr_vals.items() if len(attr_vals) == 0])
    if no_matches:
        errors.append('XPaths must reference unique objects. The following XPaths do not match any objects:\n  - {}'.format(
            '\n  - '.join(no_matches)))

    multiple_matches = sorted([x_path for x_path, attr_vals in x_path_attr_vals.items() if len(attr_vals) > 1])
    if multiple_matches:
        errors.append('XPaths must reference unique objects. The following XPaths match multiple objects:\n  - {}'.format(
            '\n  - '.join(multiple_matches)))

    if errors:
        raise ValueError('\n\n'.join(errors))

    return {key: vals[0] for key, vals in x_path_attr_vals.items()}


def eval_xpath(element, xpath, namespaces):
    """ Get the object(s) at an XPath

    Args:
        element (:obj:`etree._ElementTree`): element tree
        xpath (:obj:`str`): XPath
        namespaces (:obj:`dict`): dictionary that maps the prefixes of namespaces to their URIs

    Returns:
        :obj:`list` of :obj:`etree._ElementTree`: object(s) at the XPath
    """
    try:
        return element.xpath(xpath, namespaces=get_namespaces_with_prefixes(namespaces))
    except lxml.etree.XPathEvalError as exception:
        if namespaces:
            msg = 'XPath `{}` is invalid with these namespaces:\n  {}\n\n  {}'.format(
                xpath,
                '\n  '.join(' - {}: {}'.format(prefix, uri) for prefix, uri in namespaces.items()),
                exception.args[0].replace('\n', '\n  ')),
        else:
            msg = 'XPath `{}` is invalid without namespaces:\n\n  {}'.format(
                xpath, exception.args[0].replace('\n', '\n  ')),

        exception.args = (msg)
        raise


def get_namespaces_with_prefixes(namespaces):
    """ Get a dictionary of namespaces less namespaces that have no prefix

    Args:
        namespaces (:obj:`dict`): dictionary that maps prefixes of namespaces their URIs

    Returns:
        :obj:`dict`: dictionary that maps prefixes of namespaces their URIs
    """
    if None in namespaces:
        namespaces = dict(namespaces)
        namespaces.pop(None)
    return namespaces
