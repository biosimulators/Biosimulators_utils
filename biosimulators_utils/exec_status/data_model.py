""" Data model for the execution status of COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_config
import enum
import itertools
import os
import yaml

__all__ = [
    'ExecutionStatus',
    'CombineArchiveExecutionStatus',
    'SedDocumentExecutionStatus',
    'TaskExecutionStatus',
    'OutputExecutionStatus',
    'ReportExecutionStatus',
    'Plot2DExecutionStatus',
    'Plot3DExecutionStatus',
]


class ExecutionStatus(str, enum.Enum):
    """ Execution status of a component of a COMBINE/OMEX archive """
    QUEUED = 'QUEUED'

    RUNNING = 'RUNNING'

    SUCCEEDED = 'SUCCEEDED'

    SKIPPED = 'SKIPPED'
    # component will not / wasn't executed e.g., a plot won't be created because a
    # simulation doesn't have the ability to create plots

    FAILED = 'FAILED'


class CombineArchiveExecutionStatus(object):
    """ Execution status of a COMBINE/OMEX archive

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the archive
        sed_documents (:obj:`dict` of :obj:`str` to :obj:`SedDocumentExecutionStatus`): execution status of each
            SED document in the archive
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, sed_documents=None, out_dir=None):
        """
        Args:
            status (:obj:`ExecutionStatus`, optional): execution status of the archive
            sed_documents (:obj:`dict` of :obj:`str` to :obj:`SedDocumentExecutionStatus`, optional): execution status of each
                SED document in the archive
            out_dir (:obj:`str`, optional): directory to export status
        """
        self.status = status
        self.sed_documents = sed_documents or {}
        self.out_dir = out_dir

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == ExecutionStatus.QUEUED:
            self.status = ExecutionStatus.SKIPPED
        elif self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.FAILED

        for sed_document in self.sed_documents.values():
            sed_document.finalize()

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        return {
            'status': self.status.value if self.status else None,
            'sedDocuments': {doc_id: doc_status.to_dict() for doc_id, doc_status in self.sed_documents.items()},
        }

    def export(self):
        """ Write to a file """
        path = os.path.join(self.out_dir, get_config().EXEC_STATUS_PATH)
        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)
        with open(path, 'w') as file:
            file.write(yaml.dump(self.to_dict()))


class SedDocumentExecutionStatus(object):
    """ Execution status of a SED document

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the archive
        tasks (:obj:`dict` of :obj:`str` to :obj:`TaskExecutionStatus`): execution status of each
            task
        outputs (:obj:`dict` of :obj:`str` to :obj:`OutputExecutionStatus`): execution status of each
            output
        combine_archive_status (:obj:`CombineArchiveExecutionStatus`): execution status of parent COMBINE/OMEX archive
    """

    def __init__(self, status=None, tasks=None, outputs=None, combine_archive_status=None):
        """
        Args:
            status (:obj:`ExecutionStatus`, optional): execution status of the archive
            tasks (:obj:`dict` of :obj:`str` to :obj:`TaskExecutionStatus`, optional): execution status of each
                task
            outputs (:obj:`dict` of :obj:`str` to :obj:`OutputExecutionStatus`, optional): execution status of each
                output
            combine_archive_status (:obj:`CombineArchiveExecutionStatus`, optional): execution status of parent COMBINE/OMEX archive
        """
        self.status = status
        self.tasks = tasks or {}
        self.outputs = outputs or {}
        self.combine_archive_status = combine_archive_status

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == ExecutionStatus.QUEUED:
            self.status = ExecutionStatus.SKIPPED
        elif self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.FAILED

        for el in itertools.chain(self.tasks.values(), self.outputs.values()):
            el.finalize()

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        return {
            'status': self.status.value if self.status else None,
            'tasks': {task_id: task_status.to_dict() for task_id, task_status in self.tasks.items()},
            'outputs': {output_id: output_status.to_dict() for output_id, output_status in self.outputs.items()},
        }

    def export(self):
        """ Write to a file """
        self.combine_archive_status.export()


class TaskExecutionStatus(object):
    """ Execution status of a SED task

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the task
        document_status (:obj:`SedDocumentExecutionStatus`): execution status of parent SED document
    """

    def __init__(self, status=None, document_status=None):
        """
        Args:
            status (:obj:`ExecutionStatus`): execution status of the task
            document_status (:obj:`SedDocumentExecutionStatus`, optional): execution status of parent SED document
        """
        self.status = status
        self.document_status = document_status

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == ExecutionStatus.QUEUED:
            self.status = ExecutionStatus.SKIPPED
        elif self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        return {
            'status': self.status.value if self.status else None,
        }

    def export(self):
        """ Write to a file """
        self.document_status.export()


