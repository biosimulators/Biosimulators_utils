""" Utilities for working with COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchive  # noqa: F401
from ..combine.utils import get_sedml_contents
from ..sedml.data_model import SedDocument, Task, Report, Plot2D, Plot3D
from ..sedml.io import SedmlSimulationReader
from .data_model import (ExecutionStatus, CombineArchiveExecutionStatus, SedDocumentExecutionStatus,
                         TaskExecutionStatus, ReportExecutionStatus, Plot2DExecutionStatus, Plot3DExecutionStatus)
import os

__all__ = ['init_combine_archive_exec_status']


def init_combine_archive_exec_status(archive, archive_dir,
                                     supported_features=(CombineArchive, SedDocument, Task, Report)):
    """ Initialize the execution status of the SED documents in a COMBINE/OMEX archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dir (:obj:`str`): path where the content of the archive is located
        supported_features (:obj:`list` of :obj:`type`, optional): list of supported SED elements.
            Default: COMBINE/OMEX archives, SED documents, SED tasks, and SED reports

    Returns:
        :obj:`CombineArchiveExecutionStatus`: initial execution status of the SED documents in an archive
    """
    contents = get_sedml_contents(archive, include_non_executing_docs=False)

    status_value = ExecutionStatus.QUEUED if isinstance(archive, supported_features) else ExecutionStatus.SKIPPED
    status = CombineArchiveExecutionStatus(status=status_value)
    for content in contents:
        content_filename = os.path.join(archive_dir, content.location)
        doc = SedmlSimulationReader().run(content_filename)

        doc_id = os.path.relpath(content_filename, archive_dir)

        doc_status_value = ExecutionStatus.QUEUED if isinstance(doc, supported_features) else ExecutionStatus.SKIPPED
        doc_status = SedDocumentExecutionStatus(status=doc_status_value, combine_archive_status=status)
        status.sed_documents[doc_id] = doc_status

        for task in doc.tasks:
            el_status_value = ExecutionStatus.QUEUED if isinstance(task, supported_features) else ExecutionStatus.SKIPPED
            task_status = TaskExecutionStatus(status=el_status_value, document_status=doc_status)
            doc_status.tasks[task.id] = task_status

        for output in doc.outputs:
            output_status_value = ExecutionStatus.QUEUED if isinstance(output, supported_features) else ExecutionStatus.SKIPPED

            if isinstance(output, Report):
                output_status = ReportExecutionStatus(status=output_status_value, document_status=doc_status)
                for data_set in output.data_sets:
                    output_status.data_sets[data_set.id] = output_status_value

            elif isinstance(output, Plot2D):
                output_status = Plot2DExecutionStatus(status=output_status_value, document_status=doc_status)
                for curve in output.curves:
                    output_status.curves[curve.id] = output_status_value

            elif isinstance(output, Plot3D):
                output_status = Plot3DExecutionStatus(status=output_status_value, document_status=doc_status)
                for surface in output.surfaces:
                    output_status.surfaces[surface.id] = output_status_value

            else:
                raise NotImplementedError()  # pragma: no cover # uncreachable

            doc_status.outputs[output.id] = output_status

    return status
