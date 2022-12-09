""" Utilities for working with CellML models

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...config import Config  # noqa: F401
from ...sedml.data_model import (  # noqa: F401
    SedDocument, ModelAttributeChange, Variable, Symbol,
    Simulation, OneStepSimulation, UniformTimeCourseSimulation,
    Algorithm, Task,
    )
from ...utils.core import flatten_nested_list_of_strings
from .validation import validate_model
import libcellml  # noqa: F401
import lxml  # noqa: F401
import os
import types  # noqa: F401

__all__ = ['get_parameters_variables_outputs_for_simulation']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    change_level=SedDocument, native_ids=False, native_data_types=False, observable_only=False,
                                                    config=None):
    """ Get the possible observables for a simulation of a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:cellml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        change_level (:obj:`types.Type`, optional): level at which model changes will be made (:obj:`SedDocument` or :obj:`Task`)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types
        observable_only (:obj:`bool`, optional): whether to skip the variables that are not exposed by OpenCor
        config (:obj:`Config`, optional): whether to fail on missing includes

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulation of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model
    """
    # check model file exists
    if not isinstance(model_filename, str):
        raise ValueError('`{}` is not a path to a model file.'.format(model_filename))

    if not os.path.isfile(model_filename):
        raise FileNotFoundError('Model file `{}` does not exist.'.format(model_filename))

    errors, _, (model, root) = validate_model(model_filename, resolve_imports=False, config=config)
    if errors:
        raise ValueError('Model file `{}` is not a valid CellML file.\n  {}'.format(
            model_filename, flatten_nested_list_of_strings(errors).replace('\n', '\n  ')))

    if simulation_type not in [OneStepSimulation, UniformTimeCourseSimulation]:
        raise NotImplementedError('`simulation_type` must be `OneStepSimulation` or `UniformTimeCourseSimulation`')

    default_ns = root.nsmap.get(None, '')
    if (
        default_ns.startswith('http://www.cellml.org/cellml/1.0')
        or default_ns.startswith('http://www.cellml.org/cellml/1.1')
    ):
        return get_parameters_variables_for_simulation_version_1(model, root, simulation_type, algorithm_kisao_id=algorithm_kisao_id,
                                                                 native_ids=native_ids, native_data_types=native_data_types,
                                                                 observable_only=observable_only)

    else:
        return get_parameters_variables_for_simulation_version_2(model, root, simulation_type, algorithm_kisao_id=algorithm_kisao_id,
                                                                 native_ids=native_ids, native_data_types=native_data_types)


def get_parameters_variables_for_simulation_version_1(model, xml_root, simulation_type,
                                                      algorithm_kisao_id=None, native_ids=False, native_data_types=False, observable_only=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model (:obj:`None`): model
        xml_root (:obj:`lxml.etree._Element`): element tree for model
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types
        observable_only (:obj:`bool`, optional): whether to skip the variables that are not exposed by OpenCor

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulation of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model
    """
    params = []
    if simulation_type == UniformTimeCourseSimulation:
        sim = UniformTimeCourseSimulation(
            id='simulation',
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1.,
            number_of_steps=10,
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id or 'KISAO_0000019',
            ),
        )
    else:
        sim = OneStepSimulation(
            id='simulation',
            step=1.,
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id or 'KISAO_0000019',
            ),
        )

    vars = []

    namespaces = {
        'cellml': xml_root.nsmap.get(None, '')
    }

    for component in xml_root.xpath('/cellml:model/cellml:component', namespaces=namespaces):
        component_name = component.attrib['name']
        for variable in component.xpath('cellml:variable', namespaces=namespaces):
            variable_name = variable.attrib['name']
            public_interface_in = variable.attrib.get('public_interface', None) == 'in'
            private_interface_in = variable.attrib.get('private_interface', None) == 'in'
            variable_is_hidden = private_interface_in or public_interface_in

            if variable_is_hidden and observable_only:
                continue
            initial_value = variable.attrib.get('initial_value', None)
            if initial_value is not None:
                params.append(ModelAttributeChange(
                    id='{}.{}'.format(component_name, variable_name) if native_ids else 'initial_value_component_{}_variable_{}'.format(
                        component_name, variable_name),
                    name=None if native_ids else 'Initial value of variable "{}" of component "{}"'.format(
                        variable_name, component_name),
                    target="/cellml:model/cellml:component[@name='{}']/cellml:variable[@name='{}']/@initial_value".format(
                        component_name, variable_name),
                    target_namespaces=namespaces,
                    new_value=float(initial_value) if native_data_types else initial_value,
                ))

            vars.append(Variable(
                id='{}.{}'.format(component_name, variable_name) if native_ids else 'value_component_{}_variable_{}'.format(
                    component_name, variable_name),
                name=None if native_ids else 'Value of variable "{}" of component "{}"'.format(
                    variable_name, component_name),
                target="/cellml:model/cellml:component[@name='{}']/cellml:variable[@name='{}']".format(
                    component_name, variable_name),
                target_namespaces=namespaces,
            ))
    return params, [sim], vars, []


def get_parameters_variables_for_simulation_version_2(model, xml_root, simulation_type,
                                                      algorithm_kisao_id=None, native_ids=False, native_data_types=False):
    """ Get the possible observables for a simulation of a model

    Args:
        model (:obj:`libcellml.model.Model`): model
        xml_root (:obj:`lxml.etree._Element`): element tree for model
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulation of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model
    """
    namespaces = {
        'cellml': xml_root.nsmap.get(None, '')
    }

    params = []
    if simulation_type == UniformTimeCourseSimulation:
        sim = UniformTimeCourseSimulation(
            id='simulation',
            initial_time=0.,
            output_start_time=0.,
            output_end_time=1.,
            number_of_steps=10,
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id or 'KISAO_0000019',
            ),
        )
    else:
        sim = OneStepSimulation(
            id='simulation',
            step=1.,
            algorithm=Algorithm(
                kisao_id=algorithm_kisao_id or 'KISAO_0000019',
            ),
        )
    vars = []

    for i_component in range(model.componentCount()):
        component = model.component(i_component)
        component_name = component.name()
        for i_variable in range(component.variableCount()):
            variable = component.variable(i_variable)

            variable_name = variable.name()
            initial_value = variable.initialValue()
            if initial_value:
                params.append(ModelAttributeChange(
                    id='{}.{}'.format(component_name, variable_name) if native_ids else 'initial_value_component_{}_variable_{}'.format(
                        component_name, variable_name),
                    name=None if native_ids else 'Initial value of variable "{}" of component "{}"'.format(
                        variable_name, component_name),
                    target="/cellml:model/cellml:component[@name='{}']/cellml:variable[@name='{}']/@initial_value".format(
                        component_name, variable_name),
                    target_namespaces=namespaces,
                    new_value=float(initial_value) if native_data_types else initial_value,
                ))

            vars.append(Variable(
                id='{}.{}'.format(component_name, variable_name) if native_ids else 'value_component_{}_variable_{}'.format(
                    component_name, variable_name),
                name=None if native_ids else 'Value of variable "{}" of component "{}"'.format(
                    variable_name, component_name),
                target="/cellml:model/cellml:component[@name='{}']/cellml:variable[@name='{}']".format(
                    component_name, variable_name),
                target_namespaces=namespaces,
            ))
    return params, [sim], vars, []
