""" Utilities for reading and writing SED documents to SED-ML files

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from . import data_model
from .utils import add_namespaces_to_xml_node, convert_xml_node_to_string, get_namespaces_for_sed_object
from .validation import validate_doc
from .warnings import SedmlFeatureNotSupportedWarning
from ..biosimulations.data_model import Metadata, ExternalReferences, Citation
from ..data_model import Person, Identifier, OntologyTerm
from ..kisao.utils import normalize_kisao_id
from ..warnings import warn, BioSimulatorsWarning
from ..utils.core import flatten_nested_list_of_strings
from xml.sax import saxutils
import dateutil.parser
import enum
import libsedml
import os

__all__ = [
    'SedmlSimulationReader',
    'SedmlSimulationWriter',
]


class SedmlSimulationWriter(object):
    """ SED-ML writer

    Attributes:
        _num_meta_id (:obj:`int`): number of assigned meta ids
        _doc_sed (:obj:`libsedml.SedDocument`): SED document
        _obj_to_sed_obj_map (:obj:`object` => :obj:`object`): map from data model objects to their corresponding libSED-ML objects
    """

    def __init__(self):
        self._num_meta_id = None
        self._doc_sed = None
        self._obj_to_sed_obj_map = None

    def run(self, doc, filename, validate_semantics=True, validate_models_with_languages=True):
        """ Save a SED document to an SED-ML XML file

        Args:
            doc (:obj:`data_model.SedDocument`): SED document
            filename (:obj:`str`): Path to save simulation experiment in SED-ML format
            validate_semantics (:obj:`bool`, optional): if :obj:`True`, check that SED-ML is semantically valid
            validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

        Raises:
            :obj:`NotImplementedError`: document uses an supported type of task or output
        """
        errors, warnings = validate_doc(doc, working_dir=os.path.dirname(
            filename), validate_semantics=validate_semantics, validate_models_with_languages=validate_models_with_languages)
        if warnings:
            msg = 'The SED document is potentially incorrect.\n  {}'.format(flatten_nested_list_of_strings(warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)
        if errors:
            msg = 'The SED document is invalid.\n  {}'.format(flatten_nested_list_of_strings(errors).replace('\n', '\n  '))
            raise ValueError(msg)

        self._num_meta_id = 0
        self._obj_to_sed_obj_map = {}

        self._create_doc(doc)
        self._add_metadata_to_obj(doc)

        for model in doc.models:
            self._add_model_to_doc(model)

        for sim in doc.simulations:
            self._add_sim_to_doc(sim)

        for task in doc.tasks:
            if isinstance(task, data_model.Task):
                self._add_task_to_doc(task)

            elif isinstance(task, data_model.RepeatedTask):
                self._add_repeated_task_to_doc(task)

            else:
                raise NotImplementedError('Task type {} is not supported.'.format(task.__class__.__name__))

        for data_gen in doc.data_generators:
            self._add_data_gen_to_doc(data_gen)

        for output in doc.outputs:
            if isinstance(output, data_model.Report):
                self._add_report_to_doc(output)
            elif isinstance(output, data_model.Plot2D):
                self._add_plot2d_to_doc(output)
            elif isinstance(output, data_model.Plot3D):
                self._add_plot3d_to_doc(output)
            else:
                raise NotImplementedError('Output type {} is not supported.'.format(output.__class__.__name__))

        self._export_doc(filename)

    def _create_doc(self, doc):
        """ Create a SED document

        Args:
            doc (:obj:`data_model.SedDocument`): SED document
        """
        doc_sed = self._doc_sed = libsedml.SedDocument()
        self._doc_sed = doc_sed
        self._obj_to_sed_obj_map[doc] = doc_sed
        if doc.level is not None:
            self._call_libsedml_method(doc_sed, 'setLevel', doc.level)
        if doc.version is not None:
            self._call_libsedml_method(doc_sed, 'setVersion', doc.version)

    def _add_model_to_doc(self, model):
        """ Add a model to a SED document

        Args:
            model (:obj:`data_model.Model`): model
        """
        model_sed = self._doc_sed.createModel()
        self._obj_to_sed_obj_map[model] = model_sed
        if model.id is not None:
            self._call_libsedml_method(model_sed, 'setId', model.id)
        if model.name is not None:
            self._call_libsedml_method(model_sed, 'setName', model.name)
        if model.source is not None:
            self._call_libsedml_method(model_sed, 'setSource', model.source)
        if model.language is not None:
            self._call_libsedml_method(model_sed, 'setLanguage', model.language)
        for change in model.changes:
            if isinstance(change, data_model.ModelAttributeChange):
                self._add_attribute_change_to_model(model, change)

            elif isinstance(change, data_model.AddElementModelChange):
                self._add_add_model_element_to_model(model, change)

            elif isinstance(change, data_model.ReplaceElementModelChange):
                self._add_change_model_element_to_model(model, change)

            elif isinstance(change, data_model.RemoveElementModelChange):
                self._add_remove_model_element_to_model(model, change)

            elif isinstance(change, data_model.ComputeModelChange):
                self._add_compute_change_to_model(model, change)

            else:
                raise NotImplementedError('Model change type {} is not supported.'.format(change.__class__.__name__))

    def _add_attribute_change_to_model(self, model, change):
        """ Add an attribute change change to a SED model

        Args:
            model (:obj:`data_model.Model`): model
            change (:obj:`data_model.ModelAttributeChange`): model attribute change

        Returns:
            :obj:`libsedml.SedChangeAttribute`
        """
        model_sed = self._obj_to_sed_obj_map[model]
        change_sed = model_sed.createChangeAttribute()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
            self._add_namespaces_to_obj(change_sed, change.target_namespaces)
        if change.new_value is not None:
            self._call_libsedml_method(change_sed, 'setNewValue', change.new_value)

        return change_sed

    def _add_add_model_element_to_model(self, model, change):
        """ Add an add element change change to a SED model

        Args:
            model (:obj:`data_model.Model`): model
            change (:obj:`data_model.ModelAttributeChange`): add model element change

        Returns:
            :obj:`libsedml.SedAddXML`
        """
        model_sed = self._obj_to_sed_obj_map[model]
        change_sed = model_sed.createAddXML()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
            self._add_namespaces_to_obj(change_sed, change.target_namespaces)
        if change.new_elements is not None:
            new_xml = libsedml.XMLNode_convertStringToXMLNode(change.new_elements)
            if new_xml is None:
                raise ValueError('`{}` is invalid XML.'.format(change.new_elements))
            self._call_libsedml_method(change_sed, 'setNewXML', new_xml)

        return change_sed

    def _add_change_model_element_to_model(self, model, change):
        """ Add a change element change to a SED model

        Args:
            model (:obj:`data_model.Model`): model
            change (:obj:`data_model.ReplaceElementModelChange`): change model element change

        Returns:
            :obj:`libsedml.SedChangeXML`
        """
        model_sed = self._obj_to_sed_obj_map[model]
        change_sed = model_sed.createChangeXML()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
            self._add_namespaces_to_obj(change_sed, change.target_namespaces)
        if change.new_elements is not None:
            new_xml = libsedml.XMLNode_convertStringToXMLNode(change.new_elements)
            if new_xml is None:
                raise ValueError('`{}` is invalid XML.'.format(change.new_elements))
            self._call_libsedml_method(change_sed, 'setNewXML', new_xml)

        return change_sed

    def _add_remove_model_element_to_model(self, model, change):
        """ Add a remove element change to a SED model

        Args:
            model (:obj:`data_model.Model`): model
            change (:obj:`data_model.RemoveElementModelChange`): remove model element change

        Returns:
            :obj:`libsedml.SedRemoveXML`
        """
        model_sed = self._obj_to_sed_obj_map[model]
        change_sed = model_sed.createRemoveXML()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
            self._add_namespaces_to_obj(change_sed, change.target_namespaces)

        return change_sed

    def _add_compute_change_to_model(self, model, change):
        """ Add a compute change to a SED model

        Args:
            model (:obj:`data_model.Model`): model
            change (:obj:`data_model.ComputeModelChange`): compute change

        Returns:
            :obj:`libsedml.SedComputeChange`
        """
        model_sed = self._obj_to_sed_obj_map[model]
        change_sed = model_sed.createComputeChange()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
            self._add_namespaces_to_obj(change_sed, change.target_namespaces)

        for param in change.parameters:
            self._add_param_to_obj(change, param)

        for var in change.variables:
            self._add_var_to_obj(change, var)

        if change.math is not None:
            self._call_libsedml_method(change_sed, 'setMath', libsedml.parseFormula(change.math))

        return change_sed

    def _add_sim_to_doc(self, sim):
        """ Add a simulation to a SED document

        Args:
            sim (:obj:`data_model.Simulation`): simulation experiment
        """
        if isinstance(sim, data_model.SteadyStateSimulation):
            sim_sed = self._doc_sed.createSteadyState()
        elif isinstance(sim, data_model.OneStepSimulation):
            sim_sed = self._doc_sed.createOneStep()
            if sim.step is not None:
                self._call_libsedml_method(sim_sed, 'setStep', sim.step)
        elif isinstance(sim, data_model.UniformTimeCourseSimulation):
            sim_sed = self._doc_sed.createUniformTimeCourse()
            if sim.initial_time is not None:
                self._call_libsedml_method(sim_sed, 'setInitialTime', sim.initial_time)
            if sim.output_start_time is not None:
                self._call_libsedml_method(sim_sed, 'setOutputStartTime', sim.output_start_time)
            if sim.output_end_time is not None:
                self._call_libsedml_method(sim_sed, 'setOutputEndTime', sim.output_end_time)
            if sim.number_of_steps is not None:
                self._call_libsedml_method(sim_sed, 'setNumberOfSteps', sim.number_of_steps)
        else:  # pragma: no cover # unreachable due to earlier validation
            raise NotImplementedError('Simulation type {} is not supported.'.format(sim.__class__.__name__))

        self._obj_to_sed_obj_map[sim] = sim_sed

        if sim.id is not None:
            self._call_libsedml_method(sim_sed, 'setId', sim.id)
        if sim.name is not None:
            self._call_libsedml_method(sim_sed, 'setName', sim.name)
        if sim.algorithm is not None:
            self._add_algorithm_to_sim(sim, sim.algorithm)

    def _add_algorithm_to_sim(self, sim, alg):
        """ Add a simulation algorithm to a SED document

        Args:
            sim (:obj:`data_model.Simulation`): simulation
            alg (:obj:`data_model.Algorithm`): simulation algorithm
        """
        sim_sed = self._obj_to_sed_obj_map[sim]
        alg_sed = sim_sed.createAlgorithm()
        self._obj_to_sed_obj_map[alg] = alg_sed

        if alg.kisao_id is not None:
            self._set_kisao_id(alg)

        for change in alg.changes:
            if change.new_value is not None:
                self._add_param_change_to_alg(alg, change)

    def _add_param_change_to_alg(self, alg, change):
        """ Add simulation algorithm parameter change to a SED document

        Args:
            alg (:obj:`data_model.Algorithm`): SED simulation algorithm
            change (:obj:`data_model.AlgorithmParameterChange`): simulation algorithm parameter change
        """
        alg_sed = self._obj_to_sed_obj_map[alg]
        change_sed = alg_sed.createAlgorithmParameter()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.kisao_id is not None:
            self._set_kisao_id(change)

        if change.new_value is not None:
            self._call_libsedml_method(change_sed, 'setValue', change.new_value)

    def _set_kisao_id(self, obj):
        """ Set the KiSAO id of a SED object

        Args:
            obj (:obj:`data_model.Algorithm` or :obj:`data_model.AlgorithmParameterChange`): SED object
        """
        obj_sed = self._obj_to_sed_obj_map[obj]
        self._call_libsedml_method(obj_sed, 'setKisaoID', obj.kisao_id.replace('_', ':'))

    def _add_task_to_doc(self, task):
        """ Add a task to a SED document

        Args:
            task (:obj:`data_model.Task`): task

        Raises:
            :obj:`ValueError`: if the referenced model or simulation doesn't have an id
        """
        task_sed = self._doc_sed.createTask()
        self._obj_to_sed_obj_map[task] = task_sed

        if task.id is not None:
            self._call_libsedml_method(task_sed, 'setId', task.id)

        if task.name is not None:
            self._call_libsedml_method(task_sed, 'setName', task.name)

        if task.model is not None:
            if not task.model.id:  # pragma: no cover: already validated
                raise ValueError('Model must have an id to be referenced')
            self._call_libsedml_method(task_sed, 'setModelReference', task.model.id)

        if task.simulation is not None:
            if not task.simulation.id:  # pragma: no cover: already validated
                raise ValueError('Simulation must have an id to be referenced')
            self._call_libsedml_method(task_sed, 'setSimulationReference', task.simulation.id)

    def _add_repeated_task_to_doc(self, task):
        """ Add a repeated task to a SED document

        Args:
            task (:obj:`data_model.RepeatedTask`): task

        Raises:
            :obj:`ValueError`: if the referenced range doesn't have an id
        """
        task_sed = self._doc_sed.createRepeatedTask()
        self._obj_to_sed_obj_map[task] = task_sed

        if task.id is not None:
            self._call_libsedml_method(task_sed, 'setId', task.id)

        if task.name is not None:
            self._call_libsedml_method(task_sed, 'setName', task.name)

        if task.reset_model_for_each_iteration is not None:
            self._call_libsedml_method(task_sed, 'setResetModel', task.reset_model_for_each_iteration)

        if task.range is not None:
            if not task.range.id:  # pragma: no cover: already validated
                raise ValueError('Range must have an id to be referenced')
            self._call_libsedml_method(task_sed, 'setRangeId', task.range.id)

        for change in task.changes:
            self._add_set_value_model_change_to_repeated_task(task, change)

        for sub_task in task.sub_tasks:
            self._add_sub_task_to_repeated_task(task, sub_task)

        for range_obj in task.ranges:
            self._add_range_to_repeated_task(task, range_obj)

    def _add_set_value_model_change_to_repeated_task(self, task, change):
        """ Add a set value change to a repeated task

        Args:
            task (:obj:`data_model.RepeatedTask`): task
            change (:obj:`data_model.SetValueComputeModelChange`): change

        Raises:
            :obj:`ValueError`: if the referenced model or range doesn't have an id
        """
        task_sed = self._obj_to_sed_obj_map[task]

        change_sed = task_sed.createTaskChange()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
            self._add_namespaces_to_obj(change_sed, change.target_namespaces)

        for param in change.parameters:
            self._add_param_to_obj(change, param)

        for var in change.variables:
            self._add_var_to_obj(change, var)

        if change.math is not None:
            self._call_libsedml_method(change_sed, 'setMath', libsedml.parseFormula(change.math))

        if change.model is not None:
            if not change.model.id:  # pragma: no cover: already validated
                raise ValueError('Model must have an id to be referenced')
            self._call_libsedml_method(change_sed, 'setModelReference', change.model.id)

        if change.range is not None:
            if not change.range.id:  # pragma: no cover: already validated
                raise ValueError('Range must have an id to be referenced')
            self._call_libsedml_method(change_sed, 'setRange', change.range.id)

        if change.symbol is not None:
            self._call_libsedml_method(change_sed, 'setSymbol', change.symbol)

    def _add_sub_task_to_repeated_task(self, task, sub_task):
        """ Add a sub-task to a repeated task

        Args:
            task (:obj:`data_model.RepeatedTask`): task
            sub_task (:obj:`data_model.SubTask`): sub-task

        Raises:
            :obj:`ValueError`: if the referenced task doesn't have an id
        """
        task_sed = self._obj_to_sed_obj_map[task]

        sub_task_sed = task_sed.createSubTask()
        self._obj_to_sed_obj_map[sub_task] = sub_task_sed

        if sub_task.task is not None:
            if not sub_task.task.id:  # pragma: no cover: already validated
                raise ValueError('Task must have an id to be referenced')
            self._call_libsedml_method(sub_task_sed, 'setTask', sub_task.task.id)

        if sub_task.order is not None:
            self._call_libsedml_method(sub_task_sed, 'setOrder', sub_task.order)

    def _add_range_to_repeated_task(self, task, range_obj):
        """ Add a range to a repeated task

        Args:
            task (:obj:`data_model.RepeatedTask`): task
            sub_task (:obj:`data_model.Range`): range

        Raises:
            :obj:`ValueError`: if the referenced range doesn't have an id
        """
        task_sed = self._obj_to_sed_obj_map[task]

        if isinstance(range_obj, data_model.UniformRange):
            range_sed = task_sed.createUniformRange()
            self._obj_to_sed_obj_map[range_obj] = range_sed

            if range_obj.start is not None:
                self._call_libsedml_method(range_sed, 'setStart', range_obj.start)

            if range_obj.end is not None:
                self._call_libsedml_method(range_sed, 'setEnd', range_obj.end)

            if range_obj.number_of_steps is not None:
                self._call_libsedml_method(range_sed, 'setNumberOfSteps', range_obj.number_of_steps)

            if range_obj.type is not None:
                self._call_libsedml_method(range_sed, 'setType', range_obj.type.value)

        elif isinstance(range_obj, data_model.VectorRange):
            range_sed = task_sed.createVectorRange()
            self._obj_to_sed_obj_map[range_obj] = range_sed

            for value in range_obj.values:
                self._call_libsedml_method(range_sed, 'setValues', tuple(range_obj.values))

        elif isinstance(range_obj, data_model.FunctionalRange):
            range_sed = task_sed.createFunctionalRange()
            self._obj_to_sed_obj_map[range_obj] = range_sed

            if range_obj.range is not None:
                if not range_obj.range.id:  # pragma: no cover: already validated
                    raise ValueError('Range must have an id to be referenced')
                self._call_libsedml_method(range_sed, 'setRange', range_obj.range.id)

            for param in range_obj.parameters:
                self._add_param_to_obj(range_obj, param)

            for var in range_obj.variables:
                self._add_var_to_obj(range_obj, var)

            if range_obj.math is not None:
                self._call_libsedml_method(range_sed, 'setMath', libsedml.parseFormula(range_obj.math))

        else:
            raise NotImplementedError('Range type {} is not supported.'.format(range_obj.__class__.__name__))

        if range_obj.id is not None:
            self._call_libsedml_method(range_sed, 'setId', range_obj.id)

    def _add_data_gen_to_doc(self, data_gen):
        """ Add a data generator to a SED document

        Args:
            data_gen (:obj:`data_model.DataGenerator`): data generator
        """
        data_gen_sed = self._doc_sed.createDataGenerator()
        self._obj_to_sed_obj_map[data_gen] = data_gen_sed

        if data_gen.id is not None:
            self._call_libsedml_method(data_gen_sed, 'setId', data_gen.id)

        if data_gen.name is not None:
            self._call_libsedml_method(data_gen_sed, 'setName', data_gen.name)

        for param in data_gen.parameters:
            self._add_param_to_obj(data_gen, param)

        for var in data_gen.variables:
            self._add_var_to_obj(data_gen, var)

        if data_gen.math is not None:
            self._call_libsedml_method(data_gen_sed, 'setMath', libsedml.parseFormula(data_gen.math))

    def _add_param_to_obj(self, obj, param):
        """ Add a parameter to a SED object

        Args:
            obj (:obj:`data_model.ComputeModelChange`, :obj:`data_model.DataGenerator`):
                compute change, data generator, functional range or set value
            param (:obj:`data_model.Parameter`): parameter
        """
        obj_sed = self._obj_to_sed_obj_map[obj]
        param_sed = obj_sed.createParameter()
        self._obj_to_sed_obj_map[param] = param_sed

        if param.id is not None:
            self._call_libsedml_method(param_sed, 'setId', param.id)

        if param.name is not None:
            self._call_libsedml_method(param_sed, 'setName', param.name)

        if param.value is not None:
            self._call_libsedml_method(param_sed, 'setValue', param.value)

    def _add_var_to_obj(self, obj, var):
        """ Add a variable to a SED object

        Args:
            obj (:obj:`data_model.ComputeModelChange`, :obj:`data_model.DataGenerator`):
                compute change, data generator, functional range or set value
            var (:obj:`data_model.Variable`): variable
        """
        obj_sed = self._obj_to_sed_obj_map[obj]
        var_sed = obj_sed.createVariable()
        self._obj_to_sed_obj_map[var] = var_sed

        if var.id is not None:
            self._call_libsedml_method(var_sed, 'setId', var.id)

        if var.name is not None:
            self._call_libsedml_method(var_sed, 'setName', var.name)

        if var.symbol is not None:
            self._call_libsedml_method(var_sed, 'setSymbol', var.symbol)

        if var.target is not None:
            self._call_libsedml_method(var_sed, 'setTarget', var.target)
            self._add_namespaces_to_obj(var_sed, var.target_namespaces)

        if var.task is not None:
            if not var.task.id:  # pragma: no cover: already validated
                raise ValueError('Task must have an id to be referenced')
            self._call_libsedml_method(var_sed, 'setTaskReference', var.task.id)

        if var.model is not None:
            if not var.model.id:  # pragma: no cover: already validated
                raise ValueError('Model must have an id to be referenced')
            self._call_libsedml_method(var_sed, 'setModelReference', var.model.id)

    def _add_report_to_doc(self, report):
        """ Add a report to a SED document

        Args:
            report (:obj:`data_model.Report`): report
        """
        report_sed = self._doc_sed.createReport()
        self._obj_to_sed_obj_map[report] = report_sed

        if report.id is not None:
            self._call_libsedml_method(report_sed, 'setId', report.id)

        if report.name is not None:
            self._call_libsedml_method(report_sed, 'setName', report.name)

        for data_set in report.data_sets:
            dataset_sed = report_sed.createDataSet()
            self._obj_to_sed_obj_map[data_set] = dataset_sed

            if data_set.id is not None:
                self._call_libsedml_method(dataset_sed, 'setId', data_set.id)
            if data_set.name is not None:
                self._call_libsedml_method(dataset_sed, 'setName', data_set.name)
            if data_set.label is not None:
                self._call_libsedml_method(dataset_sed, 'setLabel', data_set.label)
            if data_set.data_generator is not None:
                if not data_set.data_generator.id:  # pragma: no cover: already validated
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(dataset_sed, 'setDataReference', data_set.data_generator.id)

    def _add_plot2d_to_doc(self, plot):
        """ Add a 2D plot to a SED document

        Args:
            plot (:obj:`data_model.Plot2D`): 2D plot
        """
        plot_sed = self._doc_sed.createPlot2D()
        self._obj_to_sed_obj_map[plot] = plot_sed

        if plot.id is not None:
            self._call_libsedml_method(plot_sed, 'setId', plot.id)

        if plot.name is not None:
            self._call_libsedml_method(plot_sed, 'setName', plot.name)

        for curve in plot.curves:
            curve_sed = plot_sed.createCurve()
            self._obj_to_sed_obj_map[curve] = curve_sed

            if curve.id is not None:
                self._call_libsedml_method(curve_sed, 'setId', curve.id)

            if curve.name is not None:
                self._call_libsedml_method(curve_sed, 'setName', curve.name)

            self._set_axis_scale(curve, 'x')
            self._set_axis_scale(curve, 'y')

            if curve.x_data_generator is not None:
                if not curve.x_data_generator.id:  # pragma: no cover: already validated
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(curve_sed, 'setXDataReference', curve.x_data_generator.id)

            if curve.y_data_generator is not None:
                if not curve.y_data_generator.id:  # pragma: no cover: already validated
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(curve_sed, 'setYDataReference', curve.y_data_generator.id)

    def _add_plot3d_to_doc(self, plot):
        """ Add a 3D plot to a SED document

        Args:
            plot (:obj:`data_model.Plot3D`): 3D plot
        """
        plot_sed = self._doc_sed.createPlot3D()
        self._obj_to_sed_obj_map[plot] = plot_sed

        if plot.id is not None:
            self._call_libsedml_method(plot_sed, 'setId', plot.id)

        if plot.name is not None:
            self._call_libsedml_method(plot_sed, 'setName', plot.name)

        for surface in plot.surfaces:
            surface_sed = plot_sed.createSurface()
            self._obj_to_sed_obj_map[surface] = surface_sed

            if surface.id is not None:
                self._call_libsedml_method(surface_sed, 'setId', surface.id)

            if surface.name is not None:
                self._call_libsedml_method(surface_sed, 'setName', surface.name)

            self._set_axis_scale(surface, 'x')
            self._set_axis_scale(surface, 'y')
            self._set_axis_scale(surface, 'z')

            if surface.x_data_generator is not None:
                if not surface.x_data_generator.id:  # pragma: no cover: already validated
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(surface_sed, 'setXDataReference', surface.x_data_generator.id)

            if surface.y_data_generator is not None:
                if not surface.y_data_generator.id:  # pragma: no cover: already validated
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(surface_sed, 'setYDataReference', surface.y_data_generator.id)

            if surface.z_data_generator is not None:
                if not surface.z_data_generator.id:  # pragma: no cover: already validated
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(surface_sed, 'setZDataReference', surface.z_data_generator.id)

    def _set_axis_scale(self, obj, axis):
        """ Set the scale of an axis of a curve of surface

        Args:
            obj (:obj:`data_model.Curve` or :obj:`data_model.Surface`): plot
            axis (:obj:`str`): axis (`x`, `y`, or `z`)
        """
        obj_sed = self._obj_to_sed_obj_map[obj]
        axis_scale = getattr(obj, axis.lower() + '_scale')
        if axis_scale == data_model.AxisScale.linear:
            self._call_libsedml_method(obj_sed, 'setLog' + axis.upper(), False)
        elif axis_scale == data_model.AxisScale.log:
            self._call_libsedml_method(obj_sed, 'setLog' + axis.upper(), True)
        else:
            # this is an error rather than a warning because SED doesn't define any other types of scales
            raise NotImplementedError('Axis scale type {} is not supported.'.format(axis_scale))

    def _export_doc(self, filename):
        """ Export a SED document to an XML file

        Args:
            filename (:obj:`str`): path to save document in XML format
        """
        # save the SED document to a file
        libsedml.writeSedML(self._doc_sed, filename)

    def _add_metadata_to_obj(self, obj):
        """ Add the metadata about a resource to the annotation of a SED object

        * Name
        * Authors
        * Description
        * Tags
        * References
        * License

        Args:
            obj (:obj:`object`): object
        """
        if not obj.metadata:
            return

        obj_sed = self._obj_to_sed_obj_map[obj]

        metadata = []
        namespaces = set()

        if obj.metadata.description:
            metadata.append(XmlNode(
                prefix='dc',
                name='description',
                type='description',
                children=obj.metadata.description,
            ))
            namespaces.add('dc')

        if obj.metadata.tags:
            metadata.append(
                XmlNode(prefix='dc', name='description', type='tags', children=[
                    XmlNode(prefix='rdf', name='Bag', children=[
                        XmlNode(prefix='rdf', name='li', children=[
                            XmlNode(prefix='rdf', name='value', children=tag)
                        ]) for tag in obj.metadata.tags
                    ])
                ]))
            namespaces.add('dc')
            namespaces.add('rdf')

        if obj.metadata.authors:
            authors_xml = []
            for author in obj.metadata.authors:
                names_xml = []
                if author.given_name:
                    names_xml.append(XmlNode(prefix='vcard', name='Given', children=author.given_name))
                if author.other_name:
                    names_xml.append(XmlNode(prefix='vcard', name='Other', children=author.other_name))
                if author.family_name:
                    names_xml.append(XmlNode(prefix='vcard', name='Family', children=author.family_name))

                authors_xml.append(XmlNode(prefix='rdf', name='li', children=[
                    XmlNode(prefix='vcard', name='N', children=names_xml)
                ]))

            metadata.append(
                XmlNode(prefix='dc', name='creator', children=[
                    XmlNode(prefix='rdf', name='Bag', children=authors_xml)
                ])
            )
            namespaces.add('dc')
            namespaces.add('rdf')
            namespaces.add('vcard')

        if obj.metadata.references and obj.metadata.references.citations:
            refs_xml = []
            for citation in obj.metadata.references.citations:
                props_xml = []
                if citation.authors:
                    props_xml.append(XmlNode(prefix='bibo', name='authorList', children=citation.authors))
                if citation.title:
                    props_xml.append(XmlNode(prefix='dc', name='title', children=citation.title))
                if citation.journal:
                    props_xml.append(XmlNode(prefix='bibo', name='journal', children=citation.journal))
                if citation.volume:
                    props_xml.append(XmlNode(prefix='bibo', name='volume', children=citation.volume))
                if citation.issue:
                    props_xml.append(XmlNode(prefix='bibo', name='issue', children=citation.issue))
                if citation.pages:
                    props_xml.append(XmlNode(prefix='bibo', name='pages', children=citation.pages))
                if citation.year:
                    props_xml.append(XmlNode(prefix='dc', name='date', children=citation.year))
                doi = next((identifier.id for identifier in citation.identifiers if identifier.namespace.lower() == 'doi'), None)
                if doi:
                    props_xml.append(XmlNode(prefix='bibo', name='doi', children=doi))

                refs_xml.append(XmlNode(prefix='rdf', name='li', children=[
                    XmlNode(prefix='bibo', name='Article', children=props_xml)
                ]))

            metadata.append(
                XmlNode(prefix='dcterms', name='references', children=[
                    XmlNode(prefix='rdf', name='Bag', children=refs_xml)
                ])
            )
            namespaces.add('dcterms')
            namespaces.add('rdf')
            namespaces.add('bibo')

        if obj.metadata.license:
            if obj.metadata.license.namespace:
                children = '{}:{}'.format(obj.metadata.license.namespace, obj.metadata.license.id)
            else:
                children = obj.metadata.license.id
            metadata.append(XmlNode(
                prefix='dcterms',
                name='license',
                children=children,
            ))
            namespaces.add('dcterms')

        metadata.append(XmlNode(prefix='dcterms', name='mediator', children='BioSimulators utils'))
        if obj.metadata.created is not None:
            metadata.append(XmlNode(prefix='dcterms', name='created',
                                    children=obj.metadata.created.strftime('%Y-%m-%dT%H:%M:%SZ')))
        if obj.metadata.updated is not None:
            metadata.append(XmlNode(prefix='dcterms', name='date', type='update',
                                    children=obj.metadata.updated.strftime('%Y-%m-%dT%H:%M:%SZ')))
        namespaces.add('dcterms')

        self._add_annotation_to_obj(metadata, obj_sed, namespaces)

    def _add_annotation_to_obj(self, nodes, obj_sed, namespaces):
        """ Add annotation to a SED object

        Args:
            nodes (:obj:`list` of :obj:`XmlNode`): annotation
            obj_sed (:obj:`libsedml.SedBase`): SED object
            namespaces (:obj:`set` of :obj:`str`): list of namespaces
        """
        if nodes:
            meta_id = self._set_meta_id(obj_sed)
            about_xml = ' rdf:about="#{}"'.format(meta_id)

            namespaces.add('rdf')
            namespaces_xml = []
            if 'rdf' in namespaces:
                namespaces_xml.append(' xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"')
            if 'dc' in namespaces:
                namespaces_xml.append(' xmlns:dc="http://purl.org/dc/elements/1.1/"')
            if 'dcterms' in namespaces:
                namespaces_xml.append(' xmlns:dcterms="http://purl.org/dc/terms/"')
            if 'vcard' in namespaces:
                namespaces_xml.append(' xmlns:vcard="http://www.w3.org/2001/vcard-rdf/3.0#"')
            if 'bibo' in namespaces:
                namespaces_xml.append(' xmlns:bibo="http://purl.org/ontology/bibo/"')

            self._call_libsedml_method(obj_sed, 'setAnnotation',
                                       ('<annotation>'
                                        '  <rdf:RDF{}>'
                                        '    <rdf:Description{}>'
                                        '    {}'
                                        '    </rdf:Description>'
                                        '  </rdf:RDF>'
                                        '  </annotation>').format(
                                           ''.join(namespaces_xml),
                                           about_xml,
                                           ''.join(node.encode() for node in nodes)))

    def _set_meta_id(self, obj_sed):
        """ Generate and set a unique meta id for a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object

        Returns:
            :obj:`str`: meta id
        """
        self._num_meta_id += 1
        meta_id = '_{:08d}'.format(self._num_meta_id)
        self._call_libsedml_method(obj_sed, 'setMetaId', meta_id)
        return meta_id

    def _add_namespaces_to_obj(self, obj_sed, namespaces):
        """ Add namespaces to a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object
            namespaces (:obj:`dict`): dictionary that maps the prefixes of namespaces to their URIs
        """
        existing_namespaces = get_namespaces_for_sed_object(obj_sed)
        obj_namespaces = obj_sed.getNamespaces()
        for prefix, uri in namespaces.items():
            if prefix in existing_namespaces:
                if uri != existing_namespaces[prefix]:
                    obj_namespaces.remove(obj_namespaces.getIndexByPrefix(prefix or ''))
                    obj_namespaces.add(uri, prefix or '')
            else:
                obj_namespaces.add(uri, prefix or '')

    def _call_libsedml_method(self, obj_sed, method_name, *args, **kwargs):
        """ Call a method of a SED object and check if there's an error

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object
            method_name (:obj:`str`): method name
            *args (:obj:`list`): positional arguments to the method
            **kwargs (:obj:`dict`, optional): keyword arguments to the method

        Returns:
            :obj:`int`: libsedml return code

        Raises:
            :obj:`ValueError`: if there was a libSED-ML error
        """
        method = getattr(obj_sed, method_name)
        return_val = method(*args, **kwargs)
        if return_val != 0 or self._doc_sed.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR):
            raise ValueError('libSED-ML error: {}'.format(self._doc_sed.getErrorLog().toString()))
        return return_val


class SedmlSimulationReader(object):
    """ SED-ML reader

    Attributes:
        errors (nested :obj:`list` of :obj:`str`): errors
        warnings (nested :obj:`list` of :obj:`str`): warnings
    """

    def __init__(self):
        self.errors = None
        self.warnings = None

    def run(self, filename, validate_semantics=True, validate_models_with_languages=True):
        """ Base class for reading a SED document

        Args:
            filename (:obj:`str`): path to SED-ML document
            validate_semantics (:obj:`bool`, optional): if :obj:`True`, check that SED-ML is semantically valid
            validate_models_with_languages (:obj:`bool`, optional): if :obj:`True`, validate models

        Returns:
            :obj:`data_model.SedDocument`: SED document

        Raises:
            :obj:`ValueError`: if any of the following conditions are met

                * The SED document contains changes other than instances of SedChangeAttribute
                * The models or simulations don't have unique ids
                * A model or simulation references cannot be resolved
        """
        self.errors = []
        self.warnings = []

        if not os.path.isfile(filename):
            msg = '`{}` is not a file.'.format(filename)
            self.errors.append([msg])
            raise FileNotFoundError(msg)

        doc_sed = libsedml.readSedMLFromFile(filename)
        if doc_sed.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR):
            error_log = doc_sed.getErrorLog()
            for i_error in range(error_log.getNumErrors()):
                error = error_log.getError(i_error)
                self.errors.append([error.getMessage()])

            msg = '`{}` is not a valid SED-ML file:\n  {}'.format(filename, doc_sed.getErrorLog().toString().replace('\n', '\n  '))
            raise ValueError(msg)

        for child_type in ('Models', 'Simulations', 'DataGenerators', 'Tasks', 'Outputs'):
            get_children = getattr(doc_sed, 'getListOf' + child_type)

            missing_ids = [str(i_child + 1) for i_child, child in enumerate(get_children()) if not child.getId()]

            if missing_ids:  # pragma no cover: validated by libSED-ML
                msg = '{} must have ids. The following {} are missing ids: {}.'.format(child_type, child_type, ', '.join(missing_ids))
                self.errors.append([msg])
                raise ValueError(msg)

        doc = data_model.SedDocument(
            level=doc_sed.getLevel(),
            version=doc_sed.getVersion(),
        )

        if doc.level > 1 or doc.version > 3:
            warn(('`{}` is encoded using L{}V{}. Only features available in L1V3 are supported. '
                  'Newer features such as simple repeated tasks are not yet supported.'
                  ).format(filename, doc.level, doc.version), SedmlFeatureNotSupportedWarning)

        doc.metadata = self._read_metadata(doc_sed)

        # initialize data structure to keep track of errors in references
        self._reference_errors = []

        # data descriptions
        if doc_sed.getListOfDataDescriptions():
            warn('Data descriptions skipped because data descriptions are not yet supported',
                 SedmlFeatureNotSupportedWarning)

        # models
        id_to_model_map = {}
        for model_sed in doc_sed.getListOfModels():
            model = data_model.Model()

            model.id = model_sed.getId() or None
            model.name = model_sed.getName() or None
            model.source = model_sed.getSource() or None
            model.language = model_sed.getLanguage() or None

            doc.models.append(model)
            self._add_obj_to_id_to_obj_map(model_sed, model, id_to_model_map)

        # simulations
        id_to_sim_map = {}
        for sim_sed in doc_sed.getListOfSimulations():
            if isinstance(sim_sed, libsedml.SedSteadyState):
                sim = data_model.SteadyStateSimulation()

            elif isinstance(sim_sed, libsedml.SedOneStep):
                sim = data_model.OneStepSimulation()
                if sim_sed.isSetStep():
                    sim.step = sim_sed.getStep()

            elif isinstance(sim_sed, libsedml.SedUniformTimeCourse):
                sim = data_model.UniformTimeCourseSimulation()
                if sim_sed.isSetInitialTime():
                    sim.initial_time = float(sim_sed.getInitialTime())
                if sim_sed.isSetOutputStartTime():
                    sim.output_start_time = float(sim_sed.getOutputStartTime())
                if sim_sed.isSetOutputEndTime():
                    sim.output_end_time = float(sim_sed.getOutputEndTime())
                if sim_sed.isSetNumberOfSteps():
                    sim.number_of_steps = int(sim_sed.getNumberOfSteps())

            else:  # pragma: no cover: already validated by libSED-ML
                # this is an error rather than a warning because SED doesn't define any other types of simulations
                msg = 'Simulation type {} is not supported.'.format(sim_sed.__class__.__name__)
                raise NotImplementedError(msg)

            doc.simulations.append(sim)

            self._add_obj_to_id_to_obj_map(sim_sed, sim, id_to_sim_map)

            sim.id = sim_sed.getId() or None
            sim.name = sim_sed.getName() or None

            alg_sed = sim_sed.getAlgorithm()
            if alg_sed:
                algorithm = sim.algorithm = data_model.Algorithm()
                algorithm.kisao_id = alg_sed.getKisaoID() or None

                for change_sed in alg_sed.getListOfAlgorithmParameters():
                    change = data_model.AlgorithmParameterChange()
                    algorithm.changes.append(change)
                    change.kisao_id = change_sed.getKisaoID() or None
                    change.new_value = change_sed.getValue() or None

        # tasks
        id_to_task_map = {}
        id_to_range_map = {}
        for task_sed in doc_sed.getListOfTasks():
            if isinstance(task_sed, libsedml.SedTask):
                task = data_model.Task()

                self._deserialize_reference(task_sed, task, 'model', 'ModelReference', 'model', id_to_model_map)
                self._deserialize_reference(task_sed, task, 'simulation', 'SimulationReference', 'simulation', id_to_sim_map)

            elif isinstance(task_sed, libsedml.SedRepeatedTask):
                task = data_model.RepeatedTask()

                if task_sed.isSetResetModel():
                    task.reset_model_for_each_iteration = task_sed.getResetModel()

                for change_sed in task_sed.getListOfTaskChanges():
                    change = data_model.SetValueComputeModelChange()

                    change.target = change_sed.getTarget() or None
                    change.target_namespaces = self._get_namespaces_for_sed_object_targets(change_sed)

                    change.parameters = self._read_parameters(change_sed)
                    change.math = self._read_math(change_sed)
                    self._deserialize_reference(change_sed, change, 'model', 'ModelReference', 'model', id_to_model_map)
                    change.symbol = change_sed.getSymbol() or None

                    task.changes.append(change)

                for sub_task_sed in task_sed.getListOfSubTasks():
                    sub_task = data_model.SubTask()

                    if sub_task_sed.isSetOrder():
                        sub_task.order = sub_task_sed.getOrder()

                    task.sub_tasks.append(sub_task)

                for range_sed in task_sed.getListOfRanges():
                    if isinstance(range_sed, libsedml.SedUniformRange):
                        range_obj = data_model.UniformRange()

                        if range_sed.isSetStart():
                            range_obj.start = range_sed.getStart()
                        if range_sed.isSetEnd():
                            range_obj.end = range_sed.getEnd()
                        if range_sed.isSetNumberOfSteps():
                            range_obj.number_of_steps = range_sed.getNumberOfSteps()
                        if range_sed.isSetType():
                            range_type = range_sed.getType()
                            if range_type in data_model.UniformRangeType.__members__:
                                range_obj.type = data_model.UniformRangeType[range_type]
                            else:
                                msg = 'Range type {} is not supported.'.format(range_type)
                                raise NotImplementedError(msg)

                    elif isinstance(range_sed, libsedml.SedVectorRange):
                        range_obj = data_model.VectorRange()

                        range_obj.values = list(range_sed.getValues())

                    elif isinstance(range_sed, libsedml.SedFunctionalRange):
                        range_obj = data_model.FunctionalRange()

                        range_obj.parameters = self._read_parameters(range_sed)
                        range_obj.math = self._read_math(range_sed)

                    else:  # pragma: no cover: already validated by libSED-ML
                        # this is an error rather than a warning because SED doesn't define any other types of ranges
                        msg = 'Range type {} is not supported.'.format(range_sed.__class__.__name__)
                        raise NotImplementedError(msg)

                    range_obj.id = range_sed.getId() or None

                    task.ranges.append(range_obj)
                    self._add_obj_to_id_to_obj_map(range_sed, range_obj, id_to_range_map)

            else:  # pragma: no cover: already validated by libSED-ML
                # this is an error rather than a warning because SED doesn't define any other types of tasks
                msg = 'Task type {} is not supported.'.format(task_sed.__class__.__name__)
                raise NotImplementedError(msg)

            task.id = task_sed.getId() or None
            task.name = task_sed.getName() or None

            doc.tasks.append(task)
            self._add_obj_to_id_to_obj_map(task_sed, task, id_to_task_map)

        # deserialize references from tasks
        for task_sed, task in zip(doc_sed.getListOfTasks(), doc.tasks):
            if isinstance(task_sed, libsedml.SedRepeatedTask):
                self._deserialize_reference(task_sed, task, 'range', 'RangeId', 'range', id_to_range_map)

                for change_sed, change in zip(task_sed.getListOfTaskChanges(), task.changes):
                    change.variables = self._read_variables(change_sed, id_to_model_map, id_to_task_map)
                    if change_sed.isSetRange():
                        self._deserialize_reference(change_sed, change, 'range', 'Range', 'range', id_to_range_map)

                for sub_task_sed, sub_task in zip(task_sed.getListOfSubTasks(), task.sub_tasks):
                    self._deserialize_reference(sub_task_sed, sub_task, 'task', 'Task', 'task', id_to_task_map)

                for range_sed, range_obj in zip(task_sed.getListOfRanges(), task.ranges):
                    if isinstance(range_sed, libsedml.SedFunctionalRange):
                        self._deserialize_reference(range_sed, range_obj, 'range', 'Range', 'range', id_to_range_map)
                        range_obj.variables = self._read_variables(range_sed, id_to_model_map, id_to_task_map)

        # model changes
        for model_sed, model in zip(doc_sed.getListOfModels(), doc.models):
            for change_sed in model_sed.getListOfChanges():
                if isinstance(change_sed, libsedml.SedChangeAttribute):
                    change = data_model.ModelAttributeChange()
                    change.new_value = change_sed.getNewValue() or None

                elif isinstance(change_sed, libsedml.SedAddXML):
                    change = data_model.AddElementModelChange()
                    new_xml = change_sed.getNewXML() or None
                    if new_xml is not None:
                        parent_namespaces = change_sed.getNamespaces()
                        prefixes = self._get_parent_namespaces_prefixes_used_in_xml_node(new_xml)
                        add_namespaces_to_xml_node(new_xml, prefixes, parent_namespaces)
                        change.new_elements = convert_xml_node_to_string(new_xml)

                elif isinstance(change_sed, libsedml.SedChangeXML):
                    change = data_model.ReplaceElementModelChange()
                    new_xml = change_sed.getNewXML() or None
                    if new_xml is not None:
                        parent_namespaces = change_sed.getNamespaces()
                        prefixes = self._get_parent_namespaces_prefixes_used_in_xml_node(new_xml)
                        add_namespaces_to_xml_node(new_xml, prefixes, parent_namespaces)
                        change.new_elements = convert_xml_node_to_string(new_xml)

                elif isinstance(change_sed, libsedml.SedRemoveXML):
                    change = data_model.RemoveElementModelChange()

                elif isinstance(change_sed, libsedml.SedComputeChange):
                    change = data_model.ComputeModelChange()
                    change.parameters = self._read_parameters(change_sed)
                    change.variables = self._read_variables(change_sed, id_to_model_map, id_to_task_map)
                    change.math = self._read_math(change_sed)

                else:  # pragma: no cover: already validated by libSED-ML
                    # this is an error rather than a warning because SED doesn't define any other types of changes
                    msg = 'Change type {} is not supported.'.format(change_sed.__class__.__name__)
                    raise NotImplementedError(msg)

                change.target = change_sed.getTarget() or None
                change.target_namespaces = self._get_namespaces_for_sed_object_targets(change_sed)
                model.changes.append(change)

        # data generators
        id_to_data_gen_map = {}
        for data_gen_sed in doc_sed.getListOfDataGenerators():
            data_gen = data_model.DataGenerator()

            data_gen.id = data_gen_sed.getId() or None
            data_gen.name = data_gen_sed.getName() or None
            data_gen.parameters = self._read_parameters(data_gen_sed)
            data_gen.variables = self._read_variables(data_gen_sed, id_to_model_map, id_to_task_map)
            data_gen.math = self._read_math(data_gen_sed)

            doc.data_generators.append(data_gen)
            self._add_obj_to_id_to_obj_map(data_gen_sed, data_gen, id_to_data_gen_map)

        # outputs
        id_to_output_map = {}
        for output_sed in doc_sed.getListOfOutputs():
            if isinstance(output_sed, libsedml.SedReport):
                output = data_model.Report()

                for dataset_sed in output_sed.getListOfDataSets():
                    data_set = data_model.DataSet()

                    data_set.id = dataset_sed.getId() or None
                    data_set.name = dataset_sed.getName() or None
                    data_set.label = dataset_sed.getLabel() or None

                    output.data_sets.append(data_set)
                    self._deserialize_reference(dataset_sed, data_set, 'data generator',
                                                'DataReference', 'data_generator', id_to_data_gen_map)

            elif isinstance(output_sed, libsedml.SedPlot2D):
                output = data_model.Plot2D()

                for curve_sed in output_sed.getListOfCurves():
                    curve = data_model.Curve()

                    curve.id = curve_sed.getId() or None
                    curve.name = curve_sed.getName() or None

                    curve.x_scale = data_model.AxisScale.log if curve_sed.getLogX() else data_model.AxisScale.linear
                    curve.y_scale = data_model.AxisScale.log if curve_sed.getLogY() else data_model.AxisScale.linear

                    output.curves.append(curve)
                    self._deserialize_reference(curve_sed, curve, 'data generator', 'XDataReference',
                                                'x_data_generator', id_to_data_gen_map)
                    self._deserialize_reference(curve_sed, curve, 'data generator', 'YDataReference',
                                                'y_data_generator', id_to_data_gen_map)

            elif isinstance(output_sed, libsedml.SedPlot3D):
                output = data_model.Plot3D()

                for surface_sed in output_sed.getListOfSurfaces():
                    surface = data_model.Surface()

                    surface.id = surface_sed.getId() or None
                    surface.name = surface_sed.getName() or None

                    surface.x_scale = data_model.AxisScale.log if surface_sed.getLogX() else data_model.AxisScale.linear
                    surface.y_scale = data_model.AxisScale.log if surface_sed.getLogY() else data_model.AxisScale.linear
                    surface.z_scale = data_model.AxisScale.log if surface_sed.getLogZ() else data_model.AxisScale.linear

                    output.surfaces.append(surface)
                    self._deserialize_reference(surface_sed, surface, 'data generator',
                                                'XDataReference', 'x_data_generator', id_to_data_gen_map)
                    self._deserialize_reference(surface_sed, surface, 'data generator',
                                                'YDataReference', 'y_data_generator', id_to_data_gen_map)
                    self._deserialize_reference(surface_sed, surface, 'data generator',
                                                'ZDataReference', 'z_data_generator', id_to_data_gen_map)

            else:  # pragma: no cover: already validated by libSED-ML
                # this is an error rather than a warning because SED doesn't define any other types of outputs
                msg = 'Output type {} is not supported.'.format(output_sed.__class__.__name__)
                raise NotImplementedError(msg)

            doc.outputs.append(output)

            self._add_obj_to_id_to_obj_map(output_sed, output, id_to_output_map)

            output.id = output_sed.getId() or None
            output.name = output_sed.getName() or None

        # normalize KiSAO ids
        for sim in doc.simulations:
            if sim.algorithm:
                if sim.algorithm.kisao_id:
                    sim.algorithm.kisao_id = normalize_kisao_id(sim.algorithm.kisao_id)
                for change in sim.algorithm.changes:
                    if change.kisao_id:
                        change.kisao_id = normalize_kisao_id(change.kisao_id)

        if self._reference_errors:
            self.errors.append([
                'The elements of the document have references that could not be resolved.',
                [[e] for e in self._reference_errors],
            ])
            raise ValueError('The elements of the document have references that could not be resolved:\n  {}'.format(
                '\n  '.join(self._reference_errors)))

        # validate
        errors, warnings = validate_doc(doc, working_dir=os.path.dirname(
            filename), validate_semantics=validate_semantics, validate_models_with_languages=validate_models_with_languages)
        self.errors.extend(errors)
        self.warnings.extend(warnings)
        if self.warnings:
            msg = 'The SED document is potentially incorrect.\n  {}'.format(
                flatten_nested_list_of_strings(self.warnings).replace('\n', '\n  '))
            warn(msg, BioSimulatorsWarning)
        if self.errors:
            msg = 'The SED document is invalid.\n  {}'.format(flatten_nested_list_of_strings(self.errors).replace('\n', '\n  '))
            raise ValueError(msg)

        # return SED document
        return doc

    def _read_parameters(self, obj_sed):
        """ Read a list of variables

        Args:
            obj_sed (:obj:`libsedml.SedBase`): compute change, data generator, functional range or set value

        Returns:
            :obj:`list` of :obj:`Parameter`
        """
        parameters = []
        for param_sed in obj_sed.getListOfParameters():
            param = data_model.Parameter()
            parameters.append(param)

            param.id = param_sed.getId() or None
            param.name = param_sed.getName() or None
            if param_sed.isSetValue():
                param.value = float(param_sed.getValue())
        return parameters

    def _read_variables(self, obj_sed, id_to_model_map, id_to_task_map):
        """ Read a list of variables

        Args:
            obj_sed (:obj:`libsedml.SedBase`): compute change, data generator, functional range or set value
            id_to_model_map (:obj:`dict` of :obj:`str` to :obj:`Model`): map from the ids of models to models
            id_to_task_map (:obj:`dict` of :obj:`str` to :obj:`Task`): map from the ids of tasks to tasks

        Returns:
            :obj:`list` of :obj:`Variable`
        """
        variables = []
        for var_sed in obj_sed.getListOfVariables():
            var = data_model.Variable()

            var.id = var_sed.getId() or None
            var.name = var_sed.getName() or None
            var.symbol = var_sed.getSymbol() or None
            var.target = var_sed.getTarget() or None
            var.target_namespaces = self._get_namespaces_for_sed_object_targets(var_sed)

            if var.target and var.target.startswith('#'):
                msg = 'Variable targets to data descriptions are not supported.'
                raise NotImplementedError(msg)

            self._deserialize_reference(var_sed, var, 'task', 'TaskReference', 'task', id_to_task_map)
            self._deserialize_reference(var_sed, var, 'model', 'ModelReference', 'model', id_to_model_map)

            variables.append(var)
        return variables

    def _read_math(self, obj_sed):
        """ Read a mathematical expression

        Args:
            obj_sed (:obj:`libsedml.SedBase`): compute change, data generator, functional range or set value

        Returns:
            :obj:`str`: expression
        """
        math = obj_sed.getMath() or None
        if math:
            math = libsedml.formulaToL3String(math)
        return math

    def _add_obj_to_id_to_obj_map(self, obj_sed, obj, id_to_obj_map):
        """ Add an object to an id to object map

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object
            obj (:obj:`object`): object
            id_to_obj_map (:obj:`dict` of :obj:`str` to :obj:`object`): map from the ids of objects to objects
        """
        id = obj_sed.getId()
        if id in id_to_obj_map:
            id_to_obj_map[id] = None
        else:
            id_to_obj_map[id] = obj

    def _deserialize_reference(self, obj_sed, obj, ref_type, sed_ref_getter, obj_attr, id_to_obj_map):
        """ Deserialize a reference to another object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object
            obj (:obj:`object`): object
            ref_type (:obj:`str`): type of reference (e.g., `data generator`)
            sed_ref_getter (:obj:`str`): SED reference getter (e.g., `XDataReference`)
            obj_attr (:obj:`str`): object attribute (e.g., `x_data_generator`)
            id_to_obj_map (:obj:`dict` of :obj:`str` to :obj:`object`): map from the ids of objects to objects
        """
        to_obj_id = getattr(obj_sed, 'get' + sed_ref_getter)() or None
        if to_obj_id:
            from_obj_id = obj_sed.__class__.__name__.replace('Sed', '') + (' `' + obj_sed.getId() + '`' if obj_sed.getId() else '')

            if to_obj_id in id_to_obj_map:
                setattr(obj, obj_attr, id_to_obj_map.get(to_obj_id, None))
                if not getattr(obj, obj_attr):
                    msg = '{} from {} cannot be resolved to a {} with id `{}` because multiple {}s have this id.'.format(
                        sed_ref_getter, from_obj_id, ref_type, to_obj_id, ref_type)
                    if msg not in self._reference_errors:
                        self._reference_errors.append(msg)
            else:
                msg = '{} from {} cannot be resolved to a {} with id `{}`.'.format(sed_ref_getter, from_obj_id, ref_type, to_obj_id)
                if msg not in self._reference_errors:
                    self._reference_errors.append(msg)

    def _read_metadata(self, obj_sed):
        """ Read metadata from a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object

        Returns:
            :obj:`Metadata`: metadata
        """
        metadata_sed = self._get_obj_annotation(obj_sed)
        metadata = Metadata(references=ExternalReferences())
        for node in metadata_sed:
            if node.prefix == 'dc' and node.name == 'description' and node.type == 'description' and isinstance(node.children, str):
                metadata.description = node.children
            elif node.prefix == 'dc' and node.name == 'description' and node.type == 'tags':
                for child in node.children:
                    if child.prefix == 'rdf' and child.name == 'Bag':
                        for child_2 in child.children:
                            if child_2.prefix == 'rdf' and child_2.name == 'li':
                                for child_3 in child_2.children:
                                    if child_3.prefix == 'rdf' and child_3.name == 'value' and isinstance(child_3.children, str):
                                        metadata.tags.append(child_3.children)
            elif node.prefix == 'dc' and node.name == 'creator':
                for child in node.children:
                    if child.prefix == 'rdf' and child.name == 'Bag':
                        for child_2 in child.children:
                            if child_2.prefix == 'rdf' and child_2.name == 'li':
                                for child_3 in child_2.children:
                                    if child_3.prefix == 'vcard' and child_3.name == 'N':
                                        author = Person()
                                        for prop in child_3.children:
                                            if prop.prefix == 'vcard' and prop.name == 'Given' and isinstance(prop.children, str):
                                                author.given_name = prop.children
                                            elif prop.prefix == 'vcard' and prop.name == 'Other' and isinstance(prop.children, str):
                                                author.other_name = prop.children
                                            elif prop.prefix == 'vcard' and prop.name == 'Family' and isinstance(prop.children, str):
                                                author.family_name = prop.children
                                        metadata.authors.append(author)
            elif node.prefix == 'dcterms' and node.name == 'references':
                for child in node.children:
                    if child.prefix == 'rdf' and child.name == 'Bag':
                        for child_2 in child.children:
                            if child_2.prefix == 'rdf' and child_2.name == 'li':
                                for child_3 in child_2.children:
                                    if child_3.prefix == 'bibo' and child_3.name == 'Article':
                                        citation = Citation()
                                        for prop in child_3.children:
                                            if prop.prefix == 'bibo' and prop.name == 'authorList' and isinstance(prop.children, str):
                                                citation.authors = prop.children
                                            elif prop.prefix == 'dc' and prop.name == 'title' and isinstance(prop.children, str):
                                                citation.title = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'journal' and isinstance(prop.children, str):
                                                citation.journal = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'volume' and isinstance(prop.children, str):
                                                citation.volume = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'issue' and isinstance(prop.children, str):
                                                citation.issue = prop.children
                                            elif prop.prefix == 'bibo' and prop.name == 'pages' and isinstance(prop.children, str):
                                                citation.pages = prop.children
                                            elif prop.prefix == 'dc' and prop.name == 'date' and isinstance(prop.children, str):
                                                citation.year = int(prop.children)
                                            elif prop.prefix == 'bibo' and prop.name == 'doi' and isinstance(prop.children, str):
                                                citation.identifiers = [
                                                    Identifier(
                                                        namespace="doi", id=prop.children, url="https://doi.org/" + prop.children),
                                                ]
                                        metadata.references.citations.append(citation)
            elif node.prefix == 'dcterms' and node.name == 'license' and isinstance(node.children, str):
                if ':' in node.children:
                    namespace, _, id = node.children.partition(':')
                else:
                    namespace = None
                    id = node.children
                if namespace == 'SPDX':
                    url = 'https://spdx.org/licenses/{}.html'.format(id)
                else:
                    url = None
                metadata.license = OntologyTerm(namespace=namespace, id=id, url=url)
            elif node.prefix == 'dcterms' and node.name == 'created' and isinstance(node.children, str):
                metadata.created = dateutil.parser.parse(node.children)
            elif node.prefix == 'dcterms' and node.name == 'date' and node.type == 'update' and isinstance(node.children, str):
                metadata.updated = dateutil.parser.parse(node.children)

        if not metadata.references.identifiers and not metadata.references.citations:
            metadata.references = None

        if next((True for field in metadata.to_tuple() if field), False):
            return metadata
        else:
            return None

    def _get_obj_annotation(self, obj_sed):
        """ Get the annotated properies of a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object

        Returns:
            :obj:`list` of :obj:`XmlNode`: list of annotations
        """
        annotations_xml = obj_sed.getAnnotation()
        if annotations_xml is None:
            return []

        nodes = []
        if annotations_xml.getPrefix() == '' and annotations_xml.getName() == 'annotation':
            for i_child in range(annotations_xml.getNumChildren()):
                rdf_xml = annotations_xml.getChild(i_child)
                if rdf_xml.getPrefix() == 'rdf' and rdf_xml.getName() == 'RDF':
                    for i_child_2 in range(rdf_xml.getNumChildren()):
                        description_xml = rdf_xml.getChild(i_child_2)
                        if description_xml.getPrefix() == 'rdf' and description_xml.getName() == 'Description':
                            description_about_obj = not obj_sed.getMetaId()
                            for i_attr in range(description_xml.getAttributesLength()):
                                if description_xml.getAttrPrefix(i_attr) == 'rdf' \
                                        and description_xml.getAttrName(i_attr) == 'about' \
                                        and description_xml.getAttrValue(i_attr) == '#' + obj_sed.getMetaId():
                                    description_about_obj = True
                                    break
                            if description_about_obj:
                                for i_child_3 in range(description_xml.getNumChildren()):
                                    child = description_xml.getChild(i_child_3)
                                    nodes.append(self._decode_obj_from_xml(child))
        return nodes

    def _decode_obj_from_xml(self, obj_xml):
        """ Decode an object from its XML representation

        Args:
            obj_xml (:obj:`libsedml.XMLNode`): XML representation of an object

        Returns:
            :obj:`XmlNode`: object
        """
        node = XmlNode(
            prefix=obj_xml.getPrefix(),
            name=obj_xml.getName(),
            type=None,
            children=None,
        )

        for i_attr in range(obj_xml.getAttributesLength()):
            if obj_xml.getAttrPrefix(i_attr) == 'dc' and obj_xml.getAttrName(i_attr) == 'type':
                node.type = obj_xml.getAttrValue(i_attr)

        if obj_xml.getNumChildren() == 1 and not obj_xml.getChild(0).getPrefix() and not obj_xml.getChild(0).getName():
            node.children = obj_xml.getChild(0).getCharacters()
        else:
            node.children = []
            for i_child in range(obj_xml.getNumChildren()):
                child_xml = obj_xml.getChild(i_child)
                node.children.append(self._decode_obj_from_xml(child_xml))

        return node

    def _get_namespaces_for_sed_object_targets(self, obj_sed):
        """ Get the namespaces for the target of a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object

        Returns:
            :obj:`dict`: dictionary that maps the prefixes of namespaces to their URIs
        """
        return get_namespaces_for_sed_object(obj_sed)

    def _get_parent_namespaces_prefixes_used_in_xml_node(self, node):
        """ Get the namespace prefixes that are in the node which aren't defined in the node

        Args:
            node (:obj:`libsedml.XMLNode`): XML node

        Returns:
            :obj:`set` of :obj:`str`: namespace prefixes used in the node which aren't defined in the node
        """
        undefined_prefixes = set()

        nodes = [(node, set())]
        while nodes:
            node, parent_namespace_prefixes = nodes.pop()
            node_namespace_prefixes = set(parent_namespace_prefixes)

            namespace_objs = node.getNamespaces()
            for i_namespace_obj in range(namespace_objs.getLength()):
                node_namespace_prefixes.add(namespace_objs.getPrefix(i_namespace_obj))

            prefix = node.getPrefix()
            if prefix and prefix not in node_namespace_prefixes:
                undefined_prefixes.add(prefix)

            attrs = node.getAttributes()
            for i_attr in range(attrs.getLength()):
                prefix = attrs.getPrefix(i_attr)
                if prefix and prefix not in node_namespace_prefixes:
                    undefined_prefixes.add(prefix)

            for i_child in range(node.getNumChildren()):
                nodes.append((node.getChild(i_child), node_namespace_prefixes))

        return undefined_prefixes


class RdfDataType(str, enum.Enum):
    """ RDF data type """
    string = 'string'
    integer = 'integer'
    float = 'float'
    date_time = 'dateTime'


class XmlNode(object):
    """ XML node, used for annotations

    Attributes:
        prefix (:obj:`str`): tag prefix
        name (:obj:`str`): tag name
        type (:obj:`str`): term type
        children (:obj:`int`, :obj:`float`, :obj:`str`, or :obj:`list` of :obj:`XmlNode`): children
    """

    def __init__(self, prefix=None, name=None, type=None, children=None):
        """
        Args:
            prefix (:obj:`str`, optional): tag prefix
            name (:obj:`str`, optional): tag name
            type (:obj:`str`, optional): term type
            children (:obj:`int`, :obj:`float`, :obj:`str`, or :obj:`list` of :obj:`XmlNode`, optional): children
        """
        self.prefix = prefix
        self.name = name
        self.type = type
        self.children = children

    def encode(self):
        if self.type:
            type = ' dc:type="{}"'.format(self.type)
        else:
            type = ''

        if isinstance(self.children, list):
            value_xml = ''.join(child.encode() for child in self.children)
        elif isinstance(self.children, str):
            value_xml = saxutils.escape(self.children)
        else:
            value_xml = self.children

        return ('<{}:{}'
                '{}>'
                '{}'
                '</{}:{}>').format(self.prefix, self.name,
                                   type, value_xml,
                                   self.prefix, self.name)
