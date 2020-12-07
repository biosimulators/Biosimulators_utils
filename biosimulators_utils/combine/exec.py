""" Utilities for executing tasks in SED-ML files in COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

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


def exec_sedml_docs_in_archive(filename, sed_task_executer, out_dir, apply_xml_model_changes=False):
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
                    '''
                    pass

        out_dir (:obj:`str`): directory to store the outputs of the archive
        apply_xml_model_changes (:obj:`bool`): if :obj:`True`, apply any model changes specified in the SED-ML files before
            calling :obj:`task_executer`.
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
            biosimulators_utils.sedml.exec.exec_doc(os.path.join(archive_tmp_dir, content.location),
                     sed_task_executer,
                     os.path.join(out_dir, os.path.splitext(content.location)[0]),
                     apply_xml_model_changes=apply_xml_model_changes)

    # cleanup temporary files
    shutil.rmtree(archive_tmp_dir)
