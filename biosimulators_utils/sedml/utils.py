""" Utilities for working with SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import SedDocument, ModelAttributeChange, Task, Report, Plot2D, Plot3D, DataGeneratorVariable  # noqa: F401
from lxml import etree
import copy
import re

__all__ = ['append_all_nested_children_to_doc', 'validate_doc', 'validate_reference', 'apply_changes_to_xml_model']


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
            for dataset in output.datasets:
                if dataset.data_generator:
                    data_generators.add(dataset.data_generator)

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


def validate_doc(doc, validate_semantics=True):
    """ Validate a SED document

    Args:
        doc (:obj:`SedDocument`): SED document
        validate_semantics (:obj:`bool`, optional): if :obj:`True`, check that SED-ML is semantically valid

    Raises:
        :obj:`ValueError`: if document is invalid (e.g., required ids missing or ids not unique)
    """
    # validate that required ids exist and are unique
    for child_type in ('models', 'simulations', 'data_generators', 'tasks', 'outputs'):
        children = getattr(doc, child_type)

        missing_ids = next((True for child in children if not getattr(child, 'id', None)), False)
        if missing_ids:
            raise ValueError('{} must have ids'.format(child_type))

        if validate_semantics:
            repeated_ids = len(set(getattr(child, 'id', None) for child in children)) < len(children)
            if repeated_ids:
                raise ValueError('{} must have unique ids'.format(child_type))

    if validate_semantics:
        # validate the models, simulations, tasks, data generators are children of the SED document
        doc_copy = copy.deepcopy(doc)
        append_all_nested_children_to_doc(doc_copy)

        for child_type in ('models', 'simulations', 'tasks', 'data_generators'):
            if len(getattr(doc, child_type)) != len(getattr(doc_copy, child_type)):
                raise ValueError('{} must be direct children of SED document'.format(child_type))

        # validate that model attribute changes have targets
        for model in doc.models:
            for change in model.changes:
                if isinstance(change, ModelAttributeChange):
                    if not change.target:
                        raise ValueError('Model change attributes must define a target')

        for sim in doc.simulations:
            if sim.algorithm:
                if not sim.algorithm.kisao_id or not re.match(r'^KISAO_\d{7}$', sim.algorithm.kisao_id):
                    raise ValueError('Algorithm of simulation {} has an invalid KiSAO id: {}'.format(sim.id, sim.algorithm.kisao_id))
                for change in sim.algorithm.changes:
                    if not change.kisao_id or not re.match(r'^KISAO_\d{7}$', change.kisao_id):
                        raise ValueError('Algorithm of simulation {} has an invalid KiSAO id: {}'.format(sim.id, sim.algorithm.kisao_id))

        for task in doc.tasks:
            if isinstance(task, Task):
                validate_reference(task, 'Task {}'.format(task.id), 'model', 'model')
                validate_reference(task, 'Task {}'.format(task.id), 'simulation', 'simulation')

        for data_gen in doc.data_generators:
            for var in data_gen.variables:
                if not var.id:
                    raise ValueError('Variables must have ids')
                if (not var.target and not var.symbol) or (var.target and var.symbol):
                    raise ValueError('Variables must define a target or symbol')
                validate_reference(var, 'Variable {} of data generator "{}"'.format(var.id, data_gen.id), 'task', 'task')
                validate_reference(var, 'Variable {} of data generator "{}"'.format(var.id, data_gen.id), 'model', 'model')

                if var.model and var.task and var.task.model and var.task.model != var.model:
                    raise ValueError('Model of variable {} of data generator "{}" and model of task must be consistent'.format(
                        var.id, data_gen.id))
            if not data_gen.math:
                raise ValueError('Data generators must have math')

        for output in doc.outputs:
            if isinstance(output, Report):
                for dataset in output.datasets:
                    if not dataset.id:
                        raise ValueError('Datasets must have ids')
                    if not dataset.label:
                        raise ValueError('Datasets must have labels')
                    validate_reference(dataset, 'Dataset {} of report "{}"'.format(
                        dataset.id, output.id), 'data_generator', 'data data generator')

            elif isinstance(output, Plot2D):
                for curve in output.curves:
                    if not curve.id:
                        raise ValueError('Curves must have ids')
                    validate_reference(curve, 'Curve {} of 2D plot "{}"'.format(
                        curve.id, output.id), 'x_data_generator', 'x data data generator')
                    validate_reference(curve, 'Curve {} of 2D plot "{}"'.format(
                        curve.id, output.id), 'y_data_generator', 'y data data generator')

            elif isinstance(output, Plot3D):
                for surface in output.surfaces:
                    if not surface.id:
                        raise ValueError('Surfaces must have ids')
                    validate_reference(surface, 'Surface {} of 3D plot "{}"'.format(
                        surface.id, output.id), 'x_data_generator', 'x data data generator')
                    validate_reference(surface, 'Surface {} of 3D plot "{}"'.format(
                        surface.id, output.id), 'y_data_generator', 'y data data generator')
                    validate_reference(surface, 'Surface {} of 3D plot "{}"'.format(
                        surface.id, output.id), 'z_data_generator', 'z data data generator')


def validate_reference(obj, obj_label, attr_name, attr_label):
    if not getattr(obj, attr_name):
        raise ValueError('{} must have a {}'.format(obj_label, attr_label))


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
