""" Data model for SED

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..biosimulations.data_model import Metadata  # noqa: F401
from ..utils.core import are_lists_equal, none_sorted
import abc
import enum


__all__ = [
    'ModelLanguage',
    'ModelLanguagePattern',
    'ModelLanguageEdamId',
    'Symbol',
    'SedBase',
    'SedIdGroupMixin',
    'TargetGroupMixin',
    'SedDocument',
    'Simulation',
    'SteadyStateSimulation',
    'OneStepSimulation',
    'UniformTimeCourseSimulation',
    'Algorithm',
    'AlgorithmParameterChange',
    'Model',
    'ModelChange',
    'ModelAttributeChange',
    'AddElementModelChange',
    'ReplaceElementModelChange',
    'RemoveElementModelChange',
    'ComputeModelChange',
    'SetValueComputeModelChange',
    'AbstractTask',
    'Task',
    'RepeatedTask',
    'SubTask',
    'Range',
    'UniformRange',
    'VectorRange',
    'FunctionalRange',
    'DataGenerator',
    'Variable',
    'Parameter',
    'Output',
    'Report',
    'DataSet',
    'Plot',
    'Plot2D',
    'Plot3D',
    'AxisScale',
    'Curve',
    'Surface',
]


class ModelLanguage(str, enum.Enum):
    """ Model language """
    BNGL = 'urn:sedml:language:bngl'
    CellML = 'urn:sedml:language:cellml'
    CopasiML = 'urn:sedml:language:copasiml'
    GINML = 'urn:sedml:language:ginml'
    HOC = 'urn:sedml:language:hoc'
    Kappa = 'urn:sedml:language:kappa'
    LEMS = 'urn:sedml:language:lems'
    MASS = 'urn:sedml:language:mass'
    MorpheusML = 'urn:sedml:language:morpheusml'
    NeuroML = 'urn:sedml:language:neuroml'
    pharmML = 'urn:sedml:language:pharmml'
    RBA = 'urn:sedml:language:rba'
    SBML = 'urn:sedml:language:sbml'
    Smoldyn = 'urn:sedml:language:smoldyn'
    VCML = 'urn:sedml:language:vcml'
    XPP = 'urn:sedml:language:xpp'
    ZGINML = 'urn:sedml:language:zginml'


class ModelLanguagePattern(str, enum.Enum):
    """ Model language """
    BNGL = r'^urn:sedml:language:bngl(\.|$)'
    CellML = r'^urn:sedml:language:cellml(\.\d+_\d+)?$'
    CopasiML = r'^urn:sedml:language:copasiml(\.|$)'
    GINML = r'^urn:sedml:language:ginml(\.|$)'
    HOC = r'^urn:sedml:language:hoc(\.|$)'
    Kappa = r'^urn:sedml:language:kappa(\.|$)'
    LEMS = r'^urn:sedml:language:lems(\.|$)'
    MASS = r'^urn:sedml:language:mass(\.|$)'
    MorpheusML = r'^urn:sedml:language:morpheusml(\.|$)'
    NeuroML = r'^urn:sedml:language:neuroml(\.version-\d+_\d+_\d+\.level\-\d+)?$'
    pharmML = r'^urn:sedml:language:pharmml(\.|$)'
    RBA = r'^urn:sedml:language:rba(\.|$)'
    SBML = r'^urn:sedml:language:sbml(\.level\-\d+\.version\-\d+)?$'
    Smoldyn = r'^urn:sedml:language:smoldyn(\.|$)'
    VCML = r'^urn:sedml:language:vcml(\.|$)'
    XPP = r'^urn:sedml:language:xpp(\.|$)'
    ZGINML = r'^urn:sedml:language:zginml(\.|$)'


class ModelLanguageEdamId(str, enum.Enum):
    """ Model language EDAM id """
    BNGL = 'format_3972'
    CellML = 'format_3240'
    CopasiML = 'format_9003'
    GINML = 'format_9009'
    HOC = 'format_9005'
    Kappa = 'format_9006'
    LEMS = 'format_9004'
    MASS = 'format_9011'
    MorpheusML = 'format_9002'
    NeuroML = 'format_3971'
    pharmML = 'format_9007'
    RBA = 'format_9012'
    SBML = 'format_2585'
    Smoldyn = 'format_9001'
    VCML = 'format_9000'
    XPP = 'format_9010'
    ZGINML = 'format_9008'


class Symbol(str, enum.Enum):
    """ Variable sumbol """
    time = 'urn:sedml:symbol:time'


class SedBase(abc.ABC):
    """ Base class for SED classes """
    @abc.abstractmethod
    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        pass  # pragma: no cover

    def is_equal(self, other):
        """ Determine if simulations are equal

        Args:
            other (:obj:`SedBase`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two simulations are equal
        """
        return self.__class__ == other.__class__


class SedIdGroupMixin(abc.ABC):
    """ Object with an id and optional name

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
    """

    def __init__(self, id=None, name=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
        """
        self.id = id
        self.name = name

    def is_equal(self, other):
        """ Determine if simulations are equal

        Args:
            other (:obj:`SedIdGroupMixin`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two simulations are equal
        """
        return self.__class__ == other.__class__ \
            and self.id == other.id \
            and self.name == other.name


class TargetGroupMixin(abc.ABC):
    """ Object with an id and optional name

    Attributes:
        target (:obj:`str`): id
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
    """

    def __init__(self, target=None, target_namespaces=None):
        """
        Args:
            target (:obj:`str`): id
            target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        """
        self.target = target
        self.target_namespaces = target_namespaces or {}

    def is_equal(self, other):
        """ Determine if simulations are equal

        Args:
            other (:obj:`TargetGroupMixin`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two simulations are equal
        """
        return self.__class__ == other.__class__ \
            and self.target == other.target \
            and self.target_namespaces == other.target_namespaces


class SedDocument(SedBase):
    """ A SED-ML document

    Attributes:
        level (:obj:`int`): level
        version (:obj:`int`): version
        models (:obj:`list` of :obj:`Model`): models
        simulations (:obj:`list` of :obj:`Simulation`): simulations
        tasks (:obj:`list` of :obj:`AbstractTask`): tasks
        data_generators (:obj:`list` of :obj:`DataGenerator`): data generators
        outputs (:obj:`list` of :obj:`Output`): outputs
        metadata (:obj:`Metadata`): metadata
    """

    def __init__(self, level=1, version=3, models=None, simulations=None, tasks=None, data_generators=None, outputs=None, metadata=None):
        """
        Args:
            level (:obj:`int`, optional): level
            version (:obj:`int`, optional): version
            models (:obj:`list` of :obj:`Model`, optional): models
            simulations (:obj:`list` of :obj:`Simulation`, optional): simulations
            tasks (:obj:`list` of :obj:`AbstractTask`, optional): tasks
            data_generators (:obj:`list` of :obj:`DataGenerator`, optional): data generators
            outputs (:obj:`list` of :obj:`Output`, optional): outputs
            metadata (:obj:`Metadata`, optional): metadata
        """
        SedBase.__init__(self)
        self.level = level
        self.version = version
        self.models = models or []
        self.simulations = simulations or []
        self.tasks = tasks or []
        self.data_generators = data_generators or []
        self.outputs = outputs or []
        self.metadata = metadata

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (
            self.level,
            self.version,
            tuple(none_sorted(model.to_tuple() for model in self.models)),
            tuple(none_sorted(simulation.to_tuple() for simulation in self.simulations)),
            tuple(none_sorted(task.to_tuple() for task in self.tasks)),
            tuple(none_sorted(data_generator.to_tuple() for data_generator in self.data_generators)),
            tuple(none_sorted(output.to_tuple() for output in self.outputs)),
            self.metadata.to_tuple() if self.metadata else None,
        )

    def is_equal(self, other):
        """ Determine if SED-ML documents are equal

        Args:
            other (:obj:`SedDocument`): another SED-ML document

        Returns:
            :obj:`bool`: :obj:`True`, if two SED-ML documents are equal
        """
        return SedBase.is_equal(self, other) \
            and self.level == other.level \
            and self.version == other.version \
            and are_lists_equal(self.models, other.models) \
            and are_lists_equal(self.simulations, other.simulations) \
            and are_lists_equal(self.tasks, other.tasks) \
            and are_lists_equal(self.data_generators, other.data_generators) \
            and are_lists_equal(self.outputs, other.outputs) \
            and ((self.metadata is None and self.metadata == other.metadata)
                 or (self.metadata is not None and self.metadata.is_equal(other.metadata)))


class Simulation(SedBase, SedIdGroupMixin):
    """ A simulation

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        algorithm (:obj:`Algorithm`): algorithm
    """

    def __init__(self, id=None, name=None, algorithm=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            algorithm (:obj:`Algorithm`, optional): algorithm
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        self.algorithm = algorithm

    def is_equal(self, other):
        """ Determine if simulations are equal

        Args:
            other (:obj:`Simulation`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two simulations are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and ((self.algorithm is None and self.algorithm == other.algorithm)
                 or (self.algorithm is not None and self.algorithm.is_equal(other.algorithm)))


class SteadyStateSimulation(Simulation):
    """ A steady-state simulation

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        algorithm (:obj:`Algorithm`): algorithm
    """

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.algorithm.to_tuple() if self.algorithm else None)


class OneStepSimulation(Simulation):
    """ A single simulation step

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        algorithm (:obj:`Algorithm`): algorithm
        step (:obj:`float`): step
    """

    def __init__(self, id=None, name=None, algorithm=None, step=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            algorithm (:obj:`Algorithm`, optional): algorithm
            step (:obj:`float`, optional): step
        """
        super(OneStepSimulation, self).__init__(id=id, name=name, algorithm=algorithm)
        self.step = step

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.algorithm.to_tuple() if self.algorithm else None, self.step)

    def is_equal(self, other):
        """ Determine if simulations are equal

        Args:
            other (:obj:`OneStepSimulation`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two simulations are equal
        """
        return super(OneStepSimulation, self).is_equal(other) \
            and self.step == other.step


class UniformTimeCourseSimulation(Simulation):
    """ A uniform time course simulation

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        algorithm (:obj:`Algorithm`): algorithm
        initial_time (:obj:`float`): initial time
        output_start_time (:obj:`float`): output start time
        output_end_time (:obj:`float`): output end time
        number_of_steps (:obj:`int`): number of time steps
    """

    def __init__(self, id=None, name=None, algorithm=None,
                 initial_time=None, output_start_time=None, output_end_time=None,
                 number_of_steps=None, number_of_points=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            algorithm (:obj:`Algorithm`, optional): algorithm
            initial_time (:obj:`float`, optional): initial time
            output_start_time (:obj:`float`, optional): output start time
            output_end_time (:obj:`float`, optional): output end time
            number_of_steps (:obj:`int`, optional): number of time steps
            number_of_points (:obj:`int`, optional): number of points
        """
        super(UniformTimeCourseSimulation, self).__init__(id=id, name=name, algorithm=algorithm)
        self.initial_time = initial_time
        self.output_start_time = output_start_time
        self.output_end_time = output_end_time
        if number_of_steps is not None and number_of_points is not None and number_of_points != number_of_steps:
            raise ValueError('Only one of `number_of_steps` or `number_of_points` should be used.')
        self.number_of_steps = number_of_steps if number_of_steps is not None else number_of_points

    @property
    def number_of_points(self):
        return self.number_of_steps

    @number_of_points.setter
    def number_of_points(self, value):
        self.number_of_steps = value

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.algorithm.to_tuple() if self.algorithm else None,
                self.initial_time, self.output_start_time, self.output_end_time, self.number_of_steps)

    def is_equal(self, other):
        """ Determine if simulations are equal

        Args:
            other (:obj:`UniformTimeCourseSimulation`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two simulations are equal
        """
        return super(UniformTimeCourseSimulation, self).is_equal(other) \
            and self.initial_time == other.initial_time \
            and self.output_start_time == other.output_start_time \
            and self.output_end_time == other.output_end_time \
            and self.number_of_steps == other.number_of_steps


class Algorithm(SedBase):
    """ A simulation algorithm

    Attributes:
        kisao_id (:obj:`str`): KiSAO id (e.g., `KISAO_0000029`)
        changes (:obj:`list` of :obj:`AlgorithmParameterChange`): parameter changes
    """

    def __init__(self, kisao_id=None, changes=None):
        """
        Args:
            kisao_id (:obj:`str`, optional): KiSAO id (e.g., `KISAO_0000029`)
            changes (:obj:`list` of :obj:`AlgorithmParameterChange`, optional): parameter changes
        """
        SedBase.__init__(self)
        self.kisao_id = kisao_id
        self.changes = changes or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.kisao_id,
                tuple(none_sorted(change.to_tuple() for change in self.changes)))

    def is_equal(self, other):
        """ Determine if algorithms are equal

        Args:
            other (:obj:`Algorithm`): another algorithm

        Returns:
            :obj:`bool`: :obj:`True`, if two algorithms are equal
        """
        return SedBase.is_equal(self, other) \
            and self.__class__ == other.__class__ \
            and self.kisao_id == other.kisao_id \
            and are_lists_equal(self.changes, other.changes)


class AlgorithmParameterChange(SedBase):
    """ A changed parameter of an algorithm

    Attributes:
        kisao_id (:obj:`str`): KiSAO id (e.g., `KISAO_0000029`)
        new_value (:obj:`str`): new value
    """

    def __init__(self, kisao_id=None, new_value=None):
        """
        Args:
            kisao_id (:obj:`str`, optional): KiSAO id (e.g., `KISAO_0000029`)
            new_value (:obj:`str`, optional): new value
        """
        SedBase.__init__(self)
        self.kisao_id = kisao_id
        self.new_value = new_value

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.kisao_id, self.new_value)

    def is_equal(self, other):
        """ Determine if parameter changes are equal

        Args:
            other (:obj:`AlgorithmParameterChange`): another parameter change

        Returns:
            :obj:`bool`: :obj:`True`, if two parameter changes are equal
        """
        return SedBase.is_equal(self, other) \
            and self.kisao_id == other.kisao_id \
            and self.new_value == other.new_value


class Model(SedBase, SedIdGroupMixin):
    """ A model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        source (:obj:`str`): path to the model file
        language (:obj:`str`): URN of the format of the model
        changes (:obj:`list` of :obj:`ModelChange`): model changes
    """

    def __init__(self, id=None, name=None, source=None, language=None, changes=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            source (:obj:`str`), optional: path to the model file
            language (:obj:`str`, optional): URN of the format of the model
            changes (:obj:`list` of :obj:`ModelChange`, optional): model changes
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        self.source = source
        self.language = language
        self.changes = changes or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.source, self.language,
                tuple(none_sorted(change.to_tuple() for change in self.changes)))

    def is_equal(self, other):
        """ Determine if models are equal

        Args:
            other (:obj:`Model`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two models are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and self.source == other.source \
            and self.language == other.language \
            and are_lists_equal(self.changes, other.changes)


class ModelChange(SedBase, SedIdGroupMixin, TargetGroupMixin):
    """ A change to a model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the model element that should be changed
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): path to the model element that should be changed
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        TargetGroupMixin.__init__(self, target=target, target_namespaces=target_namespaces)

    def is_equal(self, other):
        """ Determine if model changes are equal

        Args:
            other (:obj:`ModelChange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model changes are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and TargetGroupMixin.is_equal(self, other)


class ModelAttributeChange(ModelChange):
    """ A change of an attribute of a model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the model element that should be changed
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        new_value (:obj:`str`): new value
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None, new_value=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): path to the model element that should be changed
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
            new_value (:obj:`str`, optional): new value
        """
        super(ModelAttributeChange, self).__init__(id=id, name=name, target=target, target_namespaces=target_namespaces)
        self.new_value = new_value

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.target, self.target_namespaces, self.new_value)

    def is_equal(self, other):
        """ Determine if model attribute changes are equal

        Args:
            other (:obj:`ModelAttributeChange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model attribute changes are equal
        """
        return super(ModelAttributeChange, self).is_equal(other) \
            and self.new_value == other.new_value


class AddElementModelChange(ModelChange):
    """ An addition of an element to a model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the parent of the new element(s)
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        new_elements (:obj:`str`): new element(s)
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None, new_elements=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): path to the parent of the new element(s)
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
            new_elements (:obj:`str`): new element(s)
        """
        super(AddElementModelChange, self).__init__(id=id, name=name, target=target, target_namespaces=target_namespaces)
        self.new_elements = new_elements

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.target, self.target_namespaces, self.new_elements)

    def is_equal(self, other):
        """ Determine if model changes are equal

        Args:
            other (:obj:`AddElementModelChange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model changes are equal
        """
        return super(AddElementModelChange, self).is_equal(other) \
            and self.new_elements == other.new_elements


class ReplaceElementModelChange(ModelChange):
    """ A replacement of an element of a model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the element to replace
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        new_elements (:obj:`str`): new element(s)
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None, new_elements=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): path to the element to replace
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
            new_elements (:obj:`str`): new element(s)
        """
        super(ReplaceElementModelChange, self).__init__(id=id, name=name, target=target, target_namespaces=target_namespaces)
        self.new_elements = new_elements

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.target, self.target_namespaces, self.new_elements)

    def is_equal(self, other):
        """ Determine if model changes are equal

        Args:
            other (:obj:`ReplaceElementModelChange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model changes are equal
        """
        return super(ReplaceElementModelChange, self).is_equal(other) \
            and self.new_elements == other.new_elements


class RemoveElementModelChange(ModelChange):
    """ A removal of an element from a model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the element to remove
    """

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.target, self.target_namespaces)


class Calculation(SedBase):
    """A mathematical calculation

    Attributes:
        variables (:obj:`list` of :obj:`Variable`): variables
        parameters (:obj:`list` of :obj:`Parameter`): parameters
        math (:obj:`str`): mathematical expression
    """

    def __init__(self, variables=None, parameters=None, math=None):
        """
        Args:
            variables (:obj:`list` of :obj:`Variable`, optional): variables
            parameters (:obj:`list` of :obj:`Parameter`, optional): parameters
            math (:obj:`str`, optional): mathematical expression
        """
        SedBase.__init__(self)
        self.variables = variables or []
        self.parameters = parameters or []
        self.math = math

    def is_equal(self, other):
        """ Determine if model changes are equal

        Args:
            other (:obj:`Calculation`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model changes are equal
        """
        return SedBase.is_equal(self, other) \
            and are_lists_equal(self.variables, other.variables) \
            and are_lists_equal(self.parameters, other.parameters) \
            and self.math == other.math


class ComputeModelChange(ModelChange, Calculation):
    """ A replacement of an element of a model

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the element to replace
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        variables (:obj:`list` of :obj:`Variable`): variables
        parameters (:obj:`list` of :obj:`Parameter`): parameters
        math (:obj:`str`): mathematical expression
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None, variables=None, parameters=None, math=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): path to the element to replace
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
            variables (:obj:`list` of :obj:`Variable`, optional): variables
            parameters (:obj:`list` of :obj:`Parameter`, optional): parameters
            math (:obj:`str`, optional): mathematical expression
        """
        ModelChange.__init__(self, id=id, name=name, target=target, target_namespaces=target_namespaces)
        Calculation.__init__(self, variables=variables, parameters=parameters, math=math)

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.target, self.target_namespaces,
                tuple(none_sorted(variable.to_tuple() for variable in self.variables)),
                tuple(none_sorted(parameter.to_tuple() for parameter in self.parameters)),
                self.math)

    def is_equal(self, other):
        """ Determine if model changes are equal

        Args:
            other (:obj:`ComputeModelChange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model changes are equal
        """
        return ModelChange.is_equal(self, other) \
            and Calculation.is_equal(self, other)


class SetValueComputeModelChange(ComputeModelChange, Calculation):
    """ A change that sets the value of an attribute of a model within an iteration of a repeated task

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): path to the element to replace
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        variables (:obj:`list` of :obj:`Variable`): variables
        parameters (:obj:`list` of :obj:`Parameter`): parameters
        math (:obj:`str`): mathematical expression
        model (:obj:`Model`): model
        range (:obj:`Range`): range
        symbol (:obj:`str`): symbol
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None, variables=None, parameters=None,
                 math=None, model=None, range=None, symbol=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): path to the element to replace
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
            variables (:obj:`list` of :obj:`Variable`, optional): variables
            parameters (:obj:`list` of :obj:`Parameter`, optional): parameters
            math (:obj:`str`, optional): mathematical expression
            model (:obj:`Model`, optional): model
            range (:obj:`Range`, optional): range
            symbol (:obj:`str`, optional): symbol
        """
        ComputeModelChange.__init__(self, id=id, name=name, target=target, target_namespaces=target_namespaces)
        Calculation.__init__(self, variables=variables, parameters=parameters, math=math)
        self.model = model
        self.range = range
        self.symbol = symbol

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.target, self.target_namespaces,
                tuple(none_sorted(variable.to_tuple() for variable in self.variables)),
                tuple(none_sorted(parameter.to_tuple() for parameter in self.parameters)),
                self.math,
                self.model.id if self.model else None,
                self.range.id if self.range else None,
                self.symbol,
                )

    def is_equal(self, other):
        """ Determine if model changes are equal

        Args:
            other (:obj:`SetValueComputeModelChange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two model changes are equal
        """
        return ComputeModelChange.is_equal(self, other) \
            and Calculation.is_equal(self, other) \
            and ((self.model is None and self.model == other.model)
                 or (self.model is not None and other.model is not None and self.model.id == other.model.id)) \
            and ((self.range is None and self.range == other.range)
                 or (self.range is not None and other.range is not None and self.range.id == other.range.id)) \
            and self.symbol == other.symbol


class AbstractTask(SedBase, SedIdGroupMixin):
    """ Base class for tasks

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
    """

    def __init__(self, id=None, name=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)

    def is_equal(self, other):
        """ Determine if tasks are equal

        Args:
            other (:obj:`AbstractTask`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two tasks are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other)


class Task(AbstractTask):
    """ A task

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        model (:obj:`Model`): model
        simulation (:obj:`Simulation`): simulation
    """

    def __init__(self, id=None, name=None, model=None, simulation=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            model (:obj:`Model`, optional): model
            simulation (:obj:`Simulation`, optional): simulation
        """
        super(Task, self).__init__(id=id, name=name)
        self.model = model
        self.simulation = simulation

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                self.model.id if self.model else None,
                self.simulation.id if self.simulation else None)

    def is_equal(self, other):
        """ Determine if tasks are equal

        Args:
            other (:obj:`Task`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two tasks are equal
        """
        return super(Task, self).is_equal(other) \
            and ((self.model is None and self.model == other.model)
                 or (self.model is not None and other.model is not None and self.model.id == other.model.id)) \
            and ((self.simulation is None and self.simulation == other.simulation)
                 or (self.simulation is not None and other.simulation is not None and self.simulation.id == other.simulation.id))


class RepeatedTask(AbstractTask):
    """ A repeated task

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        range (:obj:`Range`): range of the iterations of the repeated task
        reset_model_for_each_iteration (:obj:`bool`): whether to reset the model for each iteration of the repeated task
        changes (:obj:`list` of :obj:`SetValueComputeModelChange`): set value model changes
        sub_tasks (:obj:`list` of :obj:`SubTask`): sub-tasks
        ranges (:obj:`list` of :obj:`Range`): ranges
    """

    def __init__(self, id=None, name=None, range=None, reset_model_for_each_iteration=None, changes=None, sub_tasks=None, ranges=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            range (:obj:`Range`, optional): range of the iterations of the repeated task
            reset_model_for_each_iteration (:obj:`bool`, optional): whether to reset the model for each iteration of the repeated task
            changes (:obj:`list` of :obj:`SetValueComputeModelChange`, optional): set value model changes
            sub_tasks (:obj:`list` of :obj:`SubTask`, optional): sub-tasks
            ranges (:obj:`list` of :obj:`Range`, optional): ranges
        """
        super(RepeatedTask, self).__init__(id=id, name=name)
        self.range = range
        self.reset_model_for_each_iteration = reset_model_for_each_iteration
        self.changes = changes or []
        self.sub_tasks = sub_tasks or []
        self.ranges = ranges or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                self.range.id if self.range else None,
                self.reset_model_for_each_iteration,
                tuple(none_sorted(change.to_tuple() for change in self.changes)),
                tuple(none_sorted(sub_task.to_tuple() for sub_task in self.sub_tasks)),
                tuple(none_sorted(range.to_tuple() for range in self.ranges)),
                )

    def is_equal(self, other):
        """ Determine if repeated tasks are equal

        Args:
            other (:obj:`RepeatedTask`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two repeated tasks are equal
        """
        return super(RepeatedTask, self).is_equal(other) \
            and ((self.range is None and self.range == other.range)
                 or (self.range is not None and other.range is not None and self.range.id == other.range.id)) \
            and self.reset_model_for_each_iteration == other.reset_model_for_each_iteration \
            and are_lists_equal(self.changes, other.changes) \
            and are_lists_equal(self.sub_tasks, other.sub_tasks) \
            and are_lists_equal(self.ranges, other.ranges)


class SubTask(SedBase):
    """ A subtask of a repeated task

    Attributes:
        task (:obj:`AbstractTask`): task
        order (:obj:`int`): order in which the subtask should be executed
    """

    def __init__(self, task=None, order=None):
        """
        Args:
            task (:obj:`AbstractTask`, optional): task
            order (:obj:`int`, optional): order in which the subtask should be executed
        """
        SedBase.__init__(self)
        self.task = task
        self.order = order

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.task.id if self.task else None,
                self.order,
                )

    def is_equal(self, other):
        """ Determine if repeated tasks are equal

        Args:
            other (:obj:`SubTask`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two repeated tasks are equal
        """
        return SedBase.is_equal(self, other) \
            and ((self.task is None and self.task == other.task)
                 or (self.task is not None and other.task is not None and self.task.id == other.task.id)) \
            and self.order == other.order


class Range(SedBase, SedIdGroupMixin):
    """ A range

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`, optional): name
    """

    def __init__(self, id=None, name=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)

    def is_equal(self, other):
        """ Determine if ranges are equal

        Args:
            other (:obj:`Range`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two ranges are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other)


class UniformRangeType(str, enum.Enum):
    """ Type of a uniform range """
    linear = 'linear'
    log = 'log'


class UniformRange(Range):
    """ A uniform range

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        start (:obj:`float`): start value
        end (:obj:`float`): end value
        number_of_steps (:obj:`int`): number of steps
        type (:obj:`UniformRangeType`): type
    """

    def __init__(self, id=None, name=None, start=None, end=None, number_of_steps=None, number_of_points=None, type=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            start (:obj:`float`, optional): start value
            end (:obj:`float`, optional): end value
            number_of_steps (:obj:`int`, optional): number of steps
            number_of_points (:obj:`int`, optional): number of points
            type (:obj:`UniformRangeType`, optional): type
        """
        super(UniformRange, self).__init__(id=id, name=name)
        self.start = start
        self.end = end
        if number_of_steps is not None and number_of_points is not None and number_of_points != number_of_steps:
            raise ValueError('Only one of `number_of_steps` or `number_of_points` should be used.')
        self.number_of_steps = number_of_steps if number_of_steps is not None else number_of_points
        self.type = type

    @property
    def number_of_points(self):
        return self.number_of_steps

    @number_of_points.setter
    def number_of_points(self, value):
        self.number_of_steps = value

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.start, self.end, self.number_of_steps, self.type.value)

    def is_equal(self, other):
        """ Determine if ranges are equal

        Args:
            other (:obj:`UniformRange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two ranges are equal
        """
        return super(UniformRange, self).is_equal(other) \
            and self.start == other.start \
            and self.end == other.end \
            and self.number_of_steps == other.number_of_steps \
            and self.type == other.type


class VectorRange(Range):
    """ A vector range

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        values (:obj:`list` of :obj:`float`): values
    """

    def __init__(self, id=None, name=None, values=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            values (:obj:`list` of :obj:`float`): values
        """
        super(VectorRange, self).__init__(id=id, name=name)
        self.values = values or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, tuple(self.values))

    def is_equal(self, other):
        """ Determine if ranges are equal

        Args:
            other (:obj:`VectorRange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two ranges are equal
        """
        return super(VectorRange, self).is_equal(other) \
            and self.values == other.values


class FunctionalRange(Range, Calculation):
    """ A functional range

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        range (:obj:`Range`): range
        variables (:obj:`list` of :obj:`Variable`): variables
        parameters (:obj:`list` of :obj:`Parameter`): parameters
        math (:obj:`str`): mathematical expression
    """

    def __init__(self, id=None, name=None, range=None, variables=None, parameters=None, math=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            range (:obj:`Range`, optional): range
            variables (:obj:`list` of :obj:`Variable`, optional): variables
            parameters (:obj:`list` of :obj:`Parameter`, optional): parameters
            math (:obj:`str`, optional): mathematical expression
        """
        Range.__init__(self, id=id, name=name)
        Calculation.__init__(self, variables=variables, parameters=parameters, math=math)
        self.range = range

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                self.range.id if self.range else None,
                tuple(none_sorted(variable.to_tuple() for variable in self.variables)),
                tuple(none_sorted(parameter.to_tuple() for parameter in self.parameters)),
                self.math)

    def is_equal(self, other):
        """ Determine if ranges are equal

        Args:
            other (:obj:`FunctionalRange`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two ranges are equal
        """
        return Range.is_equal(self, other) \
            and Calculation.is_equal(self, other) \
            and ((self.range is None and self.range == other.range)
                 or (self.range is not None and other.range is not None and self.range.id == other.range.id))


class DataGenerator(Calculation, SedIdGroupMixin):
    """ A data generator

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        variables (:obj:`list` of :obj:`Variable`): variables
        parameters (:obj:`list` of :obj:`Parameter`): parameters
        math (:obj:`str`): mathematical expression
    """

    def __init__(self, id=None, name=None, variables=None, parameters=None, math=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            variables (:obj:`list` of :obj:`Variable`, optional): variables
            parameters (:obj:`list` of :obj:`Parameter`, optional): parameters
            math (:obj:`str`, optional): mathematical expression
        """
        SedIdGroupMixin.__init__(self, id=id, name=name)
        Calculation.__init__(self, variables=variables, parameters=parameters, math=math)

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                tuple(none_sorted(variable.to_tuple() for variable in self.variables)),
                tuple(none_sorted(parameter.to_tuple() for parameter in self.parameters)),
                self.math)

    def is_equal(self, other):
        """ Determine if data generators
         are equal

        Args:
            other (:obj:`DataGenerator`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two data generators are equal
        """
        return SedIdGroupMixin.is_equal(self, other) \
            and Calculation.is_equal(self, other)


class Variable(SedBase, SedIdGroupMixin):
    """ A model variable

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        target (:obj:`str`): target
        target_namespaces (:obj:`dict`): map of prefixes of namespaces for the target to their URIs
        symbol (:obj:`str`): symbol
        task (:obj:`AbstractTask`): task
        model (:obj:`Model`): model
    """

    def __init__(self, id=None, name=None, target=None, target_namespaces=None, symbol=None, task=None, model=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            target (:obj:`str`, optional): target
            target_namespaces (:obj:`dict`, optional): map of prefixes of namespaces for the target to their URIs
            symbol (:obj:`str`, optional): symbol
            task (:obj:`AbstractTask`, optional): task
            model (:obj:`Model`, optional): model
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        TargetGroupMixin.__init__(self, target=target, target_namespaces=target_namespaces)
        self.symbol = symbol
        self.task = task
        self.model = model

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.target, self.target_namespaces, self.symbol,
                self.task.id if self.task else None,
                self.model.id if self.model else None)

    def is_equal(self, other):
        """ Determine if data generator variables are equal

        Args:
            other (:obj:`Variable`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two data generator variables are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and TargetGroupMixin.is_equal(self, other) \
            and self.symbol == other.symbol \
            and ((self.task is None and self.task == other.task)
                 or (self.task is not None and other.task is not None and self.task.id == other.task.id)) \
            and ((self.model is None and self.model == other.model)
                 or (self.model is not None and other.model is not None and self.model.id == other.model.id))


class Parameter(SedBase, SedIdGroupMixin):
    """ A parameter involved in a data generator

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        value (:obj:`float`): value
    """

    def __init__(self, id=None, name=None, value=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            value (:obj:`float`, optional): value
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        self.value = value

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.value)

    def is_equal(self, other):
        """ Determine if data generator parameters are equal

        Args:
            other (:obj:`Parameter`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two data generator parameters are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and self.value == other.value


class Output(SedBase, SedIdGroupMixin):
    """ An output

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
    """

    def __init__(self, id=None, name=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)

    def is_equal(self, other):
        """ Determine if outputs are equal

        Args:
            other (:obj:`Output`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two outputs are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other)


class Report(Output):
    """ A report

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        data_sets (:obj:`list` of :obj:`DataSet`): data sets
    """

    def __init__(self, id=None, name=None, data_sets=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            data_sets (:obj:`list` of :obj:`DataSet`, optional): data sets
        """
        super(Report, self).__init__(id=id, name=name)
        self.data_sets = data_sets or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                tuple(none_sorted(data_set.to_tuple() for data_set in self.data_sets)))

    def is_equal(self, other):
        """ Determine if reports are equal

        Args:
            other (:obj:`Report`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two reports are equal
        """
        return super(Report, self).is_equal(other) \
            and are_lists_equal(self.data_sets, other.data_sets)


class DataSet(SedBase, SedIdGroupMixin):
    """ A data set in a report

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        label (:obj:`str`): label
        data_generator (:obj:`DataGenerator`): data generator
    """

    def __init__(self, id=None, name=None, label=None, data_generator=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            label (:obj:`str`, optional): label
            data_generator (:obj:`DataGenerator`, optional): data generator
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        self.label = label
        self.data_generator = data_generator

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name, self.label,
                self.data_generator.id if self.data_generator is not None else None)

    def is_equal(self, other):
        """ Determine if data sets are equal

        Args:
            other (:obj:`DataSet`): another content item

        Returns:
            :obj:`bool`: :obj:`True`, if two data sets are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and self.label == other.label \
            and ((self.data_generator is None and self.data_generator == other.data_generator)
                 or (self.data_generator is not None
                     and other.data_generator is not None
                     and self.data_generator.id == other.data_generator.id))


class Plot(Output):
    """ A 2D plot

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
    """
    pass  # pragma: no cover


class Plot2D(Plot):
    """ A 2D plot

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        curves (:obj:`list` of :obj:`Curve`): curves
    """

    def __init__(self, id=None, name=None, curves=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            curves (:obj:`list` of :obj:`Curve`, optional): curves
        """
        self.id = id
        self.name = name
        self.curves = curves or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                tuple(none_sorted(curve.to_tuple() for curve in self.curves)))

    def is_equal(self, other):
        """ Determine if plots are equal

        Args:
            other (:obj:`Plot2D`): another plot

        Returns:
            :obj:`bool`: :obj:`True`, if two plots are equal
        """
        return self.__class__ == other.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and are_lists_equal(self.curves, other.curves)


class Plot3D(Plot):
    """ A 3D plot

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        surfaces (:obj:`list` of :obj:`Surface`): surfaces
    """

    def __init__(self, id=None, name=None, surfaces=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            surfaces (:obj:`list` of :obj:`Surface`, optional): surfaces
        """
        self.id = id
        self.name = name
        self.surfaces = surfaces or []

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                tuple(none_sorted(surface.to_tuple() for surface in self.surfaces)))

    def is_equal(self, other):
        """ Determine if plots are equal

        Args:
            other (:obj:`Plot3D`): another plot

        Returns:
            :obj:`bool`: :obj:`True`, if two plots are equal
        """
        return self.__class__ == other.__class__ \
            and self.id == other.id \
            and self.name == other.name \
            and are_lists_equal(self.surfaces, other.surfaces)


class AxisScale(str, enum.Enum):
    """ Scale of an axis """
    linear = 'linear'
    log = 'log'


class Curve(SedBase, SedIdGroupMixin):
    """ A curve in a 2D plot

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        x_scale (:obj:`AxisScale`): x axis scale
        y_scale (:obj:`AxisScale`): y axis scale
        x_data_generator (:obj:`DataGenerator`): x data generator
        y_data_generator (:obj:`DataGenerator`): y data generator
    """

    def __init__(self, id=None, name=None, x_scale=None, y_scale=None, x_data_generator=None, y_data_generator=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            x_scale (:obj:`AxisScale`, optional): x axis scale
            y_scale (:obj:`AxisScale`, optional): y axis scale
            x_data_generator (:obj:`DataGenerator`, optional): x data generator
            y_data_generator (:obj:`DataGenerator`, optional): y data generator
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.x_data_generator = x_data_generator
        self.y_data_generator = y_data_generator

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                self.x_scale.value if self.x_scale else None,
                self.y_scale.value if self.y_scale else None,
                self.x_data_generator.id if self.x_data_generator else None,
                self.y_data_generator.id if self.y_data_generator else None)

    def is_equal(self, other):
        """ Determine if curves are equal

        Args:
            other (:obj:`Curve`): another curve

        Returns:
            :obj:`bool`: :obj:`True`, if two curves are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and self.x_scale == other.x_scale \
            and self.y_scale == other.y_scale \
            and ((self.x_data_generator is None and self.x_data_generator == other.x_data_generator)
                 or (self.x_data_generator is not None
                     and other.x_data_generator is not None
                     and self.x_data_generator.id == other.x_data_generator.id)) \
            and ((self.y_data_generator is None and self.y_data_generator == other.y_data_generator)
                 or (self.y_data_generator is not None
                     and other.y_data_generator is not None
                     and self.y_data_generator.id == other.y_data_generator.id))


class Surface(SedBase, SedIdGroupMixin):
    """ A surface in a 3D plot

    Attributes:
        id (:obj:`str`): id
        name (:obj:`str`): name
        x_scale (:obj:`AxisScale`): x axis scale
        y_scale (:obj:`AxisScale`): y axis scale
        z_scale (:obj:`AxisScale`): z axis scale
        x_data_generator (:obj:`DataGenerator`): x data generator
        y_data_generator (:obj:`DataGenerator`): y data generator
        z_data_generator (:obj:`DataGenerator`): z data generator
    """

    def __init__(self, id=None, name=None,
                 x_scale=None, y_scale=None, z_scale=None,
                 x_data_generator=None, y_data_generator=None, z_data_generator=None):
        """
        Args:
            id (:obj:`str`, optional): id
            name (:obj:`str`, optional): name
            x_scale (:obj:`AxisScale`, optional): x axis scale
            y_scale (:obj:`AxisScale`, optional): y axis scale
            z_scale (:obj:`AxisScale`, optional): z axis scale
            x_data_generator (:obj:`DataGenerator`, optional): x data generator
            y_data_generator (:obj:`DataGenerator`, optional): y data generator
            z_data_generator (:obj:`DataGenerator`, optional): z data generator
        """
        SedBase.__init__(self)
        SedIdGroupMixin.__init__(self, id=id, name=name)
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale
        self.x_data_generator = x_data_generator
        self.y_data_generator = y_data_generator
        self.z_data_generator = z_data_generator

    def to_tuple(self):
        """ Get a tuple representation

        Returns:
            :obj:`tuple` of :obj:`str`: tuple representation
        """
        return (self.id, self.name,
                self.x_scale.value if self.x_scale else None,
                self.y_scale.value if self.y_scale else None,
                self.z_scale.value if self.z_scale else None,
                self.x_data_generator.id if self.x_data_generator else None,
                self.y_data_generator.id if self.y_data_generator else None,
                self.z_data_generator.id if self.z_data_generator else None)

    def is_equal(self, other):
        """ Determine if surfaces are equal

        Args:
            other (:obj:`Surface`): another surface

        Returns:
            :obj:`bool`: :obj:`True`, if two surfaces are equal
        """
        return SedBase.is_equal(self, other) \
            and SedIdGroupMixin.is_equal(self, other) \
            and self.x_scale == other.x_scale \
            and self.y_scale == other.y_scale \
            and self.z_scale == other.z_scale \
            and ((self.x_data_generator is None and self.x_data_generator == other.x_data_generator)
                 or (self.x_data_generator is not None
                     and other.x_data_generator is not None
                     and self.x_data_generator.id == other.x_data_generator.id)) \
            and ((self.y_data_generator is None and self.y_data_generator == other.y_data_generator)
                 or (self.y_data_generator is not None
                     and other.y_data_generator is not None
                     and self.y_data_generator.id == other.y_data_generator.id)) \
            and ((self.z_data_generator is None and self.z_data_generator == other.z_data_generator)
                 or (self.z_data_generator is not None
                     and other.z_data_generator is not None
                     and self.z_data_generator.id == other.z_data_generator.id))
