""" Utilities for executing tasks in SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import ModelChange, ModelAttributeChange
from lxml import etree
import re


__all__ = [
    'apply_changes_to_xml_model',
]


def apply_changes_to_xml_model(changes, in_model_filename, out_model_filename, pretty_print=True):
    """ Modify an XML-encoded model according to the model attribute changes in a simulation

    Args:
        changes (:obj:`list` of :obj:`ModelAttributeChange`): changes
        in_model_filename (:obj:`str`): path to model
        out_model_filename (:obj:`str`): path to save modified model
        pretty_print (:obj:`bool`, optional): if :obj:`True`, pretty print output
    """
    # read model
    et = etree.parse(in_model_filename)

    # get namespaces
    root = et.getroot()
    namespaces = root.nsmap
    if None in namespaces:
        namespaces.pop(None)
        match = re.match(r'^{(.*?)}(.*?)$', root.tag)
        if match:
            namespaces[match.group(2)] = match.group(1)

    # apply changes
    for change in changes:
        if not isinstance(change, ModelAttributeChange):
            raise NotImplementedError('Change{} of type {} is not supported'.format(
                ' ' + change.name if change.name else '', change.__class__.__name__))

        # get object to change
        obj_xpath, sep, attr = change.target.rpartition('/@')
        if sep != '/@':
            raise ValueError('target {} is not a valid XPATH to an attribute of a model element'.format(change.target))
        objs = et.xpath(obj_xpath, namespaces=namespaces)
        if len(objs) != 1:
            raise ValueError('xpath {} must match a single object in {}'.format(obj_xpath, in_model_filename))
        obj = objs[0]

        # change value
        obj.set(attr, change.new_value)

    # write model
    et.write(out_model_filename, xml_declaration=True, encoding="utf-8", standalone=False, pretty_print=pretty_print)
