""" Utilities for working with COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchive  # noqa: F401
from ..combine.utils import get_sedml_contents
from ..sedml.data_model import Report, Plot2D, Plot3D
from ..sedml.io import SedmlSimulationReader
from .data_model import (ExecutionStatus, CombineArchiveExecutionStatus, SedDocumentExecutionStatus,
                         TaskExecutionStatus, ReportExecutionStatus, Plot2DExecutionStatus, Plot3DExecutionStatus)
import os

__all__ = ['init_combine_archive_exec_status']


def init_combine_archive_exec_status(archive, archive_dir):
    """ Initialize the execution status of the SED documents in a COMBINE/OMEX archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dir (:obj:`str`): path where the content of the archive is located

    Returns:
        :obj:`CombineArchiveExecutionStatus`: initial execution status of the SED documents in an archive
    """
    contents = get_sedml_contents(archive, include_non_executing_docs=False)

    status = CombineArchiveExecutionStatus(status=ExecutionStatus.QUEUED)
    for content in contents:
        content_filename = os.path.join(archive_dir, content.location)
        doc = SedmlSimulationReader().run(content_filename)

        doc_id = os.path.relpath(content_filename, archive_dir)

        doc_status = SedDocumentExecutionStatus(status=ExecutionStatus.QUEUED, combine_archive_status=status)
        status.sed_documents[doc_id] = doc_status

        for task in doc.tasks:
            task_status = TaskExecutionStatus(status=ExecutionStatus.QUEUED, document_status=doc_status)
            doc_status.tasks[task.id] = task_status

        for output in doc.outputs:
            if isinstance(output, Report):
                output_status = ReportExecutionStatus(status=ExecutionStatus.QUEUED, document_status=doc_status)
                for data_set in output.data_sets:
                    output_status.data_sets[data_set.id] = ExecutionStatus.QUEUED

            elif isinstance(output, Plot2D):
                output_status = Plot2DExecutionStatus(status=ExecutionStatus.QUEUED, document_status=doc_status)
                for curve in output.curves:
                    output_status.curves[curve.id] = ExecutionStatus.QUEUED

            elif isinstance(output, Plot3D):
                output_status = Plot3DExecutionStatus(status=ExecutionStatus.QUEUED, document_status=doc_status)
                for surface in output.surfaces:
                    output_status.surfaces[surface.id] = ExecutionStatus.QUEUED

            else:
                raise NotImplementedError()  # pragma: no cover # uncreachable

            doc_status.outputs[output.id] = output_status

    return status
