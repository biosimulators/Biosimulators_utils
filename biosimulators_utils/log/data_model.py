""" Data model for the execution status of COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
import enum
import os
import yaml

__all__ = [
    'Status',
    'Log',
    'CombineArchiveLog',
    'SedDocumentLog',
    'TaskLog',
    'OutputLog',
    'ReportLog',
    'Plot2DLog',
    'Plot3DLog',
]


class Status(str, enum.Enum):
    """ Status of COMBINE/OMEX archive or one of its components """
    QUEUED = 'QUEUED'

    RUNNING = 'RUNNING'

    SUCCEEDED = 'SUCCEEDED'

    SKIPPED = 'SKIPPED'
    # component will not / wasn't executed e.g., a plot won't be created because a
    # simulation doesn't have the ability to create plots

    FAILED = 'FAILED'


class Log(object):
    """ Log of a COMBINE/OMEX archive or one of its components

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        parent (:obj:`Log`): execution status of parent COMBINE/OMEX archive
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None, parent=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            parent (:obj:`Log`, optional): execution status of parent COMBINE/OMEX archive
            out_dir (:obj:`str`, optional): directory to export status
        """
        self.status = status
        self.exception = exception
        self.skip_reason = skip_reason
        self.output = output
        self.duration = duration
        self.parent = parent
        self.out_dir = out_dir

    def finalize(self):
        """ Mark all unexecuted elements as skipped """
        if self.status == Status.QUEUED:
            self.status = Status.SKIPPED
        elif self.status == Status.RUNNING:
            self.status = Status.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        value = {}

        value['status'] = self.status.value if self.status else None

        if self.exception:
            value['exception'] = {
                'type': self.exception.__class__.__name__,
                'message': str(self.exception),
            }
        else:
            value['exception'] = None

        if self.skip_reason:
            value['skipReason'] = {
                'type': self.skip_reason.__class__.__name__,
                'message': str(self.skip_reason),
            }
        else:
            value['skipReason'] = None

        value['output'] = self.output

        value['duration'] = self.duration

        return value

    def export(self):
        """ Write to a file """
        if self.out_dir:
            path = os.path.join(self.out_dir, get_config().LOG_PATH)
            if not os.path.isdir(self.out_dir):
                os.makedirs(self.out_dir)
            with open(path, 'w') as file:
                file.write(yaml.dump(self.to_dict()))
        elif self.parent:
            self.parent.export()


class CombineArchiveLog(Log):
    """ Log of a COMBINE/OMEX archive

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        sed_documents (:obj:`dict` of :obj:`str` to :obj:`SedDocumentLog`): execution status of each
            SED document in the archive
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None, sed_documents=None,
                 out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            sed_documents (:obj:`dict` of :obj:`str` to :obj:`SedDocumentLog`, optional): execution status of each
                SED document in the archive
            out_dir (:obj:`str`, optional): directory to export status
        """
        super(CombineArchiveLog, self).__init__(status=status, exception=exception,
                                                skip_reason=skip_reason, output=output,
                                                duration=duration, out_dir=out_dir)
        self.sed_documents = sed_documents

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(CombineArchiveLog, self).finalize()

        if self.sed_documents:
            for sed_document in self.sed_documents.values():
                sed_document.finalize()

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        value = super(CombineArchiveLog, self).to_dict()
        value['sedDocuments'] = (
            {doc_id: (doc_log.to_dict() if doc_log else None) for doc_id, doc_log in self.sed_documents.items()}
            if self.sed_documents is not None
            else None
        )
        return value


class SedDocumentLog(Log):
    """ Log of a SED document

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        tasks (:obj:`dict` of :obj:`str` to :obj:`TaskLog`): execution status of each
            task
        outputs (:obj:`dict` of :obj:`str` to :obj:`OutputLog`): execution status of each
            output
        parent (:obj:`CombineArchiveLog`): execution status of parent COMBINE/OMEX archive
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None,
                 tasks=None, outputs=None, parent=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            tasks (:obj:`dict` of :obj:`str` to :obj:`TaskLog`, optional): execution status of each
                task
            outputs (:obj:`dict` of :obj:`str` to :obj:`OutputLog`, optional): execution status of each
                output
            parent (:obj:`CombineArchiveLog`, optional): execution status of parent COMBINE/OMEX archive
            out_dir (:obj:`str`, optional): directory to export status
        """
        super(SedDocumentLog, self).__init__(status=status, exception=exception,
                                             skip_reason=skip_reason, output=output,
                                             duration=duration, parent=parent, out_dir=out_dir)
        self.tasks = tasks
        self.outputs = outputs

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(SedDocumentLog, self).finalize()

        if self.tasks:
            for task in self.tasks.values():
                task.finalize()

        if self.outputs:
            for output in self.outputs.values():
                output.finalize()

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        value = super(SedDocumentLog, self).to_dict()
        value['tasks'] = (
            {task_id: (task_log.to_dict() if task_log else None) for task_id, task_log in self.tasks.items()}
            if self.tasks is not None
            else None
        )
        value['outputs'] = (
            {output_id: (output_log.to_dict() if output_log else None) for output_id, output_log in self.outputs.items()}
            if self.outputs is not None
            else None
        )
        return value


class TaskLog(Log):
    """ Log of a SED task

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        algorithm (:obj:`str`): KiSAO id of the requested algorithm
        simulator_details (:obj:`dict`): additional simulator-specific information
        parent (:obj:`SedDocumentLog`): execution status of parent SED document
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None,
                 algorithm=None, simulator_details=None, parent=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            algorithm (:obj:`str`, optional): KiSAO id of the executed algorithm
            simulator_details (:obj:`dict`, optional): additional simulator-specific information
            parent (:obj:`SedDocumentLog`): execution status of parent SED document
            out_dir (:obj:`str`, optional): directory to export status
        """
        super(TaskLog, self).__init__(status=status, exception=exception,
                                      skip_reason=skip_reason, output=output,
                                      duration=duration, parent=parent, out_dir=out_dir)
        self.algorithm = algorithm
        self.simulator_details = simulator_details

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        value = super(TaskLog, self).to_dict()
        value['algorithm'] = self.algorithm
        value['simulatorDetails'] = self.simulator_details
        return value


class OutputLog(Log):
    """ Log of a SED output

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        parent (:obj:`SedDocumentLog`): execution status of parent SED document
        out_dir (:obj:`str`): directory to export status
    """
    pass  # pragma: no cover


class ReportLog(OutputLog):
    """ Log of a SED report

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        data_sets (:obj:`dict` of :obj:`str` to :obj:`Status`): execution status of each
            data set
        parent (:obj:`SedDocumentLog`): execution status of parent SED document
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None, data_sets=None,
                 parent=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            data_sets (:obj:`dict` of :obj:`str` to :obj:`Status`, optional): execution status of each
                data set
            parent (:obj:`SedDocumentLog`, optional): execution status of parent SED document
            out_dir (:obj:`str`, optional): directory to export status
        """
        super(ReportLog, self).__init__(status=status, exception=exception, skip_reason=skip_reason,
                                        output=output, duration=duration, parent=parent, out_dir=out_dir)
        self.data_sets = data_sets

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(ReportLog, self).finalize()

        if self.data_sets:
            for id, status in self.data_sets.items():
                if status == Status.QUEUED:
                    self.data_sets[id] = Status.SKIPPED
                elif status == Status.RUNNING:
                    self.data_sets[id] = Status.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        dict_log = super(ReportLog, self).to_dict()
        dict_log['dataSets'] = (
            {id: status.value if status else None for id, status in self.data_sets.items()}
            if self.data_sets is not None
            else None
        )
        return dict_log


class Plot2DLog(OutputLog):
    """ Log of a 2D SED plot

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        curves (:obj:`dict` of :obj:`str` to :obj:`Status`): execution status of each
            curve
        parent (:obj:`SedDocumentLog`): execution status of parent SED document
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None, curves=None,
                 parent=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            curves (:obj:`dict` of :obj:`str` to :obj:`Status`, optional): execution status of each
                curve
            parent (:obj:`SedDocumentLog`, optional): execution status of parent SED document
            out_dir (:obj:`str`, optional): directory to export status
        """
        super(Plot2DLog, self).__init__(status=status, exception=exception, skip_reason=skip_reason,
                                        output=output, duration=duration, parent=parent, out_dir=out_dir)
        self.curves = curves

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(Plot2DLog, self).finalize()

        if self.curves:
            for id, status in self.curves.items():
                if status == Status.QUEUED:
                    self.curves[id] = Status.SKIPPED
                elif status == Status.RUNNING:
                    self.curves[id] = Status.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        dict_log = super(Plot2DLog, self).to_dict()
        dict_log['curves'] = (
            {id: status.value if status else None for id, status in self.curves.items()}
            if self.curves is not None
            else None
        )
        return dict_log


class Plot3DLog(OutputLog):
    """ Log of a 3D SED plot

    Attributes
        status (:obj:`Status`): execution status of the archive
        exception (:obj:`Exception`): exception
        skip_reason (:obj:`Exception`): reason of skip
        output (:obj:`str`): output
        duration (:obj:`float`): duration in seconds
        surfaces (:obj:`dict` of :obj:`str` to :obj:`Status`): execution status of each
            surface
        parent (:obj:`SedDocumentLog`): execution status of parent SED document
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, exception=None, skip_reason=None, output=None, duration=None, surfaces=None,
                 parent=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            exception (:obj:`Exception`, optional): exception
            skip_reason (:obj:`Exception`, optional): reason of skip
            output (:obj:`str`, optional): output
            duration (:obj:`float`, optional): duration in seconds
            surfaces (:obj:`dict` of :obj:`str` to :obj:`Status`, optional): execution status of each
                surface
            parent (:obj:`SedDocumentLog`, optional): execution status of parent SED document
            out_dir (:obj:`str`, optional): directory to export status
        """
        super(Plot3DLog, self).__init__(status=status, exception=exception, skip_reason=skip_reason,
                                        output=output, duration=duration, parent=parent, out_dir=out_dir)
        self.surfaces = surfaces

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(Plot3DLog, self).finalize()

        if self.surfaces:
            for id, status in self.surfaces.items():
                if status == Status.QUEUED:
                    self.surfaces[id] = Status.SKIPPED
                elif status == Status.RUNNING:
                    self.surfaces[id] = Status.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        dict_log = super(Plot3DLog, self).to_dict()
        dict_log['surfaces'] = (
            {id: status.value if status else None for id, status in self.surfaces.items()}
            if self.surfaces is not None
            else None
        )
        return dict_log
