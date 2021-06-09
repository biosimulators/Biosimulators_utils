""" Utilities for working with Smoldyn models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...sedml.data_model import ModelAttributeChange, Variable, Symbol
from ...utils.core import flatten_nested_list_of_strings
from .validation import validate_model
import os
import re
import types  # noqa: F401

__all__ = ['get_parameters_variables_for_simulation']

CONFIG_DECLARATION_PATTERNS = [
    {
        'regex': r'^(dim) (.*?)$',
        'parameter': {
            'group': lambda match: 'number_dimensions',
            'id': lambda match, i_group: 'number_dimensions',
            'name': lambda match, i_group: 'Number of dimensions',
            'target': lambda match: match.group(1),
            'new_value': lambda match: match.group(2),
        }
    },
    {
        'regex': r'^low_wall ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'low_wall_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'low_{}_wall_{}'.format(match.group(1), i_group + 1),
            'name': lambda match, i_group: 'Low {} wall {}'.format(match.group(1), i_group + 1),
            'target': lambda match: 'low_wall {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^high_wall ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'high_wall_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'high_{}_wall_{}'.format(match.group(1), i_group + 1),
            'name': lambda match, i_group: 'High {} wall {}'.format(match.group(1), i_group + 1),
            'target': lambda match: 'high_wall {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^boundaries ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'boundaries_{}'.format(match.group(1)),
            'id': lambda match, i_group: '{}_boundary'.format(match.group(1)),
            'name': lambda match, i_group: '{} boundary'.format(match.group(1).upper()),
            'target': lambda match: 'boundaries {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^define ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'define_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'value_parameter_{}'.format(match.group(1)),
            'name': lambda match, i_group: 'Value of parameter "{}"'.format(match.group(1)),
            'target': lambda match: 'define {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^difc ([^ \(\)]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'difc_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'diffusion_coefficient_species_{}'.format(match.group(1)),
            'name': lambda match, i_group: 'Diffusion coefficient of species "{}"'.format(match.group(1)),
            'target': lambda match: 'difc {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^difc ([^ \(\)]+)\(([^ \(\)]+)\) (.*?)$',
        'parameter': {
            'group': lambda match: 'difc_{}_{}'.format(match.group(1), match.group(2)),
            'id': lambda match, i_group: 'diffusion_coefficient_species_{}_state_{}'.format(match.group(1), match.group(2)),
            'name': lambda match, i_group: 'Diffusion coefficient of species "{}" in state "{}"'.format(match.group(1), match.group(2)),
            'target': lambda match: 'difc {}({})'.format(match.group(1), match.group(2)),
            'new_value': lambda match: match.group(3),
        },
    },
    {
        'regex': r'^difc_rule ([^ \(\)]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'difc_rule_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'diffusion_coefficient_rule_species_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', match.group(1))),
            'name': lambda match, i_group: 'Diffusion coefficient rule for species "{}"'.format(match.group(1)),
            'target': lambda match: 'difc_rule {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^difc_rule ([^ \(\)]+)\(([^ \(\)]+)\) (.*?)$',
        'parameter': {
            'group': lambda match: 'difc_rule_{}_{}'.format(
                match.group(1), match.group(2)),
            'id': lambda match, i_group: 'diffusion_coefficient_rule_species_{}_state_{}'.format(
                re.sub('[^a-zA-Z0-9_]', '_', match.group(1)), match.group(2)),
            'name': lambda match, i_group: 'Diffusion coefficient rule for species "{}" in state "{}"'.format(
                match.group(1), match.group(2)),
            'target': lambda match: 'difc_rule {}({})'.format(
                match.group(1), match.group(2)),
            'new_value': lambda match: match.group(3),
        },
    },
    {
        'regex': r'^difm ([^ \(\)]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'difm_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'membrane_diffusion_coefficient_species_{}'.format(match.group(1)),
            'name': lambda match, i_group: 'Membrane diffusion coefficient of species "{}"'.format(match.group(1)),
            'target': lambda match: 'difm {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^difm ([^ \(\)]+)\(([^ \(\)]+)\) (.*?)$',
        'parameter': {
            'group': lambda match: 'difm_{}_{}'.format(match.group(1), match.group(2)),
            'id': lambda match, i_group: 'membrane_diffusion_coefficient_species_{}_state_{}'.format(
                match.group(1), match.group(2)),
            'name': lambda match, i_group: 'Membrane diffusion coefficient of species "{}" in state "{}"'.format(
                match.group(1), match.group(2)),
            'target': lambda match: 'difm {}({})'.format(match.group(1), match.group(2)),
            'new_value': lambda match: match.group(3),
        },
    },
    {
        'regex': r'^difm_rule ([^ \(\)]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'difm_rule_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'membrane_diffusion_coefficient_rule_species_{}'.format(
                re.sub('[^a-zA-Z0-9_]', '_', match.group(1))),
            'name': lambda match, i_group: 'Membrane diffusion coefficient rule for species "{}"'.format(match.group(1)),
            'target': lambda match: 'difm_rule {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^difm_rule ([^ \(\)]+)\(([^ \(\)]+)\) (.*?)$',
        'parameter': {
            'group': lambda match: 'difm_rule_{}_{}'.format(match.group(1), match.group(2)),
            'id': lambda match, i_group: 'membrane_diffusion_coefficient_rule_species_{}_state_{}'.format(
                re.sub('[^a-zA-Z0-9_]', '_', match.group(1)), match.group(2)),
            'name': lambda match, i_group: 'Membrane diffusion coefficient rule for species "{}" in state "{}"'.format(
                match.group(1), match.group(2)),
            'target': lambda match: 'difm_rule {}({})'.format(match.group(1), match.group(2)),
            'new_value': lambda match: match.group(3),
        },
    },
    {
        'regex': r'^drift ([^ \(\)]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'drift_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'drift_species_{}'.format(match.group(1)),
            'name': lambda match, i_group: 'Drift of species "{}"'.format(match.group(1)),
            'target': lambda match: 'drift {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^drift ([^ \(\)]+)\(([^ \(\)]+)\) (.*?)$',
        'parameter': {
            'group': lambda match: 'drift_{}_{}'.format(match.group(1), match.group(2)),
            'id': lambda match, i_group: 'drift_species_{}_state_{}'.format(
                match.group(1), match.group(2)),
            'name': lambda match, i_group: 'Drift of species "{}" in state "{}"'.format(
                match.group(1), match.group(2)),
            'target': lambda match: 'drift {}({})'.format(match.group(1), match.group(2)),
            'new_value': lambda match: match.group(3),
        },
    },
    {
        'regex': r'^drift_rule ([^ \(\)]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'drift_rule_{}'.format(match.group(1)),
            'id': lambda match, i_group: 'drift_rule_species_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', match.group(1))),
            'name': lambda match, i_group: 'Drift rule for species "{}"'.format(match.group(1)),
            'target': lambda match: 'drift_rule {}'.format(match.group(1)),
            'new_value': lambda match: match.group(2),
        },
    },
    {
        'regex': r'^drift_rule ([^ \(\)]+)\(([^ \(\)]+)\) (.*?)$',
        'parameter': {
            'group': lambda match: 'drift_rule_{}_{}'.format(match.group(1), match.group(2)),
            'id': lambda match, i_group: 'drift_rule_species_{}_state_{}'.format(
                re.sub('[^a-zA-Z0-9_]', '_', match.group(1)), match.group(2)),
            'name': lambda match, i_group: 'Drift rule for species "{}" in state "{}"'.format(
                match.group(1), match.group(2)),
            'target': lambda match: 'drift_rule {}({})'.format(match.group(1), match.group(2)),
            'new_value': lambda match: match.group(3),
        },
    },
    {
        'regex': r'^surface_drift ([^ \(\)]+) ([^ ]+) ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'surface_drift_{}_{}_{}'.format(
                match.group(1), match.group(2), match.group(3)),
            'id': lambda match, i_group: 'surface_drift_species_{}_surface_{}_shape_{}'.format(
                match.group(1), match.group(2), match.group(3)),
            'name': lambda match, i_group: 'Surface drift of species "{}" on surface "{}" with panel shape "{}"'.format(
                match.group(1), match.group(2), match.group(3)),
            'target': lambda match: 'surface_drift {} {} {}'.format(
                match.group(1), match.group(2), match.group(3)),
            'new_value': lambda match: match.group(4),
        },
    },
    {
        'regex': r'^surface_drift ([^ \(\)]+)\(([^ \(\)]+)\) ([^ ]+) ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'surface_drift_{}_{}_{}_{}'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'id': lambda match, i_group: 'surface_drift_species_{}_state_{}_surface_{}_shape_{}'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'name': lambda match, i_group: 'Surface drift of species "{}" in state "{}" on surface "{}" with panel shape "{}"'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'target': lambda match: 'surface_drift {}({}) {} {}'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'new_value': lambda match: match.group(5),
        },
    },
    {
        'regex': r'^surface_drift_rule ([^ \(\)]+) ([^ ]+) ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'surface_drift_rule_{}_{}_{}'.format(
                match.group(1), match.group(2), match.group(3)),
            'id': lambda match, i_group: 'surface_drift_rule_species_{}_surface_{}_panel_{}'.format(
                re.sub('[^a-zA-Z0-9_]', '_', match.group(1)), match.group(2), match.group(3)),
            'name': lambda match, i_group: 'Surface drift rule for species "{}" on surface "{}" of panel shape "{}"'.format(
                match.group(1), match.group(2), match.group(3)),
            'target': lambda match: 'surface_drift_rule {} {} {}'.format(
                match.group(1), match.group(2), match.group(3)),
            'new_value': lambda match: match.group(4),
        },
    },
    {
        'regex': r'^surface_drift_rule ([^ \(\)]+)\(([^ \(\)]+)\) ([^ ]+) ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'surface_drift_rule_{}_{}_{}_{}'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'id': lambda match, i_group: 'surface_drift_rule_species_{}_state_{}_surface_{}_panel_{}'.format(
                re.sub('[^a-zA-Z0-9_]', '_', match.group(1)), match.group(2), match.group(3), match.group(4)),
            'name': lambda match, i_group: 'Surface drift rule for species "{}" in state "{}" on surface "{}" of panel shape "{}"'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'target': lambda match: 'surface_drift_rule {}({}) {} {}'.format(
                match.group(1), match.group(2), match.group(3), match.group(4)),
            'new_value': lambda match: match.group(5),
        },
    },
    {
        'regex': r'^mol ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'mol_{}'.format(match.group(2)),
            'id': lambda match, i_group: 'initial_count_species_{}'.format(re.sub(r'[^a-zA-Z0-9_]', '_', match.group(2))),
            'name': lambda match, i_group: 'Initial count of species "{}"'.format(match.group(2)),
            'target': lambda match: 'mol {}'.format(match.group(2)),
            'new_value': lambda match: match.group(1),
        },
    },
    {
        'regex': r'^compartment_mol ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'compartment_mol_{}'.format(match.group(2)),
            'id': lambda match, i_group: 'initial_count_species_{}'.format(re.sub(r'[^a-zA-Z0-9_]', '_', match.group(2))),
            'name': lambda match, i_group: 'Initial count of species "{}"'.format(match.group(2)),
            'target': lambda match: 'compartment_mol {}'.format(match.group(2)),
            'new_value': lambda match: match.group(1),
        },
    },
    {
        'regex': r'^surface_mol ([^ ]+) (.*?)$',
        'parameter': {
            'group': lambda match: 'surface_mol_{}'.format(match.group(2)),
            'id': lambda match, i_group: 'initial_count_species_{}'.format(re.sub(r'[^a-zA-Z0-9_]', '_', match.group(2))),
            'name': lambda match, i_group: 'Initial count of species "{}"'.format(match.group(2)),
            'target': lambda match: 'surface_mol {}'.format(match.group(2)),
            'new_value': lambda match: match.group(1),
        },
    },
]


def get_parameters_variables_for_simulation(model_filename, model_language, simulation_type, algorithm,
                                            include_compartment_sizes_in_simulation_variables=False,
                                            include_model_parameters_in_simulation_variables=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm (:obj:`str`): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        include_compartment_sizes_in_simulation_variables (:obj:`bool`, optional): whether to include the sizes of
            non-constant SBML compartments with assignment rules among the returned SED variables
        include_model_parameters_in_simulation_variables (:obj:`bool`, optional): whether to include the values of
            non-constant SBML parameters with assignment rules among the returned SED variables

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
    """
    # check model file exists and is valid
    if not isinstance(model_filename, str):
        raise ValueError('`{}` is not a path to a model file.'.format(model_filename))

    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist.'.format(model_filename))

    errors, _, (model, model_config) = validate_model(model_filename)
    if errors:
        raise ValueError('Model file `{}` is not a valid BNGL or BNGL XML file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    # get parameters and observables
    params = []
    param_group_counts = {}
    for line in model_config:
        param = _parse_configuration_line(line, param_group_counts)
        if param:
            params.append(param)

    vars = []
    vars.append(Variable(
        id='time',
        name='Time',
        symbol=Symbol.time.value,
    ))
    species_names = _get_species_names(model_config)
    compartment_names = _get_compartment_names(model_config)
    surface_names = _get_surface_names(model_config)
    for species_name in species_names:
        vars.append(Variable(
            id='count_species_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species_name)),
            name='Count of species "{}"'.format(species_name),
            target="molcount {}".format(species_name),
        ))
        for compartment_name in compartment_names:
            vars.append(Variable(
                id='count_species_{}_compartment_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species_name), compartment_name),
                name='Count of species "{}" in compartment "{}"'.format(species_name, compartment_name),
                target="molcountincmpt {} {}".format(species_name, compartment_name),
            ))
        for surface_name in surface_names:
            vars.append(Variable(
                id='count_species_{}_surface_{}'.format(re.sub('[^a-zA-Z0-9_]', '_', species_name), surface_name),
                name='Count of species "{}" in surface "{}"'.format(species_name, surface_name),
                target="molcountonsurf {} {}".format(species_name, surface_name),
            ))

    return (params, vars)


def _get_species_names(config):
    species_names = []

    for line in config:
        # remove comments
        line = line.partition('#')[0].strip()

        # remove consecutive spaces
        line = re.sub(' +', ' ', line)

        if line.startswith('species '):
            species_names.extend(line.split(' ')[1:])

    return species_names


def _get_compartment_names(config):
    comp_names = []

    for line in config:
        # remove comments
        line = line.partition('#')[0].strip()

        # remove consecutive spaces
        line = re.sub(' +', ' ', line)

        if line.startswith('start_compartment '):
            comp_names.append(line.partition(' ')[2])

    return comp_names


def _get_surface_names(config):
    surface_names = []

    for line in config:
        # remove comments
        line = line.partition('#')[0].strip()

        # remove consecutive spaces
        line = re.sub(' +', ' ', line)

        if line.startswith('start_surface '):
            surface_names.append(line.partition(' ')[2])

    return surface_names


def _parse_configuration_line(line, param_group_counts):
    # remove comments
    line = line.partition('#')[0].strip()

    # remove consecutive spaces
    line = re.sub(' +', ' ', line)

    param = None

    for pattern in CONFIG_DECLARATION_PATTERNS:
        match = re.match(pattern['regex'], line)
        if match:
            if pattern.get('parameter', None):
                group = pattern['parameter']['group'](match)
                if group not in param_group_counts:
                    param_group_counts[group] = -1
                param_group_counts[group] += 1
                i_group = param_group_counts[group]

                param = ModelAttributeChange(
                    id=pattern['parameter']['id'](match, i_group),
                    name=pattern['parameter']['name'](match, i_group),
                    target=pattern['parameter']['target'](match),
                    new_value=pattern['parameter']['new_value'](match),
                )

            break

    return param
