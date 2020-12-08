""" Utilities for executing tasks in SED-ML files in COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..report.data_model import DataGeneratorVariableResults, OutputResults, ReportFormat  # noqa: F401
from ..sedml.data_model import Task, DataGeneratorVariable  # noqa: F401
from .io import CombineArchiveReader
import biosimulators_utils.sedml.exec
import os
import tempfile
import shutil
import types  # noqa: F401

__all__ = [
    'exec_sedml_docs_in_archive',
]

SEDML_SPECIFICATIONS_URL = 'http://identifiers.org/combine.specifications/sed-ml'


def exec_sedml_docs_in_archive(filename, sed_task_executer, out_path, apply_xml_model_changes=False,
                               report_formats=[ReportFormat.CSV, ReportFormat.HDF5]):
    """ Execute the SED-ML files in a COMBINE/OMEX archive (execute tasks and save outputs)

    Args:
        filename (:obj:`str`): path to COMBINE archive
        sed_task_executer (:obj:`types.FunctionType`): function to execute each SED task in each SED-ML file in the archive.
            The function must implement the following interface::

                def exec_task(task, variables):
                    ''' Execute a simulation and return its results

                    Args:
                       task (:obj:`Task`): task
                       variables (:obj:`list` of :obj:`DataGeneratorVariable`): variables that should be recorded

                    Returns:
                        :obj:`tuple`:

                            * :obj:`OutputResults`: results of outputs
                            * :obj:`DataGeneratorVariableResults`: results of variables
                    '''
                    pass

        out_path (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{out_path}/{relative-path-to-SED-ML-file-within-archive}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{out_path}/reports.h5``),
              with reports at keys ``{relative-path-to-SED-ML-file-within-archive}/{report.id}`` within the HDF5 file

        apply_xml_model_changes (:obj:`bool`): if :obj:`True`, apply any model changes specified in the SED-ML files before
            calling :obj:`task_executer`.
        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., CSV or HDF5)
    """
    # create temporary directory to unpack archive
    archive_tmp_dir = tempfile.mkdtemp()

    # unpack archive and read metadata
    archive = CombineArchiveReader.run(filename, archive_tmp_dir)

    # determine files to execute
    master_content = archive.get_master_content()
    exec_content = [master_content] if master_content else archive.contents

    # execute SED-ML files: execute tasks and save outputs
    for content in exec_content:
        if content.format == SEDML_SPECIFICATIONS_URL:
            if os.path.isabs(content.location):
                raise ValueError('Content locations must be relative')
            filename = os.path.join(archive_tmp_dir, content.location)
            working_dir = os.path.dirname(filename)
            biosimulators_utils.sedml.exec.exec_doc(filename,
                                                    working_dir,
                                                    sed_task_executer,
                                                    out_path,
                                                    os.path.splitext(os.path.relpath(filename, archive_tmp_dir))[0],
                                                    apply_xml_model_changes=apply_xml_model_changes,
                                                    report_formats=report_formats)

    # cleanup temporary files
    shutil.rmtree(archive_tmp_dir)
