from . import data_model
from ..biosimulations.data_model import Metadata, Person, ExternalReferences, Citation, Identifier, OntologyTerm
from xml.sax import saxutils
import copy
import dateutil.parser
import enum
import libsedml
import os
import re
import warnings


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

    def run(self, doc, filename):
        """ Save a SED document to an SED-ML XML file

        Args:
            doc (:obj:`data_model.SedDocument`): SED document
            filename (:obj:`str`): Path to save simulation experiment in SED-ML format
        """
        if next((True for model in doc.models if not model.id), False):
            raise ValueError('Models must have ids')
        if next((True for sim in doc.simulations if not sim.id), False):
            raise ValueError('Simulations must have ids')
        if next((True for data_gen in doc.data_generators if not data_gen.id), False):
            raise ValueError('Data generators must have ids')
        if next((True for task in doc.tasks if not task.id), False):
            raise ValueError('Tasks must have ids')
        if next((True for output in doc.outputs if not output.id), False):
            raise ValueError('Outputs must have ids')

        if len(set(model.id for model in doc.models)) < len(doc.models):
            raise ValueError('Models must have unique ids')
        if len(set(sim.id for sim in doc.simulations)) < len(doc.simulations):
            raise ValueError('Simulations must have unique ids')
        if len(set(data_gen.id for data_gen in doc.data_generators)) < len(doc.data_generators):
            raise ValueError('Data generators must have unique ids')
        if len(set(task.id for task in doc.tasks)) < len(doc.tasks):
            raise ValueError('Tasks must have unique ids')
        if len(set(output.id for output in doc.outputs)) < len(doc.outputs):
            raise ValueError('Outputs must have unique ids')

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
            else:
                raise NotImplementedError('Task type {} is not supported'.format(task.__class__.__name__))

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
                raise NotImplementedError('Output type {} is not supported'.format(output.__class__.__name__))

        self._export_doc(filename)

    def _create_doc(self, doc):
        """ Create a SED document

        Args:
            doc (:obj:`data_model.SedDocument`): SED document
        """
        doc_sed = self._doc_sed = libsedml.SedDocument()
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
            else:
                raise NotImplementedError('Model change type {} is not supported'.format(change.__class__.__name__))

    def _add_attribute_change_to_model(self, model, change):
        """ Add an attribute change change to a SED model

        Args:
            model (:obj:`data_model.Model`): model
            change (:obj:`data_model.ModelAttributeChange`): model attribute change
        """
        model_sed = self._obj_to_sed_obj_map[model]
        change_sed = model_sed.createChangeAttribute()
        self._obj_to_sed_obj_map[change] = change_sed

        if change.target is not None:
            self._call_libsedml_method(change_sed, 'setTarget', change.target)
        if change.new_value is not None:
            self._call_libsedml_method(change_sed, 'setNewValue', change.new_value)

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
            if sim.number_of_points is not None:
                self._call_libsedml_method(sim_sed, 'setNumberOfPoints', sim.number_of_points)
        else:
            raise NotImplementedError('Simulation type {} is not supported'.format(sim.__class__.__name__))

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
        self._call_libsedml_method(obj_sed, 'setKisaoID', obj.kisao_id)

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
            if task.model.id is None:
                raise ValueError('Model must have an id to be referenced')
            self._call_libsedml_method(task_sed, 'setModelReference', task.model.id)

        if task.simulation is not None:
            if task.simulation.id is None:
                raise ValueError('Simulation must have an id to be referenced')
            self._call_libsedml_method(task_sed, 'setSimulationReference', task.simulation.id)

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

        for var in data_gen.variables:
            self._add_var_to_data_gen(data_gen, var)

        for param in data_gen.parameters:
            self._add_param_to_data_gen(data_gen, param)

        if data_gen.math is not None:
            self._call_libsedml_method(data_gen_sed, 'setMath', libsedml.parseFormula(data_gen.math))

    def _add_var_to_data_gen(self, data_gen, var):
        """ Add a variable to a SED data generator

        Args:
            data_gen (:obj:`data_model.DataGenerator`): data generator
            var (:obj:`data_model.DataGeneratorVariable`): variable
        """
        data_gen_sed = self._obj_to_sed_obj_map[data_gen]
        var_sed = data_gen_sed.createVariable()
        self._obj_to_sed_obj_map[var] = var_sed

        if var.id is not None:
            self._call_libsedml_method(var_sed, 'setId', var.id)

        if var.name is not None:
            self._call_libsedml_method(var_sed, 'setName', var.name)

        if var.symbol is not None:
            self._call_libsedml_method(var_sed, 'setSymbol', var.symbol)

        if var.target is not None:
            self._call_libsedml_method(var_sed, 'setTarget', var.target)

        if var.task is not None:
            if var.task.id is None:
                raise ValueError('Task must have an id to be referenced')
            self._call_libsedml_method(var_sed, 'setTaskReference', var.task.id)

        if var.model is not None:
            if var.model.id is None:
                raise ValueError('Model must have an id to be referenced')
            self._call_libsedml_method(var_sed, 'setModelReference', var.model.id)

    def _add_param_to_data_gen(self, data_gen, param):
        """ Add a parameter to a SED data generator

        Args:
            data_gen (:obj:`data_model.DataGenerator`): data generator
            param (:obj:`data_model.DataGeneratorParameter`): parameter
        """
        data_gen_sed = self._obj_to_sed_obj_map[data_gen]
        param_sed = data_gen_sed.createParameter()
        self._obj_to_sed_obj_map[param] = param_sed

        if param.id is not None:
            self._call_libsedml_method(param_sed, 'setId', param.id)

        if param.name is not None:
            self._call_libsedml_method(param_sed, 'setName', param.name)

        if param.value is not None:
            self._call_libsedml_method(param_sed, 'setValue', param.value)

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

        for dataset in report.datasets:
            dataset_sed = report_sed.createDataSet()
            self._obj_to_sed_obj_map[dataset] = dataset_sed

            if dataset.id is not None:
                self._call_libsedml_method(dataset_sed, 'setId', dataset.id)
            if dataset.name is not None:
                self._call_libsedml_method(dataset_sed, 'setName', dataset.name)
            if dataset.label is not None:
                self._call_libsedml_method(dataset_sed, 'setLabel', dataset.label)
            if dataset.data_generator is not None:
                if dataset.data_generator.id is None:
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(dataset_sed, 'setDataReference', dataset.data_generator.id)

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

            if curve.x_scale == data_model.AxisScale.linear:
                self._call_libsedml_method(curve_sed, 'setLogX', False)
            elif curve.x_scale == data_model.AxisScale.log:
                self._call_libsedml_method(curve_sed, 'setLogX', True)

            if curve.y_scale == data_model.AxisScale.linear:
                self._call_libsedml_method(curve_sed, 'setLogY', False)
            elif curve.y_scale == data_model.AxisScale.log:
                self._call_libsedml_method(curve_sed, 'setLogY', True)

            if curve.x_data_generator is not None:
                if curve.x_data_generator.id is None:
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(curve_sed, 'setXDataReference', curve.x_data_generator.id)

            if curve.y_data_generator is not None:
                if curve.y_data_generator.id is None:
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

            if surface.x_scale == data_model.AxisScale.linear:
                self._call_libsedml_method(surface_sed, 'setLogX', False)
            elif surface.x_scale == data_model.AxisScale.log:
                self._call_libsedml_method(surface_sed, 'setLogX', True)

            if surface.y_scale == data_model.AxisScale.linear:
                self._call_libsedml_method(surface_sed, 'setLogY', False)
            elif surface.y_scale == data_model.AxisScale.log:
                self._call_libsedml_method(surface_sed, 'setLogY', True)

            if surface.z_scale == data_model.AxisScale.linear:
                self._call_libsedml_method(surface_sed, 'setLogZ', False)
            elif surface.z_scale == data_model.AxisScale.log:
                self._call_libsedml_method(surface_sed, 'setLogZ', True)

            if surface.x_data_generator is not None:
                if surface.x_data_generator.id is None:
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(surface_sed, 'setXDataReference', surface.x_data_generator.id)

            if surface.y_data_generator is not None:
                if surface.y_data_generator.id is None:
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(surface_sed, 'setYDataReference', surface.y_data_generator.id)

            if surface.z_data_generator is not None:
                if surface.z_data_generator.id is None:
                    raise ValueError('Data generator must have an id to be referenced')
                self._call_libsedml_method(surface_sed, 'setZDataReference', surface.z_data_generator.id)

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
                doi = next((identifier.id for identifier in citation.identifiers if identifier.namespace == 'doi'), None)
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
            metadata.append(XmlNode(
                prefix='dcterms',
                name='license',
                children='{}:{}'.format(obj.metadata.license.namespace, obj.metadata.license.id),
            ))
            namespaces.add('dcterms')

        metadata.append(XmlNode(prefix='dcterms', name='mediator', children='BioSimulators utils'))
        if obj.metadata.created is not None:
            metadata.append(XmlNode(prefix='dcterms', name='created',
                                    children=obj._metadata.created.strftime('%Y-%m-%dT%H:%M:%SZ')))
        if obj.metadata.updated is not None:
            metadata.append(XmlNode(prefix='dcterms', name='date', type='update',
                                    children=obj._metadata.updated.strftime('%Y-%m-%dT%H:%M:%SZ')))
        namespaces.add('dcterms')

        self._set_meta_id(obj_sed)
        self._add_annotation_to_obj(metadata, obj_sed, namespaces)

    def _set_meta_id(self, obj_sed):
        """ Generate and set a unique meta id for a SED object

        Args:
            obj_sed (:obj:`libsedml.SedBase`): SED object
        """
        self._num_meta_id += 1
        self._call_libsedml_method(obj_sed, 'setMetaId', '_{:08d}'.format(self._num_meta_id))

    def _add_annotation_to_obj(self, nodes, obj_sed, namespaces):
        """ Add annotation to a SED object

        Args:
            nodes (:obj:`list` of :obj:`XmlNode`): annotation
            obj_sed (:obj:`libsedml.SedBase`): SED object
            namespaces (:obj:`set` of :obj:`str`): list of namespaces
        """
        if nodes:
            meta_id = obj_sed.getMetaId()
            if meta_id:
                about_xml = ' rdf:about="#{}"'.format(meta_id)
            else:
                about_xml = ''

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
    """ SED-ML reader """

    def run(self, filename):
        """ Base class for reading a SED document

        Args:
            filename (:obj:`str`): path to SED-ML document

        Returns:
            :obj:`data_model.SedDocument`: SED document

        Raises:
            :obj:`ValueError`: if any of the following conditions are met

                * The SED document contains changes other than instances of SedChangeAttribute
                * The models or simulations don't have unique ids
                * A model or simulation references cannot be resolved
        """
        doc_sed = libsedml.readSedMLFromFile(filename)
        if doc_sed.getErrorLog().getNumFailsWithSeverity(libsedml.LIBSEDML_SEV_ERROR):
            raise ValueError('libsedml error: {}'.format(doc_sed.getErrorLog().toString()))

        if next((True for model in doc_sed.getListOfModels() if not model.getId()), False):
            raise ValueError('Models must have ids')
        if next((True for sim in doc_sed.getListOfSimulations() if not sim.getId()), False):
            raise ValueError('Simulations must have ids')
        if next((True for data_gen in doc_sed.getListOfDataGenerators() if not data_gen.getId()), False):
            raise ValueError('Data generators must have ids')
        if next((True for task in doc_sed.getListOfTasks() if not task.getId()), False):
            raise ValueError('Tasks must have ids')
        if next((True for output in doc_sed.getListOfOutputs() if not output.getId()), False):
            raise ValueError('Outputs must have ids')

        if len(set(model.getId() for model in doc_sed.getListOfModels())) < len(doc_sed.getListOfModels()):
            raise ValueError('Models must have unique ids')
        if len(set(sim.getId() for sim in doc_sed.getListOfSimulations())) < len(doc_sed.getListOfSimulations()):
            raise ValueError('Simulations must have unique ids')
        if len(set(data_gen.getId() for data_gen in doc_sed.getListOfDataGenerators())) < len(doc_sed.getListOfDataGenerators()):
            raise ValueError('Data generators must have unique ids')
        if len(set(task.getId() for task in doc_sed.getListOfTasks())) < len(doc_sed.getListOfTasks()):
            raise ValueError('Tasks must have unique ids')
        if len(set(output.getId() for output in doc_sed.getListOfOutputs())) < len(doc_sed.getListOfOutputs()):
            raise ValueError('Outputs must have unique ids')

        doc = data_model.SedDocument(
            level=doc_sed.getLevel(),
            version=doc_sed.getVersion(),
        )

        doc.metadata = self._read_metadata(doc_sed)

        # data descriptions
        if doc_sed.getListOfDataDescriptions():
            raise NotImplementedError('Data descriptions are not supported')

        # models
        id_to_model_map = {}
        for model_sed in doc_sed.getListOfModels():
            model = data_model.Model()
            doc.models.append(model)

            id_to_model_map[model_sed.getId()] = model

            model.id = model_sed.getId() or None
            model.name = model_sed.getName() or None
            model.source = model_sed.getSource() or None
            model.language = model_sed.getLanguage() or None

            for change_sed in model_sed.getListOfChanges():
                if not isinstance(change_sed, libsedml.SedChangeAttribute):
                    raise NotImplementedError('Model change type {} is not supported'.format(change_sed.__class__.__name__))
                change = data_model.ModelAttributeChange()
                model.changes.append(change)
                change.target = change_sed.getTarget() or None
                change.new_value = change_sed.getNewValue() or None

        # simulations
        id_to_sim_map = {}
        for sim_sed in doc_sed.getListOfSimulations():
            if isinstance(sim_sed, libsedml.SedSteadyState):
                sim = data_model.SteadyStateSimulation()

            elif isinstance(sim_sed, libsedml.SedOneStep):
                sim = data_model.OneStepSimulation()
                sim.step = sim_sed.getStep()

            elif isinstance(sim_sed, libsedml.SedUniformTimeCourse):
                sim = data_model.UniformTimeCourseSimulation()
                sim.initial_time = float(sim_sed.getInitialTime())
                sim.output_start_time = float(sim_sed.getOutputStartTime())
                sim.output_end_time = float(sim_sed.getOutputEndTime())
                sim.number_of_points = int(sim_sed.getNumberOfPoints())

                if sim.output_start_time < sim.initial_time:
                    raise ValueError('Output start time must be at least the initial time')

                if sim.output_end_time < sim.output_start_time:
                    raise ValueError('Output end time must be at least the output start time')

            else:
                raise NotImplementedError('Simulation type {} is not supported'.format(sim_sed.__class__.__name__))

            doc.simulations.append(sim)

            id_to_sim_map[sim_sed.getId()] = sim

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
        for task_sed in doc_sed.getListOfTasks():
            if not isinstance(task_sed, libsedml.SedTask):
                raise NotImplementedError('Task type {} is not supported'.format(task_sed.__class__.__name__))

            task = data_model.Task()
            doc.tasks.append(task)

            id_to_task_map[task_sed.getId()] = task

            task.id = task_sed.getId() or None
            task.name = task_sed.getName() or None

            model_id = task_sed.getModelReference() or None
            if model_id:
                task.model = id_to_model_map.get(model_id, None)
                if not task.model:
                    raise ValueError('Document does not contain a model with id "{}"'.format(model_id))

            sim_id = task_sed.getSimulationReference() or None
            if sim_id:
                task.simulation = id_to_sim_map.get(sim_id, None)
                if not task.simulation:
                    raise ValueError('Document does not contain a simulation with id "{}"'.format(sim_id))

        # data generators
        id_to_data_gen_map = {}
        for data_gen_sed in doc_sed.getListOfDataGenerators():
            data_gen = data_model.DataGenerator()
            doc.data_generators.append(data_gen)

            id_to_data_gen_map[data_gen_sed.getId()] = data_gen

            data_gen.id = data_gen_sed.getId() or None
            data_gen.name = data_gen_sed.getName() or None

            for var_sed in data_gen_sed.getListOfVariables():
                var = data_model.DataGeneratorVariable()
                data_gen.variables.append(var)

                var.id = var_sed.getId() or None
                var.name = var_sed.getName() or None
                var.symbol = var_sed.getSymbol() or None
                var.target = var_sed.getTarget() or None
                
                task_id = var_sed.getTaskReference() or None
                if task_id:
                    var.task = id_to_task_map.get(task_id, None)
                    if not var.task:
                        raise ValueError('Document does not contain a task with id "{}"'.format(task_id))

                model_id = var_sed.getModelReference() or None
                if model_id:
                    var.model = id_to_model_map.get(model_id, None)
                    if not var.model:
                        raise ValueError('Document does not contain a model with id "{}"'.format(model_id))        

            for param_sed in data_gen_sed.getListOfParameters():
                param = data_model.DataGeneratorParameter()
                data_gen.parameters.append(param)

                param.id = param_sed.getId() or None
                param.name = param_sed.getName() or None
                param.value = param_sed.getValue() or None
                if param.value is not None:
                    param.value = float(param.value)

            data_gen.math = data_gen_sed.getMath() or None
            if data_gen.math is not None:
                data_gen.math = libsedml.formulaToL3String(data_gen.math)

        # outputs
        id_to_output_map = {}
        for output_sed in doc_sed.getListOfOutputs():
            if isinstance(output_sed, libsedml.SedReport):
                output = data_model.Report()

                for dataset_sed in output_sed.getListOfDataSets():
                    dataset = data_model.Dataset() 
                    output.datasets.append(dataset)

                    dataset.id = dataset_sed.getId() or None
                    dataset.name = dataset_sed.getName() or None
                    dataset.label = dataset_sed.getLabel() or None
                    
                    data_gen_id = dataset_sed.getDataReference() or None
                    if data_gen_id:
                        dataset.data_generator = id_to_data_gen_map.get(data_gen_id, None)
                        if not dataset.data_generator:
                            raise ValueError('Document does not contain a data generator with id "{}"'.format(data_gen_id))  

            elif isinstance(output_sed, libsedml.SedPlot2D):
                output = data_model.Plot2D()

                for curve_sed in output_sed.getListOfCurves():
                    curve = data_model.Curve() 
                    output.curves.append(curve)

                    curve.id = curve_sed.getId() or None
                    curve.name = curve_sed.getName() or None
                    
                    curve.x_scale = data_model.AxisScale.log if curve_sed.getLogX() else data_model.AxisScale.linear
                    curve.y_scale = data_model.AxisScale.log if curve_sed.getLogY() else data_model.AxisScale.linear

                    x_data_gen_id = curve_sed.getXDataReference() or None
                    if x_data_gen_id:
                        curve.x_data_generator = id_to_data_gen_map.get(x_data_gen_id, None)
                        if not curve.x_data_generator:
                            raise ValueError('Document does not contain a data generator with id "{}"'.format(x_data_gen_id))  

                    y_data_gen_id = curve_sed.getYDataReference() or None
                    if y_data_gen_id:
                        curve.y_data_generator = id_to_data_gen_map.get(y_data_gen_id, None)
                        if not curve.y_data_generator:
                            raise ValueError('Document does not contain a data generator with id "{}"'.format(y_data_gen_id))  

            elif isinstance(output_sed, libsedml.SedPlot3D):
                output = data_model.Plot3D()

                for surface_sed in output_sed.getListOfSurfaces():
                    surface = data_model.Surface() 
                    output.surfaces.append(surface)

                    surface.id = surface_sed.getId() or None
                    surface.name = surface_sed.getName() or None
                    
                    surface.x_scale = data_model.AxisScale.log if surface_sed.getLogX() else data_model.AxisScale.linear
                    surface.y_scale = data_model.AxisScale.log if surface_sed.getLogY() else data_model.AxisScale.linear
                    surface.z_scale = data_model.AxisScale.log if surface_sed.getLogZ() else data_model.AxisScale.linear

                    x_data_gen_id = surface_sed.getXDataReference() or None
                    if x_data_gen_id:
                        surface.x_data_generator = id_to_data_gen_map.get(x_data_gen_id, None)
                        if not surface.x_data_generator:
                            raise ValueError('Document does not contain a data generator with id "{}"'.format(x_data_gen_id))  

                    y_data_gen_id = surface_sed.getYDataReference() or None
                    if y_data_gen_id:
                        surface.y_data_generator = id_to_data_gen_map.get(y_data_gen_id, None)
                        if not surface.y_data_generator:
                            raise ValueError('Document does not contain a data generator with id "{}"'.format(y_data_gen_id))  

                    z_data_gen_id = surface_sed.getZDataReference() or None
                    if z_data_gen_id:
                        surface.z_data_generator = id_to_data_gen_map.get(z_data_gen_id, None)
                        if not surface.z_data_generator:
                            raise ValueError('Document does not contain a data generator with id "{}"'.format(z_data_gen_id))  

            else:
                raise NotImplementedError('Output type {} is not supported'.format(output_sed.__class__.__name__))
            
            doc.outputs.append(output)

            id_to_output_map[output_sed.getId()] = output

            output.id = output_sed.getId() or None
            output.name = output_sed.getName() or None

        # return SED document
        return doc

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
                                                citation.identifiers = Identifier(
                                                    namespace="doi", id=prop.children, url="https://doi.org/" + prop.children)
                                        metadata.references.citations.append(citation)
            elif node.prefix == 'dcterms' and node.name == 'license' and isinstance(node.children, str):
                if ':' not in node.children:
                    raise SimulationIoError("License must be an SPDX id (SPDX:{ id })")
                namespace, _, id = node.children.partition(':')
                if namespace == 'SPDX':
                    url = 'https://spdx.org/licenses/{}.html'.format(id)
                else:
                    url = None
                metadata.license = OntologyTerm(namespace=namespace, id=id, url=url)
            elif node.prefix == 'dcterms' and node.name == 'created' and isinstance(node.children, str):
                sim._metadata.created = dateutil.parser.parse(node.children)
            elif node.prefix == 'dcterms' and node.name == 'date' and node.type == 'update' and isinstance(node.children, str):
                sim._metadata.updated = dateutil.parser.parse(node.children)

        if not metadata.references.identifiers and not metadata.references.citations:
            metadata.references = None

        if next((True for field in metadata.to_tuple() if field is not None), False):
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
                            if not description_about_obj:
                                continue
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


def normalize_kisao_id(id):
    """ Normalize an id for a KiSAO term to the official pattern `KISAO_\d{7}`.

    The official id pattern for KiSAO terms is `KISAO_\d{7}`. This is often confused with `KISAO:\d{7}` and `\d{7}`.
    This function automatically converts these other patterns to the offfical pattern.

    Args:
        id (:obj:`str`): offical KiSAO id with pattern `KISAO_\d{7}` or a variant such as `KISAO:\d{7}` or `\d{7}`

    Returns:
        :obj:`str`: normalized KiSAO id that follows the official pattern `KISAO_\d{7}`
    """
    unnormalized_id = id

    if id.startswith('KISAO:'):
        id = 'KISAO_' + id[6:]

    if not id.startswith('KISAO_'):
        id = 'KISAO_' + id

    if not re.match(r'KISAO_\d{7}', id):
        warnings.warn("'{}' is likely not a KiSAO term".format(unnormalized_id), SimulationIoWarning)

    return id