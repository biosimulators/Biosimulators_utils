""" Utilities for working with SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import (SedDocument, ModelAttributeChange, Task, Report, Plot2D, Plot3D,  # noqa: F401
                         DataGeneratorVariable)
from lxml import etree
import re

__all__ = [
    'append_all_nested_children_to_doc',
    'apply_changes_to_xml_model',
]


def append_all_nested_children_to_doc(doc):
    """ Append all nested children to a SED document

    Args:
        doc (:obj:`SedDocument`): SED document
    """
    data_generators = set(doc.data_generators)
    tasks = set(doc.tasks)
    simulations = set(doc.simulations)
    models = set(doc.models)

    for output in doc.outputs:
        if isinstance(output, Report):
            for data_set in output.data_sets:
                if data_set.data_generator:
                    data_generators.add(data_set.data_generator)

        elif isinstance(output, Plot2D):
            for curve in output.curves:
                if curve.x_data_generator:
                    data_generators.add(curve.x_data_generator)
                if curve.y_data_generator:
                    data_generators.add(curve.y_data_generator)

        elif isinstance(output, Plot3D):
            for surface in output.surfaces:
                if surface.x_data_generator:
                    data_generators.add(surface.x_data_generator)
                if surface.y_data_generator:
                    data_generators.add(surface.y_data_generator)
                if surface.z_data_generator:
                    data_generators.add(surface.z_data_generator)

    for data_gen in data_generators:
        for var in data_gen.variables:
            if var.task:
                tasks.add(var.task)
            if var.model:
                models.add(var.model)

    for task in tasks:
        if isinstance(task, Task):
            if task.model:
                models.add(task.model)
            if task.simulation:
                simulations.add(task.simulation)

    doc.models += list(models - set(doc.models))
    doc.simulations += list(simulations - set(doc.simulations))
    doc.tasks += list(tasks - set(doc.tasks))
    doc.data_generators += list(data_generators - set(doc.data_generators))


def get_variables_for_task(doc, task):
    """ Get the variables that a task must record

    Args:
        doc (:obj:`SedDocument`): SED document
        task (:obj:`Task`): task

    Returns:
        :obj:`list` of :obj:`DataGeneratorVariable`: variables that task must record
    """
    variables = set()
    for data_gen in doc.data_generators:
        for var in data_gen.variables:
            if var.task == task:
                variables.add(var)
    return list(variables)


def apply_changes_to_xml_model(changes, in_model_filename, out_model_filename, pretty_print=False):
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
