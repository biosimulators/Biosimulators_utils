""" Utilities for working with COMBINE/OMEX archives

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-06
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import Report, Plot2D, Plot3D
from ..sedml.io import SedmlSimulationReader
from .data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormatPattern  # noqa: F401
import os
import re

__all__ = ['get_sedml_contents', 'get_summary_sedml_contents']


def get_sedml_contents(archive, include_non_executing_docs=False):
    """ Get the SED-ML files in an archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        include_non_executing_docs (:obj:`bool`, optional): if :obj:`False`, only
            return the documents which should be executed

    Returns:
        :obj:`list` of :obj:`CombineArchiveContent`: SED-ML files in a COMBINE/OMEX archive
    """

    master_content = archive.get_master_content()
    if master_content and not include_non_executing_docs:
        potential_content = [master_content]
    else:
        potential_content = archive.contents

    sedml_contents = []
    for content in potential_content:
        if content.format and re.match(CombineArchiveContentFormatPattern.SED_ML.value, content.format):
            sedml_contents.append(content)
    sedml_contents.sort(key=lambda content: content.location)

    return sedml_contents


def get_summary_sedml_contents(archive, archive_dir, include_non_executing_docs=False):
    """ Get a summary of the SED-ML content in a COMBINE/OMEX archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dir (:obj:`str`): path where the content of the archive is located
        include_non_executing_docs (:obj:`bool`, optional): if :obj:`False`, only
            return the documents which should be executed

    Returns:
        :obj:`str`: summary of the SED-ML content in a COMBINE/OMEX archive
    """
    contents = get_sedml_contents(archive, include_non_executing_docs=include_non_executing_docs)

    n_docs = 0
    n_models = 0
    n_simulations = 0
    n_tasks = 0
    n_reports = 0
    n_plots = 0
    for i_content, content in enumerate(contents):
        n_docs += 1

        content_filename = os.path.join(archive_dir, content.location)
        doc = SedmlSimulationReader().run(content_filename)

        n_models += len(doc.models)
        n_simulations += len(doc.simulations)
        n_tasks += len(doc.tasks)
        for output in doc.outputs:
            if isinstance(output, Report):
                n_reports += 1
            else:
                n_plots += 1
    summary = 'Found {} SED-ML documents with {} models, {} simulations, {} tasks, {} reports, and {} plots:\n'.format(
        n_docs, n_models, n_simulations, n_tasks, n_reports, n_plots)

    for i_content, content in enumerate(sorted(contents, key=lambda content: content.location)):
        content_filename = os.path.join(archive_dir, content.location)
        doc = SedmlSimulationReader().run(content_filename)
        content_id = os.path.relpath(content_filename, archive_dir)
        summary += '  {}:\n'.format(content_id)

        sorted_tasks = sorted(doc.tasks, key=lambda task: task.id)
        sorted_reports = sorted((output for output in doc.outputs if isinstance(output, Report)), key=lambda output: output.id)
        sorted_plots = sorted((output for output in doc.outputs if isinstance(output, (Plot2D, Plot3D))), key=lambda output: output.id)

        if sorted_tasks:
            summary += '    Tasks ({}):\n'.format(len(sorted_tasks))
            for task in sorted_tasks:
                summary += '      {}\n'.format(task.id)

        if sorted_reports:
            summary += '    Reports ({}):\n'.format(len(sorted_reports))
            for output in sorted_reports:
                summary += '      {}: {} data sets\n'.format(output.id, len(output.data_sets))

        if sorted_plots:
            summary += '    Plots ({}):\n'.format(len(sorted_plots))
            for output in sorted_plots:
                if isinstance(output, Plot2D):
                    summary += '      {}: {} curves\n'.format(output.id, len(output.curves))
                elif isinstance(output, Plot3D):
                    summary += '      {}: {} surfaces\n'.format(output.id, len(output.surfaces))

    return summary
