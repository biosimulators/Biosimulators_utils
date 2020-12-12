""" Utilities for executing tasks in SED-ML files in COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..archive.io import ArchiveWriter
from ..archive.utils import build_archive_from_paths
from ..config import get_config
from ..report.data_model import DataGeneratorVariableResults, OutputResults, ReportFormat  # noqa: F401
from ..sedml.data_model import Task, DataGeneratorVariable  # noqa: F401
from .data_model import CombineArchiveContentFormatPattern
from .io import CombineArchiveReader
import biosimulators_utils.sedml.exec
import os
import re
import tempfile
import shutil
import types  # noqa: F401

__all__ = [
    'exec_sedml_docs_in_archive',
]


def exec_sedml_docs_in_archive(archive_filename, sed_task_executer, out_dir, apply_xml_model_changes=False,
                               report_formats=None):
    """ Execute the SED-ML files in a COMBINE/OMEX archive (execute tasks and save outputs)

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        sed_task_executer (:obj:`types.FunctionType`): function to execute each SED task in each SED-ML file in the archive.
            The function must implement the following interface::

                def exec_task(task, variables):
                    ''' Execute a simulation and return its results

                    Args:
                       task (:obj:`Task`): task
                       variables (:obj:`list` of :obj:`DataGeneratorVariable`): variables that should be recorded

                    Returns:
                       :obj:`DataGeneratorVariableResults`: results of variables
                    '''
                    pass

        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        apply_xml_model_changes (:obj:`bool`): if :obj:`True`, apply any model changes specified in the SED-ML files before
            calling :obj:`task_executer`.
        report_formats (:obj:`list` of :obj:`ReportFormat`, optional): report format (e.g., CSV or HDF5)
    """
    config = get_config()

    # process arguments
    if report_formats is None:
        report_formats = [ReportFormat(format_value) for format_value in config.REPORT_FORMATS]

    # create temporary directory to unpack archive
    archive_tmp_dir = tempfile.mkdtemp()

    # unpack archive and read metadata
    archive = CombineArchiveReader.run(archive_filename, archive_tmp_dir)

    # determine files to execute
    master_content = archive.get_master_content()
    exec_content = [master_content] if master_content else archive.contents

    # execute SED-ML files: execute tasks and save outputs
    tmp_out_dir = tempfile.mkdtemp()
    for content in exec_content:
        if re.match(CombineArchiveContentFormatPattern.SED_ML.value, content.format):
            if os.path.isabs(content.location):
                raise ValueError('Content locations must be relative')
            content_filename = os.path.join(archive_tmp_dir, content.location)
            working_dir = os.path.dirname(content_filename)
            biosimulators_utils.sedml.exec.exec_doc(content_filename,
                                                    working_dir,
                                                    sed_task_executer,
                                                    tmp_out_dir,
                                                    os.path.relpath(content_filename, archive_tmp_dir),
                                                    apply_xml_model_changes=apply_xml_model_changes,
                                                    report_formats=report_formats)

    # arrange outputs
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # move HDF5 file to desired location
    tmp_hdf5_path = os.path.join(tmp_out_dir, config.HDF5_REPORTS_PATH)
    out_hdf5_path = os.path.join(out_dir, config.HDF5_REPORTS_PATH)
    if os.path.isfile(tmp_hdf5_path):
        shutil.move(tmp_hdf5_path, out_hdf5_path)

    # bundle CSV files of reports into zip archive
    if ReportFormat.CSV in report_formats:
        archive = build_archive_from_paths([os.path.join(tmp_out_dir, '**', '*.csv')], tmp_out_dir)
        if archive.files:
            ArchiveWriter().run(archive, os.path.join(out_dir, config.CSV_REPORTS_PATH))

    # bundle PDF files of plots into zip archive
    archive = build_archive_from_paths([os.path.join(tmp_out_dir, '**', '*.pdf')], tmp_out_dir)
    if archive.files:
        ArchiveWriter().run(archive, os.path.join(out_dir, config.PDF_PLOTS_PATH))

    # cleanup temporary files
    shutil.rmtree(archive_tmp_dir)
    shutil.rmtree(tmp_out_dir)
