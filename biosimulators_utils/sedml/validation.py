""" Methods for validating SED objects

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-09
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..xml.utils import validate_xpaths_ref_to_unique_objects
from .data_model import (AbstractTask, Task, RepeatedTask,  # noqa: F401
                         Model, ModelLanguage, ModelLanguagePattern,
                         ModelChange, ComputeModelChange,
                         Simulation, OneStepSimulation, SteadyStateSimulation,
                         UniformTimeCourseSimulation, Variable,
                         Range, FunctionalRange, UniformRange, VectorRange,
                         Report, Plot2D, Plot3D)
from .utils import (append_all_nested_children_to_doc, get_range_len,
                    is_model_language_encoded_in_xml, get_models_referenced_by_task)
import collections
import copy
import lxml.etree
import math
import networkx
import os
import re

__all__ = [
    'validate_doc',
    'validate_reference',
    'validate_task',
    'validate_model',
    'validate_model_language',
    'validate_model_source',
    'validate_model_with_language',
    'validate_model_change_types',
    'validate_model_changes',
    'validate_simulation_type',
    'validate_simulation',
    'validate_uniform_range',
    'validate_output',
    'validate_data_generator_variables',
    'validate_target',
    'validate_variable_xpaths',
]


def validate_doc(doc, working_dir, validate_semantics=True, validate_models_with_languages=True):
    """ Validate a SED document

    Args:
        doc (:obj:`SedDocument`): SED document
        working_dir (:obj:`str`): working directory (e.g., for referencing model files)
        validate_semantics (:obj:`bool`, optional): if :obj:`True`, check that SED-ML is semantically valid
        validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []

    # validate that required ids exist and are unique
    for child_type in ('models', 'simulations', 'data_generators', 'tasks', 'outputs'):
        children = getattr(doc, child_type)

        missing_ids = [[str(i_child + 1)] for i_child, child in enumerate(children) if not getattr(child, 'id', None)]
        if missing_ids:
            errors.append([
                '{} must have ids. The following {} are missing ids:'.format(
                    child_type[0].upper() + child_type[1:], child_type),
                missing_ids,
            ])

        if validate_semantics:
            id_counts = {}
            for child in children:
                child_id = getattr(child, 'id', None)
                if child_id:
                    if child_id in id_counts:
                        id_counts[child_id] += 1
                    else:
                        id_counts[child_id] = 1

            repeated_ids = sorted([child_id for child_id, count in id_counts.items() if count > 1])

            if repeated_ids:
                errors.append([
                    '{} must have unique ids. The following ids are repeated:'.format(child_type[0].upper() + child_type[1:]),
                    [[id] for id in repeated_ids],
                ])

    if validate_semantics:
        # validate the models, simulations, tasks, data generators are children of the SED document
        doc_copy = copy.deepcopy(doc)
        append_all_nested_children_to_doc(doc_copy)

        for child_type in ('models', 'simulations', 'tasks', 'data_generators', 'outputs'):
            not_children = set([child.id for child in getattr(doc_copy, child_type)]).difference(
                set([child.id for child in getattr(doc, child_type)]))
            if not_children:
                errors.append([
                    '{} must be direct children of the SED document. The following {} are not direct children of the document:'.format(
                        child_type[0].upper() + child_type[1:], child_type),
                    [[child] for child in sorted(not_children)],
                ])

        # model
        model_ids = [model.id for model in doc.models]
        for i_model, model in enumerate(doc.models):
            model_errors, model_warnings = validate_model(model, model_ids, working_dir,
                                                          validate_models_with_languages=validate_models_with_languages)

            # append errors/warnings to global lists of errors and warnings
            model_id = '`' + model.id + '`' if model and model.id else str(i_model + 1)

            if model_errors:
                errors.append(['Model {} is invalid.'.format(model_id), model_errors])

            if model_warnings:
                warnings.append(['Model {} may be invalid.'.format(model_id), model_warnings])

        # model sources are acyclic
        model_source_graph = networkx.DiGraph()

        for model in doc.models:
            model_source_graph.add_node(model.id)

        for model in doc.models:
            if model.source and model.source.startswith('#'):
                model_source_graph.add_edge(model.id, model.source[1:])

        try:
            networkx.algorithms.cycles.find_cycle(model_source_graph)
            errors.append(['The sources of the models are defined cyclically. The sources of models must be acyclic.'])
        except networkx.NetworkXNoCycle:
            pass

        # validate the compute model changes are acyclic
        model_change_graph = networkx.DiGraph()

        for model in doc.models:
            model_change_graph.add_node(model.id)

        for model in doc.models:
            for change in model.changes:
                if isinstance(change, ComputeModelChange):
                    for variable in change.variables:
                        if variable.model and variable.model != model:
                            model_change_graph.add_edge(model.id, variable.model.id)

        try:
            networkx.algorithms.cycles.find_cycle(model_change_graph)
            errors.append(['The compute changes of the models are defined cyclically. The changes must be acyclic.'])
        except networkx.NetworkXNoCycle:
            pass

        # algorithms and parameters are described with valid ids of KiSAO terms
        for i_sim, sim in enumerate(doc.simulations):
            sim_errors = validate_simulation(sim)
            if sim_errors:
                sim_id = '`' + sim.id + '`' if sim and sim.id else str(i_sim + 1)
                errors.append(['Simulation {} is invalid.'.format(sim_id), sim_errors])

        # basic tasks reference a model and a simulation
        task_errors = {}
        task_warnings = {}
        for task in doc.tasks:
            task_errors[task] = {'ranges': [], 'other': []}
            task_warnings[task] = {'ranges': [], 'other': []}
            if isinstance(task, Task):
                task_errors[task]['other'].extend(validate_reference(task, 'Task', 'model', 'model'))
                task_errors[task]['other'].extend(validate_reference(task, 'Task', 'simulation', 'simulation'))
                task_errors[task]['other'].extend(validate_task(task))

        # sub tasks of repeated tasks reference tasks and have unique orders
        sub_task_graph = networkx.DiGraph()
        for task in doc.tasks:
            sub_task_graph.add_node(task.id)

            if isinstance(task, RepeatedTask):
                if not task.sub_tasks:
                    msg = 'Repeated task must have at least one sub-task.'
                    task_errors[task]['other'].append([msg])

                for i_sub_task, sub_task in enumerate(task.sub_tasks):
                    if sub_task.task and isinstance(sub_task.task, AbstractTask):
                        sub_task_graph.add_edge(task.id, sub_task.task.id)
                    else:
                        msg = 'Sub-task {} must reference a task.'.format(i_sub_task + 1)
                        task_errors[task]['other'].append([msg])

                duplicate_orders = [item for item, count in collections.Counter(
                    sub_task.order for sub_task in task.sub_tasks).items() if count > 1]
                if duplicate_orders:
                    msg = ('The `order` of each sub-task should be distinct within a repeated task. '
                           'Multiple sub-tasks have the following orders:\n  - {}').format(
                        '\n  - '.join([str(order) for order in sorted(duplicate_orders)]))
                    task_errors[task]['other'].append([msg])

        try:
            networkx.algorithms.cycles.find_cycle(sub_task_graph)
            errors.append(['The subtasks are defined cyclically. The graph of subtasks must be acyclic.'])
        except networkx.NetworkXNoCycle:
            pass

        # Ranges of repeated tasks
        # - Functional ranges
        #   - Reference other ranges
        #   - Parameters of functional ranges
        #     - Have ids
        #   - Variables of functional ranges
        #     - Have ids
        #     - Reference models
        #     - Have symbols or targets
        #   - Have math
        #   - Graph is acyclic
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                if not isinstance(task.range, Range):
                    task_errors[task]['ranges'].append(['Repeated task must have a main range.'])

                for i_range, range in enumerate(task.ranges):
                    range_errors = []

                    if not range or not range.id:
                        range_errors.append(['Range must have an id.'])

                    if isinstance(range, FunctionalRange):
                        if not range.range:
                            range_errors.append(['Functional range must reference another range.'])

                        for i_param, param in enumerate(range.parameters):
                            if not param.id:
                                range_errors.append(['Parameter {} must have an id.'.format(i_param + 1)])

                        for i_variable, variable in enumerate(range.variables):
                            variable_errors = []

                            if not variable.id:
                                variable_errors.append(['Variable must have an id.'])

                            if not variable.model:
                                variable_errors.append(['Variable must reference a model.'])
                            if variable.task:
                                variable_errors.append(['Variable should not reference a task.'])

                            if not variable.symbol and not variable.target:
                                variable_errors.append(['Variable should define a symbol or target.'])
                            if variable.symbol and variable.target:
                                variable_errors.append(['Variable should define a symbol or target, not both.'])

                            if variable.target and variable.model and variable.model.language:
                                variable_errors.extend(validate_target(
                                    variable.target, variable.target_namespaces, variable.model.language))

                            if variable_errors:
                                variable_id = '`' + variable.id + '`' if variable and variable.id else str(i_variable + 1)
                                range_errors.append(['Variable {} is invalid.'.format(variable_id), variable_errors])

                        if not range.math:
                            range_errors.append(['Functional range must have math.'])

                    elif isinstance(range, UniformRange):
                        range_errors.extend(validate_uniform_range(range))

                    elif isinstance(range, VectorRange):
                        pass

                    else:
                        range_errors.append(['Range must be a functional, uniform, or vector range, not an instance of `{}`.'.format(
                            range.__class__.__name__)])

                    if range_errors:
                        range_id = '`' + range.id + '`' if range and range.id else str(i_range + 1)
                        task_errors[task]['ranges'].append(['{} {} is invalid.'.format(range.__class__.__name__, range_id), range_errors])

        # ranges of repeated tasks have unique ids
        ranges_have_ids = True
        range_ids = []
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                for i_range, range in enumerate(task.ranges):
                    if isinstance(range, Range) and range.id:
                        range_ids.append(range.id)
                    else:
                        ranges_have_ids = False

        duplicate_range_ids = [item for item, count in collections.Counter(range_ids).items() if count > 1]
        if duplicate_range_ids:
            msg = ('Ranges must have unique ids. The following range ids are repeated:\n  - {}').format(
                '\n  - '.join(sorted(duplicate_range_ids)))
            task_errors[task]['ranges'].append([msg])

        # graph of ranges is acyclic
        check_range_cycles = ranges_have_ids and not duplicate_range_ids
        functional_range_graph = networkx.DiGraph()
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                for range in task.ranges:
                    if isinstance(range, FunctionalRange):
                        if range.id and range.range and range.range.id:
                            functional_range_graph.add_node(range.id)
                            functional_range_graph.add_edge(range.id, range.range.id)
                        else:
                            check_range_cycles = False

        check_range_lens = False
        if check_range_cycles:
            try:
                networkx.algorithms.cycles.find_cycle(functional_range_graph)
                errors.append(['The functional ranges are defined cyclically. The graph of functional ranges must be acyclic.'])
            except networkx.NetworkXNoCycle:
                check_range_lens = True

        # ranges of repeated tasks
        # - are of a supported type (error)
        # - are at least as long as the main range (error)
        # - the same lengths (warnings)
        if check_range_lens:
            for task in doc.tasks:
                if isinstance(task, RepeatedTask):
                    if isinstance(task.range, Range):
                        main_range_len = get_range_len(task.range)
                    else:
                        main_range_len = 0

                    for range in task.ranges:
                        range_len = get_range_len(range)
                        if range_len < main_range_len:
                            msg = (
                                'The child ranges of repeated tasks must be at least as long as '
                                'the main range of their parent repeated tasks. '
                                'Range `{}` is shorter than its main range, {} < {}.'
                            ).format(range.id, range_len, main_range_len)
                            task_errors[task]['ranges'].append([msg])
                        elif range_len > main_range_len:
                            msg = ('Child range `{}` is longer than its main range ({} > {}). '
                                   'The tail elements of the range will be ignored.').format(range.id, range_len, main_range_len)
                            task_warnings[task]['ranges'].append([msg])

                    for i_change, change in enumerate(task.changes):
                        if change.range:
                            range_len = get_range_len(change.range)
                            if range_len < main_range_len:
                                msg = (
                                    'The child ranges of repeated tasks must be '
                                    'at least as long as the main range of their parent repeated tasks. '
                                    'Range `{}` is shorter than its main range, {} < {}.'
                                ).format(change.range.id, range_len, main_range_len)
                                task_errors[task]['ranges'].append([msg])
                            elif range_len > main_range_len:
                                msg = (
                                    'Child range `{}` is longer than its main range ({} > {}). '
                                    'The tail elements of the range will be ignored.'
                                ).format(change.range.id, range_len, main_range_len)
                                task_warnings[task]['ranges'].append([msg])

        # Set value changes of repeated tasks
        # - Changes reference models
        # - Changes reference a symbol or target
        # - Parameters
        #   - Have ids
        # - Variables
        #   - Have ids
        #   - Reference a model, not a task
        #   - Define a target, not a symbol
        # - Changes have math
        for task in doc.tasks:
            if isinstance(task, RepeatedTask):
                all_change_errors = []
                for i_change, change in enumerate(task.changes):
                    change_errors = []

                    if not change.model:
                        msg = ('Set value change must reference a model. '
                               'Change does not reference a model.')
                        change_errors.append([msg])

                    if change.target:
                        if change.model and change.model.language:
                            change_errors.extend(validate_target(change.target, change.target_namespaces, change.model.language))

                    else:
                        msg = ('Set value changes must define a target. '
                               'Change does not define a target.')
                        change_errors.append([msg])

                    if change.symbol:
                        msg = ('Set value changes should not define a symbol. '
                               'Change defines a symbol.')
                        change_errors.append([msg])

                    for i_parameter, parameter in enumerate(change.parameters):
                        if not parameter.id:
                            change_errors.append(['Parameter {} must have an id.'.format(i_parameter + 1)])

                    for i_variable, variable in enumerate(change.variables):
                        variable_errors = []

                        if not variable.id:
                            variable_errors.append(['Variable must have an id.'])

                        if not variable.model:
                            variable_errors.append(['Set value variable must reference a model.'])
                        if variable.task:
                            variable_errors.append(['Set value variable should not reference a task.'])

                        if not variable.target and not variable.symbol:
                            variable_errors.append(['Set value variable must define a target or a symbol.'])
                        if variable.target and variable.symbol:
                            variable_errors.append(['Set value variable must define a target or a symbol, not both.'])

                        if variable.target and variable.model and variable.model.language:
                            variable_errors.extend(validate_target(variable.target, variable.target_namespaces, variable.model.language))

                        if variable_errors:
                            variable_id = '`' + variable.id + '`' if variable and variable.id else str(i_variable + 1)
                            change_errors.append(['Variable {} is invalid.'.format(variable_id), variable_errors])

                    if not change.math:
                        msg = 'Set value change must have math.'
                        change_errors.append([msg])

                    if change_errors:
                        change_id = '`' + change.id + '`' if change and change.id else str(i_change + 1)
                        all_change_errors.append(['Change {} is invalid.'.format(change_id), change_errors])

                if all_change_errors:
                    task_errors[task]['other'].append(['Changes are invalid.', all_change_errors])

        for i_task, task in enumerate(doc.tasks):
            task_id = '`' + task.id + '`' if task and task.id else str(i_task + 1)

            task_errors[task]['other'] += task_errors[task]['ranges']
            task_warnings[task]['other'] += task_warnings[task]['ranges']

            if task_errors[task]['other']:
                errors.append(['Task {} is invalid.'.format(task_id), task_errors[task]['other']])
            if task_warnings[task]['other']:
                warnings.append(['Task {} may be invalid.'.format(task_id), task_warnings[task]['other']])

        # variables of data generators
        # - have ids
        # - have target OR symbol
        # - don't have model references
        # - have math
        for i_data_gen, data_gen in enumerate(doc.data_generators):
            data_gen_errors = []

            for i_parameter, param in enumerate(data_gen.parameters):
                if not param.id:
                    data_gen_errors.append(['Parameter {} must have an id.'.format(i_parameter + 1)])

            data_gen_errors.extend(validate_data_generator_variables(data_gen.variables))

            if not data_gen.math:
                data_gen_errors.append(['Data generator must have math.'])

            if data_gen_errors:
                data_gen_id = '`' + data_gen.id + '`' if data_gen and data_gen.id else str(i_data_gen + 1)
                errors.append(['Data generator {} is invalid.'.format(data_gen_id), data_gen_errors])

        # validate outputs
        # - reports
        #   - data sets have ids and labels
        #   - data sets reference data generators
        # - plots
        #   - curves and surfaces have ids
        #   - x, y, z attributes reference data generators
        for i_output, output in enumerate(doc.outputs):
            output_errors = validate_output(output)

            if output_errors:
                output_id = '`' + output.id + '`' if output and output.id else str(i_output + 1)
                errors.append(['Output {} is invalid.'.format(output_id), output_errors])

    return (errors, warnings)


