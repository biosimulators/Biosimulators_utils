""" Utilities for working with SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..report.data_model import DataGeneratorVariableResults  # noqa: F401
from ..warnings import warn
from .data_model import (SedDocument, Model, ModelChange, ModelAttributeChange, AddElementModelChange,  # noqa: F401
                         ReplaceElementModelChange, RemoveElementModelChange, ComputeModelChange,
                         Task, Report, Plot2D, Plot3D,
                         DataGenerator, DataGeneratorVariable, MATHEMATICAL_FUNCTIONS)
from .warnings import InconsistentVariableShapesWarning
from lxml import etree
import copy
import evalidate
import io
import math
import numpy
import os
import re
import requests
import tempfile

__all__ = [
    'append_all_nested_children_to_doc',
    'resolve_model',
    'apply_changes_to_xml_model',
    'remove_model_changes',
    'remove_algorithm_parameter_changes',
    'replace_complex_data_generators_with_generators_for_individual_variables',
    'remove_plots',
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


BIOMODELS_DOWNLOAD_ENDPOINT = 'https://www.ebi.ac.uk/biomodels/model/download/{}?filename={}_url.xml'


def resolve_model(model, sed_doc, working_dir):
    """ Resolve the source of a model and return a temporary file with the content of the source

    Args:
        model (:obj:`Model`): model whose ``source`` is one of the following

            * A path to a file
            * A URL
            * A MIRIAM URN for an entry in the BioModelsl database (e.g., ``urn:miriam:biomodels.db:BIOMD0000000012``)
            * A reference to another model, using the ``id`` of the other model (e.g., ``#other-model-id``).
              In this case, the model also inherits changes from the parent model.

        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

    Returns:
        :obj:`bool`: whether the model source is a temporary file obtained from an external source
    """
    source = model.source

    if source.lower().startswith('urn:'):
        if source.lower().startswith('urn:miriam:biomodels.db:'):
            biomodels_id = source.lower().replace('urn:miriam:biomodels.db:', '')
            url = BIOMODELS_DOWNLOAD_ENDPOINT.format(biomodels_id, biomodels_id)
            response = requests.get(url)
            try:
                response.raise_for_status()
            except Exception:
                raise ValueError('Model `{}` could not be downloaded from BioModels.'.format(biomodels_id))

            temp_file, model.source = tempfile.mkstemp()
            os.close(temp_file)
            with open(model.source, 'wb') as file:
                file.write(response.content)
        else:
            raise NotImplementedError('URN model source `{}` could be resolved.'.format(source))

        return True

    elif re.match(r'^http(s)?://', source, re.IGNORECASE):
        response = requests.get(source)
        try:
            response.raise_for_status()
        except Exception:
            raise ValueError('Model could not be downloaded from `{}`.'.format(source))

        temp_file, model.source = tempfile.mkstemp()
        os.close(temp_file)
        with open(model.source, 'wb') as file:
            file.write(response.content)

        return True

    elif source.startswith('#'):
        other_model_id = source[1:]
        other_model = next((m for m in sed_doc.models if m.id == other_model_id), None)
        if other_model is None:
            raise ValueError('Relative model source `{}` does not exist.'.format(source))

        model.source = other_model.source
        model.changes = other_model.changes + model.changes
        return resolve_model(model, sed_doc, working_dir)

    else:
        if os.path.isabs(source):
            model.source = source
        else:
            model.source = os.path.join(working_dir, source)

        if not os.path.isfile(model.source):
            raise FileNotFoundError('Model source file `{}` does not exist.'.format(source))

        return False


def apply_changes_to_xml_model(changes, in_model_filename, out_model_filename, pretty_print=False):
    """ Modify an XML-encoded model according to the model attribute changes in a simulation

    Args:
        changes (:obj:`list` of :obj:`ModelChange`): changes
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
        if isinstance(change, ModelAttributeChange):

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

        elif isinstance(change, AddElementModelChange):
            parent = et.xpath(change.target, namespaces=namespaces)
            if len(parent) != 1:
                raise ValueError('xpath {} must match a single object in {}'.format(change.target, in_model_filename))
            parent = parent[0]

            try:
                new_element = etree.parse(io.StringIO(change.new_element)).getroot()
            except etree.XMLSyntaxError as exception:
                raise ValueError('`{}` is not valid XML. {}'.format(change.new_element, str(exception)))
            parent.append(new_element)

        elif isinstance(change, ReplaceElementModelChange):
            old_element = et.xpath(change.target, namespaces=namespaces)
            if len(old_element) != 1:
                raise ValueError('xpath {} must match a single object in {}'.format(change.target, in_model_filename))
            old_element = old_element[0]
            try:
                new_element = etree.parse(io.StringIO(change.new_element)).getroot()
            except etree.XMLSyntaxError as exception:
                raise ValueError('`{}` is not valid XML. {}'.format(change.new_element, str(exception)))
            parent = old_element.getparent()

            parent.remove(old_element)
            parent.append(new_element)

        elif isinstance(change, RemoveElementModelChange):
            elements = et.xpath(change.target, namespaces=namespaces)
            for element in elements:
                parent = element.getparent()
                parent.remove(element)

        elif isinstance(change, ComputeModelChange):
            pass

        else:
            raise NotImplementedError('Change{} of type {} is not supported'.format(
                ' ' + change.name if change.name else '', change.__class__.__name__))

    # remove changes from list of changes
    changes.clear()

    # write model
    et.write(out_model_filename, xml_declaration=True, encoding="utf-8", standalone=False, pretty_print=pretty_print)


def calc_data_generator_results(data_generator, variable_results):
    """ Calculate the results of a data generator from the results of its variables

    Args:
        data_generator (:obj:`DataGenerator`): data generator
        variable_results (:obj:`DataGeneratorVariableResults`): results for the variables of the data generator

    Returns:
        :obj:`numpy.ndarray`: result of data generator
    """
    var_shapes = set()
    max_shape = []
    for var in data_generator.variables:
        var_res = variable_results[var.id]
        var_shape = var_res.shape
        if not var_shape and var_res.size:
            var_shape = (1,)
        var_shapes.add(var_shape)

        max_shape = max_shape + [1 if max_shape else 0] * (var_res.ndim - len(max_shape))
        for i_dim in range(var_res.ndim):
            max_shape[i_dim] = max(max_shape[i_dim], var_res.shape[i_dim])

    if len(var_shapes) > 1:
        warn('Variables for data generator {} do not have consistent shapes'.format(data_generator.id),
             InconsistentVariableShapesWarning)

    math_node = evalidate.evalidate(data_generator.math,
                                    addnodes=[
                                        'Eq', 'NotEq', 'Gt', 'Lt', 'GtE', 'LtE',
                                        'Sub', 'Mult', 'Div' 'Pow',
                                        'And', 'Or', 'Not',
                                        'BitAnd', 'BitOr', 'BitXor',
                                        'Call',
                                    ],
                                    funcs=MATHEMATICAL_FUNCTIONS.keys())
    compiled_math = compile(math_node, '<data_generator.math>', 'eval')

    workspace = {
        'true': True,
        'false': False,
        'notanumber': math.nan,
        'pi': math.pi,
        'infinity': math.inf,
        'exponentiale': math.e,
    }
    for param in data_generator.parameters:
        workspace[param.id] = param.value

    if not var_shapes:
        try:
            value = eval(compiled_math, MATHEMATICAL_FUNCTIONS, workspace)
        except Exception as exception:
            raise ValueError('Expression for data generator {} could not be evaluated:\n  {}'.format(
                data_generator.id, str(exception)))
        result = numpy.array(value)

    else:
        padded_var_shapes = []
        for var in data_generator.variables:
            var_res = variable_results[var.id]
            padded_var_shapes.append(
                list(var_res.shape)
                + [1 if var_res.size else 0] * (len(max_shape) - var_res.ndim)
            )

        result = numpy.full(max_shape, numpy.nan)
        n_dims = result.ndim
        for i_el in range(result.size):
            el_indices = numpy.unravel_index(i_el, result.shape)

            vars_available = True
            for var, padded_shape in zip(data_generator.variables, padded_var_shapes):
                var_res = variable_results[var.id]
                if var_res.ndim == 0:
                    if i_el == 0 and var_res.size:
                        workspace[var.id] = var_res.tolist()
                    else:
                        vars_available = False
                        break

                else:
                    for x, y in zip(padded_shape, el_indices):
                        if (y + 1) > x:
                            vars_available = False
                            break
                    if not vars_available:
                        break

                    workspace[var.id] = var_res[el_indices[0:var_res.ndim]]

            if not vars_available:
                continue

            try:
                result_el = eval(compiled_math, MATHEMATICAL_FUNCTIONS, workspace)
            except Exception as exception:
                raise ValueError('Expression for data generator {} could not be evaluated:\n  {}'.format(
                    data_generator.id, str(exception)))

            if n_dims == 0:
                result = numpy.array(result_el)
            else:
                result.flat[i_el] = result_el

    return result


def remove_model_changes(sed_doc):
    """ Remove model changes from a SED document

    Args:
        sed_doc (:obj:`SedDocument`): SED document
    """
    for model in sed_doc.models:
        model.changes = []


def remove_algorithm_parameter_changes(sed_doc):
    """ Remove algorithm parameter changes from a SED document

    Args:
        sed_doc (:obj:`SedDocument`): SED document
    """
    for simulation in sed_doc.simulations:
        simulation.algorithm.changes = []


def replace_complex_data_generators_with_generators_for_individual_variables(sed_doc):
    """ Remove model changes from a SED document

    Args:
        sed_doc (:obj:`SedDocument`): SED document
    """
    data_gen_replacements = {}

    for original_data_gen in list(sed_doc.data_generators):
        if len(original_data_gen.parameters) + len(original_data_gen.variables) > 1:
            sed_doc.data_generators.remove(original_data_gen)
            data_gen_replacements[original_data_gen] = []

            for var in original_data_gen.variables:
                new_data_gen = DataGenerator(id='__single_var_gen__' + var.id, variables=[var], math=var.id)
                data_gen_replacements[original_data_gen].append(new_data_gen)
                sed_doc.data_generators.append(new_data_gen)

    for output in sed_doc.outputs:
        if isinstance(output, Report):
            els = 'data_sets'
            props = ['data_generator']

        elif isinstance(output, Plot2D):
            els = 'curves'
            props = ['x_data_generator', 'y_data_generator']

        elif isinstance(output, Plot3D):
            els = 'surfaces'
            props = ['x_data_generator', 'y_data_generator', 'z_data_generator']

        old_els = getattr(output, els)

        new_els = []
        i_single_var_output_el = 0
        for el in old_els:
            replacement_els = [el]
            for prop in props:
                new_replacement_els = []
                for el2 in replacement_els:
                    original_data_gen = getattr(el2, prop)
                    for replaced_data_gen in data_gen_replacements.get(original_data_gen, [original_data_gen]):
                        i_single_var_output_el += 1
                        el3 = copy.copy(el2)
                        el3.id = '__single_var_output_el__' + str(i_single_var_output_el)
                        el3.label = el3.id
                        setattr(el3, prop, replaced_data_gen)
                        new_replacement_els.append(el3)
                replacement_els = new_replacement_els
            new_els.extend(replacement_els)

        setattr(output, els, new_els)


def remove_plots(sed_doc):
    """ Remove plots from a SED document

    Args:
        sed_doc (:obj:`SedDocument`): SED document
    """
    for output in list(sed_doc.outputs):
        if isinstance(output, (Plot2D, Plot3D)):
            sed_doc.outputs.remove(output)