class OutputExecutionStatus(object):
    """ Execution status of a SED output

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the archive
        document_status (:obj:`SedDocumentExecutionStatus`): execution status of parent SED document
    """

    def __init__(self, status=None, document_status=None):
        """
        Args:
            status (:obj:`ExecutionStatus`, optional): execution status of the archive
            document_status (:obj:`SedDocumentExecutionStatus`, optional): execution status of parent SED document
        """
        self.status = status
        self.document_status = document_status

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == ExecutionStatus.QUEUED:
            self.status = ExecutionStatus.SKIPPED
        elif self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        return {
            'status': self.status.value if self.status else None,
        }

    def export(self):
        """ Write to a file """
        self.document_status.export()


class ReportExecutionStatus(OutputExecutionStatus):
    """ Execution status of a SED report

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the archive
        data_sets (:obj:`dict` of :obj:`str` to :obj:`ExecutionStatus`): execution status of each
            data set
        document_status (:obj:`SedDocumentExecutionStatus`): execution status of parent SED document
    """

    def __init__(self, status=None, data_sets=None, document_status=None):
        """
        Args:
            status (:obj:`ExecutionStatus`, optional): execution status of the archive
            data_sets (:obj:`dict` of :obj:`str` to :obj:`ExecutionStatus`, optional): execution status of each
                data set
            document_status (:obj:`SedDocumentExecutionStatus`, optional): execution status of parent SED document
        """
        super(ReportExecutionStatus, self).__init__(status=status, document_status=document_status)
        self.data_sets = data_sets or {}

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(ReportExecutionStatus, self).finalize()

        for id, status in self.data_sets.items():
            if status == ExecutionStatus.QUEUED:
                self.data_sets[id] = ExecutionStatus.SKIPPED
            elif status == ExecutionStatus.RUNNING:
                self.data_sets[id] = ExecutionStatus.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        dict_status = super(ReportExecutionStatus, self).to_dict()
        dict_status['dataSets'] = {id: status.value if status else None for id, status in self.data_sets.items()}
        return dict_status


class Plot2DExecutionStatus(OutputExecutionStatus):
    """ Execution status of a 2D SED plot

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the archive
        curves (:obj:`dict` of :obj:`str` to :obj:`ExecutionStatus`): execution status of each
            curve
        document_status (:obj:`SedDocumentExecutionStatus`): execution status of parent SED document
    """

    def __init__(self, status=None, curves=None, document_status=None):
        """
        Args:
            status (:obj:`ExecutionStatus`, optional): execution status of the archive
            curves (:obj:`dict` of :obj:`str` to :obj:`ExecutionStatus`, optional): execution status of each
                curve
            document_status (:obj:`SedDocumentExecutionStatus`, optional): execution status of parent SED document
        """
        super(Plot2DExecutionStatus, self).__init__(status=status, document_status=document_status)
        self.curves = curves or {}

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(Plot2DExecutionStatus, self).finalize()

        for id, status in self.curves.items():
            if status == ExecutionStatus.QUEUED:
                self.curves[id] = ExecutionStatus.SKIPPED
            elif status == ExecutionStatus.RUNNING:
                self.curves[id] = ExecutionStatus.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        dict_status = super(Plot2DExecutionStatus, self).to_dict()
        dict_status['curves'] = {id: status.value if status else None for id, status in self.curves.items()}
        return dict_status


class Plot3DExecutionStatus(OutputExecutionStatus):
    """ Execution status of a 3D SED plot

    Attributes
        status (:obj:`ExecutionStatus`): execution status of the archive
        surfaces (:obj:`dict` of :obj:`str` to :obj:`ExecutionStatus`): execution status of each
            surface
        document_status (:obj:`SedDocumentExecutionStatus`): execution status of parent SED document
    """

    def __init__(self, status=None, surfaces=None, document_status=None):
        """
        Args:
            status (:obj:`ExecutionStatus`, optional): execution status of the archive
            surfaces (:obj:`dict` of :obj:`str` to :obj:`ExecutionStatus`, optional): execution status of each
                surface
            document_status (:obj:`SedDocumentExecutionStatus`, optional): execution status of parent SED document
        """
        super(Plot3DExecutionStatus, self).__init__(status=status, document_status=document_status)
        self.surfaces = surfaces or {}

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(Plot3DExecutionStatus, self).finalize()

        for id, status in self.surfaces.items():
            if status == ExecutionStatus.QUEUED:
                self.surfaces[id] = ExecutionStatus.SKIPPED
            elif status == ExecutionStatus.RUNNING:
                self.surfaces[id] = ExecutionStatus.FAILED

    def to_dict(self):
        """ Generate a JSON-compatible representation

        Returns:
            :obj:`dict`: JSON-compatible representation
        """
        dict_status = super(Plot3DExecutionStatus, self).to_dict()
        dict_status['surfaces'] = {id: status.value if status else None for id, status in self.surfaces.items()}
        return dict_status