def validate_reference(obj, obj_label, attr_name, attr_label):
    errors = []

    if not getattr(obj, attr_name):
        errors.append(['{} `{}` must have a {}.'.format(obj_label, obj.id, attr_label)])

    return errors


def validate_task(task):
    """ Validate a simulation task

    Args:
        task (:obj:`Task`): task

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    if isinstance(task, Task):

        # check that task has model
        if not task.model:
            errors.append(['Task must have a model.'])

        # check that task has simulation
        if not task.simulation:
            errors.append(['Task must have a simulation.'])

    else:
        errors.append(['Task must be an instance of `Task` not `{}`.'.format(task.__class__.__name__)])

    # return errors
    return errors


def validate_model(model, model_ids, working_dir, validate_models_with_languages=True):
    """ Check a model

    Args:
        model (:obj:`Model`): model
        model_ids (:obj:`list` of :obj:`str`): ids of models
        working_dir (:obj:`str`): working directory (e.g., for referencing model files)
        validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of warnings (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []

    # check source
    if not model.language:
        errors.append(['Model must have a language.'])

    # check source
    tmp_errors, tmp_warnings = validate_model_source(
        model, model_ids, working_dir, validate_models_with_languages=validate_models_with_languages)
    errors.extend(tmp_errors)
    warnings.extend(tmp_warnings)

    # validate that model changes have targets
    model_change_errors = validate_model_changes(model)
    if model_change_errors:
        errors.append(['The changes of the model are invalid.', model_change_errors])

    return (errors, warnings)


def validate_model_language(language, valid_language):
    """ Check that model is encoded in a specific language

    Args:
        language (:obj:`str`): model language
        valid_language (:obj:`ModelLanguage`): regular expression pattern for valid model language

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    valid_language_pattern = ModelLanguagePattern[valid_language.name]

    if not language or not re.match(valid_language_pattern.value, language):
        msg = (
            "Model language `{}` is not supported. "
            "Models must be in {} format (`sed:model/@language` must match `{}` such as `{}`)."
        ).format(language or '', valid_language.name, valid_language_pattern.value, valid_language.value)
        errors.append([msg])

    return errors


def validate_model_source(model, model_ids, working_dir, validate_models_with_languages=True):
    """ Check the source of a model

    Args:
        model (:obj:`Model`): model
        model_ids (:obj:`list` of :obj:`str`): ids of models
        working_dir (:obj:`str`): working directory (e.g., for referencing model files)
        validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of warnings (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []

    if not model.source:
        errors.append(['Model must have a source.'])

    elif model.source.startswith('#'):
        if model.source[1:] not in model_ids:
            errors.append(['The referenced source `{}` is not defined.'.format(model.source)])

    elif not model.source.startswith('#') and not model.source.startswith('http://') and not model.source.startswith('https://'):
        if os.path.isabs(model.source):
            model_source = model.source
        else:
            model_source = os.path.join(working_dir, model.source)

        if validate_models_with_languages:
            model_source_errors, model_source_warnings = validate_model_with_language(model_source, model.language, name=model.id)
            if model_source_errors:
                errors.append(['The model file `{}` is invalid.'.format(model.source), model_source_errors])
            if model_source_warnings:
                warnings.append(['The model file `{}` may be invalid.'.format(model.source), model_source_warnings])

    return (errors, warnings)


def validate_model_with_language(source, language, name=None):
    """ Check that a model is valid

    Args:
        source (:obj:`str`): path to model
        language (:obj:`ModelLanguage`): language
        name (:obj:`str`, optional): name of model for use in error messages

    Returns:
        :obj:`tuple`:

            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
            * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []
    warnings = []

    if language == ModelLanguage.SBML:
        from ..sbml.validation import validate_model
    else:
        warnings.append(['No validation is available for models encoded in `{}`'.format(getattr(language, 'name', language) or '')])
        return (errors, warnings)

    return validate_model(source, name=name)


def validate_model_change_types(changes, types=(ModelChange, )):
    """ Check that model changes are valid

    Args:
        changes (:obj:`list` of :obj:`ModelChange`): model changes
        types (:obj:`type` or :obj:`tuple` of :obj:`type`, optional): valid type(s) of model changes

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    for i_change, change in enumerate(changes):
        if not isinstance(change, types):
            msg = "".join([
                'Model change {} of type `{}` is not supported. '.format(i_change + 1, change.__class__.__name__),
                'Model changes must be instances of one of the following types:\n  - {}'.format(
                    '\n  - '.join(type.__name__ for type in types)),
            ])
            errors.append([msg])

    return errors


def validate_model_changes(model):
    """ Check that model changes are semantically valid

    * Check that the variables of compute model changes are valid

    Args:
        model (:obj:`Model`): model

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    for i_change, change in enumerate(model.changes):
        change_errors = []

        if change.target:
            if model.language:
                change_errors.extend(validate_target(change.target, change.target_namespaces, model.language))

        else:
            change_errors.append(['Model attribute change must define a target.'])

        if isinstance(change, ComputeModelChange):
            for i_parameter, parameter in enumerate(change.parameters):
                if not parameter.id:
                    change_errors.append(['Parameter {} must have an id.'.format(i_parameter + 1)])

            for i_variable, variable in enumerate(change.variables):
                variable_errors = []

                if not variable.id:
                    variable_errors.append(['Variable must have an id.'])

                if not variable.model:
                    variable_errors.append(['Variable must reference a model.'])
                if variable.task:
                    variable_errors.append(['Variable should not reference a task.'])

                if not variable.target:
                    variable_errors.append(['Variable must define a target.'])
                if variable.symbol:
                    variable_errors.append(['Variable must define a target, not a symbol.'])

                if variable.target and variable.model and variable.model.language:
                    variable_errors.extend(validate_target(variable.target, variable.target_namespaces, variable.model.language))

                if variable_errors:
                    var_id = '`' + variable.id + '`' if variable and variable.id else str(i_variable + 1)
                    change_errors.append(['Variable {} is invalid.'.format(var_id), variable_errors])

            if not change.math:
                change_errors.append(['Compute model change must have math.'])

        if change_errors:
            change_id = '`' + change.id + '`' if change and change.id else str(i_change + 1)
            errors.append(['Change {} is invalid.'.format(change_id), change_errors])

    return errors


def validate_simulation_type(simulation, types):
    """ Check that simulation is a time course simulation

    Args:
        simulation (:obj:`Simulation`): simulation
        types (:obj:`type`): valid simulation types

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    if not isinstance(simulation, types):
        errors.append([
            'Simulation {} of type `{}` is not supported. Simulation must be an instance of one of the following:\n  - {}'.format(
                simulation.id, simulation.__class__.__name__, '\n  - '.join(type.__name__ for type in types))
        ])

    return errors


def validate_simulation(simulation):
    """ Check that simulation is a valid simulation

    Args:
        simulation (:obj:`Simulation`): simulation

    Returns:
        * nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    if isinstance(simulation, OneStepSimulation):
        if not isinstance(simulation.step, (int, float)):
            errors.append(['Step must be a float.'])

    elif isinstance(simulation, SteadyStateSimulation):
        pass

    elif isinstance(simulation, UniformTimeCourseSimulation):
        if simulation.initial_time is None:
            errors.append(['Inital time must be set.'])
        if simulation.output_start_time is None:
            errors.append(['Output start time must be set.'])
        if simulation.output_end_time is None:
            errors.append(['Output end time must be set.'])
        if simulation.number_of_steps is None:
            errors.append(['Number of steps must be set.'])

        if (
            simulation.initial_time is not None
            and simulation.output_start_time is not None
            and simulation.output_start_time < simulation.initial_time
        ):
            errors.append(['Output start time {} must be at least the initial time {}.'.format(
                simulation.output_start_time, simulation.initial_time)])

        if (
            simulation.output_start_time is not None
            and simulation.output_end_time is not None
            and simulation.output_end_time < simulation.output_start_time
        ):
            errors.append(['Output end time {} must be at least the output start time {}.'.format(
                simulation.output_end_time, simulation.output_start_time)])

        if simulation.number_of_steps is not None:
            if simulation.number_of_steps < 1:
                errors.append(['Number of points must be at least 1.'])

            if math.floor(simulation.number_of_steps) != simulation.number_of_steps:
                errors.append(['Number of points must be an integer.'])

    else:
        errors.append(['Simulation must be a one step, steady-state, or uniform time course, not an instance of `{}`.'.format(
            simulation.__class__.__name__)])

    if simulation.algorithm:
        if not simulation.algorithm.kisao_id or not re.match(r'^KISAO_\d{7}$', simulation.algorithm.kisao_id):
            errors.append(['Algorithm has an invalid KiSAO id `{}`.'.format(simulation.algorithm.kisao_id)])
        for i_change, change in enumerate(simulation.algorithm.changes):
            if not change.kisao_id or not re.match(r'^KISAO_\d{7}$', change.kisao_id):
                errors.append(
                    ['Algorithm change {} has an invalid KiSAO id `{}`.'.format(i_change + 1, change.kisao_id)])

    else:
        errors.append(['Simulation must have an algorithm.'])

    return errors


def validate_uniform_range(range):
    """ Validate a uniform range

    Args:
        range (:obj:`data_model.UniformRange`): range

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    if range.number_of_steps < 1:
        errors.append(['Uniform range `{}` must have at least one step.'.format(
            range.id)])

    return errors


def validate_data_generator_variables(variables):
    """ Check variables have a symbol or target

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    for i_variable, variable in enumerate(variables):
        variable_errors = []

        if not variable.id:
            variable_errors.append(['Variable must have an id.'])

        if variable.model:
            variable_errors.append(['Variable should not reference a model.'])

        if not variable.task:
            variable_errors.append(['Variable must reference a task.'])

        if (variable.symbol and variable.target) or (not variable.symbol and not variable.target):
            variable_errors.append(['Variable must define a symbol or target.'])

        if variable.target and variable.task:
            models = get_models_referenced_by_task(variable.task)
            for model in models:
                if model and model.language:
                    variable_errors.extend(validate_target(variable.target, variable.target_namespaces, model.language))

        if variable_errors:
            variable_id = '`' + variable.id + '`' if variable and variable.id else str(i_variable + 1)
            errors.append(['Variable {} is invalid.'.format(variable_id), variable_errors])

    return errors


def validate_output(output):
    """ Validate an output

    Args:
        output (:obj:`Output`): output

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    if isinstance(output, Report):
        for i_data_set, data_set in enumerate(output.data_sets):
            data_set_errors = []

            if not data_set.id:
                data_set_errors.append(['Data set must have an id.'])

            if not data_set.label:
                data_set_errors.append(['Data set must have a label.'])

            data_set_errors.extend(validate_reference(data_set, 'Data set', 'data_generator', 'data data generator'))

            if data_set_errors:
                data_set_id = '`' + data_set.id + '`' if data_set and data_set.id else str(i_data_set + 1)
                errors.append(['Data set {} is invalid.'.format(data_set_id), data_set_errors])

    elif isinstance(output, Plot2D):
        for i_curve, curve in enumerate(output.curves):
            curve_errors = []

            if not curve.id:
                curve_errors.append(['Curve must have an id.'])
            curve_errors.extend(validate_reference(curve, 'Curve', 'x_data_generator', 'x data data generator'))
            curve_errors.extend(validate_reference(curve, 'Curve', 'y_data_generator', 'y data data generator'))

            if curve_errors:
                curve_id = '`' + curve.id + '`' if curve and curve.id else str(i_curve + 1)
                errors.append(['Curve {} is invalid.'.format(curve_id), curve_errors])

    elif isinstance(output, Plot3D):
        for i_surface, surface in enumerate(output.surfaces):
            surface_errors = []

            if not surface.id:
                surface_errors.append(['Surface must have an id.'])
            surface_errors.extend(validate_reference(surface, 'Surface', 'x_data_generator', 'x data data generator'))
            surface_errors.extend(validate_reference(surface, 'Surface', 'y_data_generator', 'y data data generator'))
            surface_errors.extend(validate_reference(surface, 'Surface', 'z_data_generator', 'z data data generator'))

            if surface_errors:
                surface_id = '`' + surface.id + '`' if surface and surface.id else str(i_surface + 1)
                errors.append(['Surface {} is invalid.'.format(surface_id), surface_errors])

    return errors


def validate_target(target, namespaces, language):
    """ Validate that a target is a valid XPath and that the namespaces needed to resolve a target are defined

    Args:
        target (:obj:`string`): XPath to a model element or attribute
        namespaces (:obj:`dict`): dictionary that maps prefixes of namespaces to their URIs
        language (:obj:`str`): model language

    Returns:
        nested :obj:`list` of :obj:`str`: nested list of errors (e.g., required ids missing or ids not unique)
    """
    errors = []

    if is_model_language_encoded_in_xml(language):

        if None in namespaces:
            namespaces = dict(namespaces)
            namespaces.pop(None, None)

        try:
            xpath = lxml.etree.XPath(target, namespaces=namespaces)
            root = lxml.etree.Element("root")
            try:
                xpath.evaluate(root)
            except lxml.etree.XPathEvalError as exception:
                if 'Undefined namespace prefix' in str(exception):
                    if namespaces:
                        ns_message = 'Only the following namespaces are defined for the target: {}.'.format(
                            ', '.join('`' + prefix + '`' for prefix in sorted(namespaces.keys())))
                    else:
                        ns_message = 'No namespaces are defined for the target.'

                    errors.append(['One or more namespaces required for target `{}` are not defined. {}'.format(target, ns_message)])

        except lxml.etree.XPathSyntaxError:
            errors.append(['Target `{}` is not a valid XML XPath.'.format(target)])

    return errors


def validate_variable_xpaths(variables, model_source, attr='id'):
    """ Validate that the target of each variable matches one object in
    an XML-encoded model

    Args:
        variables (:obj:`list` of :obj:`Variable`): variables
        model_source (:obj:`str`): path to XML model file
        attr (:obj:`str`, optional): attribute to get values of

    Returns:
        :obj:`dict` of :obj:`str` to :obj:`str`: dictionary that maps each XPath to the
            value of the attribute of the object in the XML file that matches the XPath
    """
    x_path_attrs = {}
    for variable in variables:
        if variable.target:
            x_path = variable.target
            if '/@' in x_path:
                x_path, _, _ = x_path.rpartition('/@')
            x_path_attrs[variable.target] = validate_xpaths_ref_to_unique_objects(
                model_source, [x_path], variable.target_namespaces, attr=attr)[x_path]
    return x_path_attrs
