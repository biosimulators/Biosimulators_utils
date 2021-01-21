""" Utilities for working with SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..log.data_model import Status
from ..report.data_model import VariableResults, DataGeneratorResults  # noqa: F401
from ..utils.core import pad_arrays_to_consistent_shapes
from ..warnings import warn
from ..xml.utils import get_namespaces_for_xml_doc
from .data_model import (SedDocument, Model, ModelChange, ModelAttributeChange, AddElementModelChange,  # noqa: F401
                         ReplaceElementModelChange, RemoveElementModelChange, ComputeModelChange,
                         Task, Report, Plot2D, Plot3D,
                         DataGenerator, Variable, MATHEMATICAL_FUNCTIONS, RESERVED_MATHEMATICAL_SYMBOLS)
from .warnings import InconsistentVariableShapesWarning
from lxml import etree
import copy
import evalidate
import io
import libsedml  # noqa: F401
import math
import numpy
import os
import re
import requests
import tempfile

__all__ = [
    'append_all_nested_children_to_doc',
    'convert_xml_node_to_string',
    'resolve_model_and_apply_xml_changes',
    'resolve_model',
    'apply_changes_to_xml_model',
    'get_values_of_variable_model_xml_targets_of_model_change',
    'get_value_of_variable_model_xml_targets',
    'calc_compute_model_change_new_value',
    'calc_data_generator_results',
    'calc_data_generators_results',
    'compile_math',
    'eval_math',
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

    for model in doc.models:
        for change in model.changes:
            if isinstance(change, ComputeModelChange):
                for var in change.variables:
                    # tasks not added because `var.task` should be null
                    if var.model:
                        models.add(var.model)

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
            # models not added because `var.model` should be null

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


def add_namespaces_to_xml_node(node, namespaces, include_default=False):
    """ Add namespaces to an XML node

    Args:
        node (:obj:`libsedml.XMLNode`): XML node
        namespaces (:obj:`libsedml.XMLNamespaces`): namespaces for the parent document
        include_default (:obj:`bool`, optional): include the default (SED-ML) namespace
    """
    node_namespaces = node.getNamespaces()

    for i_ns in range(namespaces.getNumNamespaces()):
        uri = namespaces.getURI(i_ns)
        prefix = namespaces.getPrefix(i_ns)

        if prefix == '' and not include_default:
            continue

        i_node_ns_prefix = node_namespaces.getIndexByPrefix(prefix)

        if i_node_ns_prefix == -1:
            node.addNamespace(uri, prefix)


def convert_xml_node_to_string(node):
    """ Generate a string representation of an XML node

    Args:
        node (:obj:`libsedml.XMLNode`): XML node

    Returns:
        :obj:`str`: string representation of the node
    """
    return node.convertXMLNodeToString(node)


def get_variables_for_task(doc, task):
    """ Get the variables that a task must record

    Args:
        doc (:obj:`SedDocument`): SED document
        task (:obj:`Task`): task

    Returns:
        :obj:`list` of :obj:`Variable`: variables that task must record
    """
    variables = set()
    for data_gen in doc.data_generators:
        for var in data_gen.variables:
            if var.task == task:
                variables.add(var)
    return list(variables)


BIOMODELS_DOWNLOAD_ENDPOINT = 'https://www.ebi.ac.uk/biomodels/model/download/{}?filename={}_url.xml'


def resolve_model_and_apply_xml_changes(model, sed_doc, working_dir,
                                        apply_xml_model_changes=True,
                                        save_to_file=True,
                                        pretty_print_modified_xml_models=False):
    """ Resolve the source of a model and, optionally, apply XML changes to the model.

    Args:
        model (:obj:`Model`): model whose ``source`` is one of the following

            * A path to a file
            * A URL
            * A MIRIAM URN for an entry in the BioModelsl database (e.g., ``urn:miriam:biomodels.db:BIOMD0000000012``)
            * A reference to another model, using the ``id`` of the other model (e.g., ``#other-model-id``).
              In this case, the model also inherits changes from the parent model.

        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        save_to_file (:obj:`bool`): whether to save the resolved/modified model to a file
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models

    Returns:
        :obj:`tuple`:

            * :obj:`Model`: modified model
            * :obj:`str`: temporary path to the source of the modified model, if the model needed to be resolved from
              a remote source of modified
            * :obj:`etree._Element`: element tree for the resolved/modified model
    """
    model = copy.deepcopy(model)

    # resolve model
    temp_model_source = resolve_model(model, sed_doc, working_dir)

    # apply changes to model
    if apply_xml_model_changes:
        # read model from file
        model_etree = etree.parse(model.source)

        if model.changes:
            # apply changes
            apply_changes_to_xml_model(model, model_etree, sed_doc, working_dir)
            model.changes.clear()

            # write model to file
            if save_to_file:
                if temp_model_source is None:
                    modified_model_file, temp_model_source = tempfile.mkstemp(suffix='.xml')
                    os.close(modified_model_file)
                    model.source = temp_model_source

                model_etree.write(model.source,
                                  xml_declaration=True,
                                  encoding="utf-8",
                                  standalone=False,
                                  pretty_print=pretty_print_modified_xml_models)
    else:
        model_etree = None

    return model, temp_model_source, model_etree


def resolve_model(model, sed_doc, working_dir):
    """ Resolve the source of a model

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
        :obj:`str`: temporary path to the source of the modified model, if the model needed to be resolved from
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

        return model.source

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

        return model.source

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

        return None


def apply_changes_to_xml_model(model, model_etree, sed_doc, working_dir,
                               variable_values=None,
                               validate_unique_xml_targets=True):
    """ Modify an XML-encoded model according to a model change

    Args:
        model (:obj:`Model`): model
        model_etree (:obj:`etree._ElementTree`): element tree for model
        sed_doc (:obj:`SedDocument`): parent SED document; used to resolve sources defined by reference to other models
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)
        variable_values (:obj:`dict`, optional): dictionary which contains the value of each variable of each
            compute model change
        validate_unique_xml_targets (:obj:`bool`, optional): whether to validate the XML targets match
            uniue objects
    """
    # get namespaces
    namespaces = get_namespaces_for_xml_doc(model_etree)

    # get XPATH evaluator
    xpath_evaluator = etree.XPathEvaluator(model_etree, namespaces=namespaces)

    # apply changes
    model_etrees = {model.id: model_etree}
    for change in model.changes:
        if isinstance(change, ModelAttributeChange):

            # get object to change
            obj_xpath, sep, attr = change.target.rpartition('/@')
            if sep != '/@':
                raise ValueError('target {} is not a valid XPATH to an attribute of a model element'.format(change.target))
            objs = xpath_evaluator(obj_xpath)
            if validate_unique_xml_targets and len(objs) != 1:
                raise ValueError('xpath {} must match a single object'.format(obj_xpath))

            # change value
            for obj in objs:
                obj.set(attr, change.new_value)

        elif isinstance(change, AddElementModelChange):
            parents = xpath_evaluator(change.target)

            if validate_unique_xml_targets and len(parents) != 1:
                raise ValueError('xpath {} must match a single object'.format(change.target))

            try:
                new_elements = etree.fromstring('<root>' + change.new_elements + '</root>').getchildren()
            except etree.XMLSyntaxError as exception:
                raise ValueError('`{}` is not valid XML. {}'.format(change.new_elements, str(exception)))

            for parent in parents:
                for new_element in copy.deepcopy(new_elements):
                    parent.append(new_element)

        elif isinstance(change, ReplaceElementModelChange):
            old_elements = xpath_evaluator(change.target)

            if validate_unique_xml_targets and len(old_elements) != 1:
                raise ValueError('xpath {} must match a single object'.format(change.target))

            try:
                new_elements = etree.parse(io.StringIO('<root>' + change.new_elements + '</root>')).getroot().getchildren()
            except etree.XMLSyntaxError as exception:
                raise ValueError('`{}` is not valid XML. {}'.format(change.new_elements, str(exception)))

            for old_element in old_elements:
                parent = old_element.getparent()

                parent.remove(old_element)

                for new_element in copy.deepcopy(new_elements):
                    parent.append(new_element)

        elif isinstance(change, RemoveElementModelChange):
            elements = xpath_evaluator(change.target)

            if validate_unique_xml_targets and len(elements) != 1:
                raise ValueError('xpath {} must match a single object'.format(change.target))

            for element in elements:
                parent = element.getparent()
                parent.remove(element)

        elif isinstance(change, ComputeModelChange):
            # get the values of model variables referenced by compute model changes
            if variable_values is None:
                variable_values = get_values_of_variable_model_xml_targets_of_model_change(change, sed_doc, model_etrees, working_dir)

            # calculate new value
            new_value = calc_compute_model_change_new_value(change, variable_values)

            # get object to change
            obj_xpath, sep, attr = change.target.rpartition('/@')
            if sep != '/@':
                raise ValueError('target {} is not a valid XPATH to an attribute of a model element'.format(change.target))
            objs = xpath_evaluator(obj_xpath)
            if validate_unique_xml_targets and len(objs) != 1:
                raise ValueError('xpath {} must match a single object'.format(obj_xpath))

            # change value
            for obj in objs:
                obj.set(attr, str(new_value))

        else:
            raise NotImplementedError('Change{} of type {} is not supported'.format(
                ' ' + change.name if change.name else '', change.__class__.__name__))


def get_values_of_variable_model_xml_targets_of_model_change(change, sed_doc, model_etrees, working_dir):
    """ Get the values of the model variables of a compute model change

    Args:
        change (:obj:`ComputeModelChange`): compute model change
        sed_doc (:obj:`SedDocument`): SED document
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): map from the ids of models to element
            trees of their sources
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

    Returns:
        :obj:`dict`: dictionary which contains the value of each variable of each
            compute model change
    """
    variable_values = {}
    for variable in change.variables:
        variable_model = variable.model
        if variable_model.id not in model_etrees:
            copy_variable_model, temp_model_source, variable_model_etree = resolve_model_and_apply_xml_changes(
                variable_model, sed_doc, working_dir,
                apply_xml_model_changes=True,
                save_to_file=False)
            model_etrees[variable_model.id] = variable_model_etree

            if temp_model_source:
                os.remove(temp_model_source)

        variable_values[variable.id] = get_value_of_variable_model_xml_targets(
            variable, model_etrees)

    return variable_values


def get_value_of_variable_model_xml_targets(variable, model_etrees):
    """ Get the value of a variable of a model

    Args:
        variable (:obj:`Variable`): variable
        model_etrees (:obj:`dict` of :obj:`str` to :obj:`etree._Element`): dictionary that maps the
            ids of models to paths to files which contain their XML definitions

    Returns:
        :obj:`float`: value
    """
    if not variable.target:
        raise NotImplementedError('Compute model change variable `{}` must have a target'.format(variable.id))

    obj_xpath, sep, attr = variable.target.rpartition('/@')
    if sep != '/@':
        raise ValueError('target {} is not a valid XPATH to an attribute of a model element'.format(variable.target))

    et = model_etrees[variable.model.id]
    namespaces = get_namespaces_for_xml_doc(et)
    obj = et.xpath(obj_xpath, namespaces=namespaces)
    if len(obj) != 1:
        raise ValueError('xpath {} must match a single object in model {}'.format(obj_xpath, variable.model.id))

    value = obj[0].get(attr)
    if value is None:
        raise ValueError('Target `{}` is not defined in model `{}`.'.format(variable.target, variable.model.id))
    try:
        value = float(value)
    except ValueError:
        raise ValueError('Target `{}` in model `{}` must be a float.'.format(variable.target, variable.model.id))

    return value


def calc_compute_model_change_new_value(change, variable_values):
    """ Calculate the new value of a compute model change

    Args:
        change (:obj:`ComputeModelChange`): change
        variable_values (:obj:`dict`, optional): dictionary which contains the value of each variable of each
            compute model change

    Returns:
        :obj:`float`: new value
    """
    compiled_math = compile_math(change.math)

    workspace = {}
    for param in change.parameters:
        workspace[param.id] = param.value
    for var in change.variables:
        workspace[var.id] = variable_values.get(var.id, None)
        if workspace[var.id] is None:
            raise ValueError('Value of variable `{}` is not defined.'.format(var.id))

    return eval_math(change.math, compiled_math, workspace)


def calc_data_generator_results(data_generator, variable_results):
    """ Calculate the results of a data generator from the results of its variables

    Args:
        data_generator (:obj:`DataGenerator`): data generator
        variable_results (:obj:`VariableResults`): results for the variables of the data generator

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

    compiled_math = compile_math(data_generator.math)

    workspace = {}
    for param in data_generator.parameters:
        workspace[param.id] = param.value

    if not var_shapes:
        value = eval_math(math, compiled_math, workspace)
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

            result_el = eval_math(math, compiled_math, workspace)

            if n_dims == 0:
                result = numpy.array(result_el)
            else:
                result.flat[i_el] = result_el

    return result


def calc_data_generators_results(data_generators, variable_results, output, task, make_shapes_consistent=True):
    """ Calculator the values of a list of data generators

    Args:
        data_generators (:obj:`list` of :obj:`DataGenerator`): SED task
        variable_results (:obj:`VariableResults`): results of the SED variables involved in the data generators
        output (:obj:`Output`): SED output
        task (:obj:`Task`): SED task
        make_shapes_consistent (:obj:`bool`, optional): where to make the shapes of the data generators consistent
            (e.g., for concatenation into a table for a report)

    Returns:
        :obj:`tuple`:

            * :obj:`DataGeneratorResults`: values of the data generators
            * :obj:`dict` of :obj:`str` to :obj:`Status`: dictionary that maps the id of each data generator to its status
            * :obj:`Exception`: exception for failures
            * :obj:`bool`: where the task contributes to any of the data generators
    """
    task_contributes_to_data_generators = False
    statuses = {}
    exceptions = []
    results = DataGeneratorResults()

    for data_gen in data_generators:
        vars_available = True
        vars_failed = False
        for variable in data_gen.variables:
            if variable.task == task:
                task_contributes_to_data_generators = True
            if variable.id in variable_results:
                if variable_results.get(variable.id, None) is None:
                    vars_available = False
                    vars_failed = True
            else:
                vars_available = False

        if vars_failed:
            status = Status.FAILED
            msg = 'Data generator {} cannot be calculated because its variables were not successfully produced.'.format(data_gen.id)
            exceptions.append(ValueError(msg))
            result = None

        elif vars_available:
            try:
                result = calc_data_generator_results(data_gen, variable_results)
                status = Status.SUCCEEDED
            except Exception as exception:
                result = None
                exceptions.append(exception)
                status = Status.FAILED

        else:
            status = Status.QUEUED
            result = None

        statuses[data_gen.id] = status
        results[data_gen.id] = result

    if make_shapes_consistent:
        arrays = results.values()
        consistent_arrays = pad_arrays_to_consistent_shapes(arrays)
        for data_gen_id, result in zip(results.keys(), consistent_arrays):
            results[data_gen_id] = result

    if exceptions:
        exception = ValueError('Some generators could not be produced:\n  - {}'.format(
            '\n  '.join(str(exception) for exception in exceptions)))
    else:
        exception = None

    return results, statuses, exception, task_contributes_to_data_generators


def compile_math(math):
    """ Compile a mathematical expression

    Args:
        math (:obj:`str`): mathematical expression

    Returns:
        :obj:`_ast.Expression`: compiled expression
    """
    math_node = evalidate.evalidate(math,
                                    addnodes=[
                                        'Eq', 'NotEq', 'Gt', 'Lt', 'GtE', 'LtE',
                                        'Sub', 'Mult', 'Div' 'Pow',
                                        'And', 'Or', 'Not',
                                        'BitAnd', 'BitOr', 'BitXor',
                                        'Call',
                                    ],
                                    funcs=MATHEMATICAL_FUNCTIONS.keys())
    compiled_math = compile(math_node, '<math>', 'eval')
    return compiled_math


def eval_math(math, compiled_math, workspace):
    """ Compile a mathematical expression

    Args:
        math (:obj:`str`): mathematical expression
        compiled_math (:obj:`_ast.Expression`): compiled expression
        workspace (:obj:`dict`): values to use for the symbols in the expression

    Returns:
        :obj:`object`: result of the expression

    Raises:
        :obj:`ValueError`: if the expression could not be evaluated
    """
    invalid_symbols = set(RESERVED_MATHEMATICAL_SYMBOLS.keys()).intersection(set(workspace.keys()))
    if invalid_symbols:
        raise ValueError('Variables for mathematical expressions cannot have ids equal to the following reserved symbols:\n  - {}'.format(
            '\n  - '.join('`' + symbol + '`' for symbol in sorted(invalid_symbols))))

    try:
        return eval(compiled_math, MATHEMATICAL_FUNCTIONS, dict(**RESERVED_MATHEMATICAL_SYMBOLS, **workspace))
    except Exception as exception:
        raise ValueError('Expression `{}` could not be evaluated:\n  {}'.format(
            math, str(exception)))


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
