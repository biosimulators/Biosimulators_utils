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
    'Status',
    'CombineArchiveLog',
    'SedDocumentLog',
    'TaskLog',
    'OutLog',
    'ReportLog',
    'Plot2DLog',
    'Plot3DLog',
]


class Status(str, enum.Enum):
    """ Execution status of a component of a COMBINE/OMEX archive """
    QUEUED = 'QUEUED'

    RUNNING = 'RUNNING'

    SUCCEEDED = 'SUCCEEDED'

    SKIPPED = 'SKIPPED'
    # component will not / wasn't executed e.g., a plot won't be created because a
    # simulation doesn't have the ability to create plots

    FAILED = 'FAILED'


class CombineArchiveLog(object):
    """ Execution status of a COMBINE/OMEX archive

    Attributes
        status (:obj:`Status`): execution status of the archive
        sed_documents (:obj:`dict` of :obj:`str` to :obj:`SedDocumentLog`): execution status of each
            SED document in the archive
        out_dir (:obj:`str`): directory to export status
    """

    def __init__(self, status=None, sed_documents=None, out_dir=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            sed_documents (:obj:`dict` of :obj:`str` to :obj:`SedDocumentLog`, optional): execution status of each
                SED document in the archive
            out_dir (:obj:`str`, optional): directory to export status
        """
        self.status = status
        self.sed_documents = sed_documents or {}
        self.out_dir = out_dir

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == Status.QUEUED:
            self.status = Status.SKIPPED
        elif self.status == Status.RUNNING:
            self.status = Status.FAILED

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
        path = os.path.join(self.out_dir, get_config().LOG_PATH)
        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)
        with open(path, 'w') as file:
            file.write(yaml.dump(self.to_dict()))


class SedDocumentLog(object):
    """ Execution status of a SED document

    Attributes
        status (:obj:`Status`): execution status of the archive
        tasks (:obj:`dict` of :obj:`str` to :obj:`TaskLog`): execution status of each
            task
        outputs (:obj:`dict` of :obj:`str` to :obj:`OutLog`): execution status of each
            output
        combine_archive_status (:obj:`CombineArchiveLog`): execution status of parent COMBINE/OMEX archive
    """

    def __init__(self, status=None, tasks=None, outputs=None, combine_archive_status=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            tasks (:obj:`dict` of :obj:`str` to :obj:`TaskLog`, optional): execution status of each
                task
            outputs (:obj:`dict` of :obj:`str` to :obj:`OutLog`, optional): execution status of each
                output
            combine_archive_status (:obj:`CombineArchiveLog`, optional): execution status of parent COMBINE/OMEX archive
        """
        self.status = status
        self.tasks = tasks or {}
        self.outputs = outputs or {}
        self.combine_archive_status = combine_archive_status

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == Status.QUEUED:
            self.status = Status.SKIPPED
        elif self.status == Status.RUNNING:
            self.status = Status.FAILED

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


class TaskLog(object):
    """ Execution status of a SED task

    Attributes
        status (:obj:`Status`): execution status of the task
        document_status (:obj:`SedDocumentLog`): execution status of parent SED document
    """

    def __init__(self, status=None, document_status=None):
        """
        Args:
            status (:obj:`Status`): execution status of the task
            document_status (:obj:`SedDocumentLog`, optional): execution status of parent SED document
        """
        self.status = status
        self.document_status = document_status

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == Status.QUEUED:
            self.status = Status.SKIPPED
        elif self.status == Status.RUNNING:
            self.status = Status.FAILED

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


class OutLog(object):
    """ Execution status of a SED output

    Attributes
        status (:obj:`Status`): execution status of the archive
        document_status (:obj:`SedDocumentLog`): execution status of parent SED document
    """

    def __init__(self, status=None, document_status=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            document_status (:obj:`SedDocumentLog`, optional): execution status of parent SED document
        """
        self.status = status
        self.document_status = document_status

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        if self.status == Status.QUEUED:
            self.status = Status.SKIPPED
        elif self.status == Status.RUNNING:
            self.status = Status.FAILED

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


class ReportLog(OutLog):
    """ Execution status of a SED report

    Attributes
        status (:obj:`Status`): execution status of the archive
        data_sets (:obj:`dict` of :obj:`str` to :obj:`Status`): execution status of each
            data set
        document_status (:obj:`SedDocumentLog`): execution status of parent SED document
    """

    def __init__(self, status=None, data_sets=None, document_status=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            data_sets (:obj:`dict` of :obj:`str` to :obj:`Status`, optional): execution status of each
                data set
            document_status (:obj:`SedDocumentLog`, optional): execution status of parent SED document
        """
        super(ReportLog, self).__init__(status=status, document_status=document_status)
        self.data_sets = data_sets or {}

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(ReportLog, self).finalize()

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
        dict_status = super(ReportLog, self).to_dict()
        dict_status['dataSets'] = {id: status.value if status else None for id, status in self.data_sets.items()}
        return dict_status


class Plot2DLog(OutLog):
    """ Execution status of a 2D SED plot

    Attributes
        status (:obj:`Status`): execution status of the archive
        curves (:obj:`dict` of :obj:`str` to :obj:`Status`): execution status of each
            curve
        document_status (:obj:`SedDocumentLog`): execution status of parent SED document
    """

    def __init__(self, status=None, curves=None, document_status=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            curves (:obj:`dict` of :obj:`str` to :obj:`Status`, optional): execution status of each
                curve
            document_status (:obj:`SedDocumentLog`, optional): execution status of parent SED document
        """
        super(Plot2DLog, self).__init__(status=status, document_status=document_status)
        self.curves = curves or {}

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(Plot2DLog, self).finalize()

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
        dict_status = super(Plot2DLog, self).to_dict()
        dict_status['curves'] = {id: status.value if status else None for id, status in self.curves.items()}
        return dict_status


class Plot3DLog(OutLog):
    """ Execution status of a 3D SED plot

    Attributes
        status (:obj:`Status`): execution status of the archive
        surfaces (:obj:`dict` of :obj:`str` to :obj:`Status`): execution status of each
            surface
        document_status (:obj:`SedDocumentLog`): execution status of parent SED document
    """

    def __init__(self, status=None, surfaces=None, document_status=None):
        """
        Args:
            status (:obj:`Status`, optional): execution status of the archive
            surfaces (:obj:`dict` of :obj:`str` to :obj:`Status`, optional): execution status of each
                surface
            document_status (:obj:`SedDocumentLog`, optional): execution status of parent SED document
        """
        super(Plot3DLog, self).__init__(status=status, document_status=document_status)
        self.surfaces = surfaces or {}

    def finalize(self):
        """ Mark all unexceuted elements as skipped """
        super(Plot3DLog, self).finalize()

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
        dict_status = super(Plot3DLog, self).to_dict()
        dict_status['surfaces'] = {id: status.value if status else None for id, status in self.surfaces.items()}
        return dict_status
