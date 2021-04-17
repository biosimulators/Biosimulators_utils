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


def get_sedml_contents(archive,
                       include_all_sed_docs_when_no_sed_doc_is_master=True,
                       always_include_all_sed_docs=False):
    """ Get the SED-ML files in an archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        include_all_sed_docs_when_no_sed_doc_is_master (:obj:`bool`, optional): if :obj:`true`
            and no SED document has ``master="true"``, return all SED documents.
        always_include_all_sed_docs (:obj:`bool`, optional): if :obj:`true`,
            return all SED documents, regardless of whether they have ``master="true"`` or not.

    Returns:
        :obj:`list` of :obj:`CombineArchiveContent`: SED-ML files in a COMBINE/OMEX archive
    """

    sedml_contents = []
    master_sedml_contents = []
    for content in archive.contents:
        if (
            isinstance(content, CombineArchiveContent)
            and content.format
            and re.match(CombineArchiveContentFormatPattern.SED_ML.value, content.format)
        ):
            sedml_contents.append(content)
            if content.master:
                master_sedml_contents.append(content)

    if always_include_all_sed_docs:
        return sedml_contents
    else:
        if master_sedml_contents:
            return master_sedml_contents
        else:
            if include_all_sed_docs_when_no_sed_doc_is_master:
                return sedml_contents
            else:
                return []


def get_summary_sedml_contents(archive, archive_dir,
                               include_all_sed_docs_when_no_sed_doc_is_master=True,
                               always_include_all_sed_docs=False):
    """ Get a summary of the SED-ML content in a COMBINE/OMEX archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dir (:obj:`str`): path where the content of the archive is located
        include_all_sed_docs_when_no_sed_doc_is_master (:obj:`bool`, optional): if :obj:`true`
            and no SED document has ``master="true"``, return all SED documents.
        always_include_all_sed_docs (:obj:`bool`, optional): if :obj:`true`,
            return all SED documents, regardless of whether they have ``master="true"`` or not.

    Returns:
        :obj:`str`: summary of the SED-ML content in a COMBINE/OMEX archive
    """
    contents = get_sedml_contents(archive,
                                  include_all_sed_docs_when_no_sed_doc_is_master=include_all_sed_docs_when_no_sed_doc_is_master,
                                  always_include_all_sed_docs=always_include_all_sed_docs)

    n_docs = 0
    n_models = 0
    n_simulations = 0
    n_tasks = 0
    n_reports = 0
    n_plots = 0
    for i_content, content in enumerate(contents):
        n_docs += 1

        content_filename = os.path.join(archive_dir, content.location)
        doc = SedmlSimulationReader().run(content_filename, validate_models_with_languages=False)

        n_models += len(doc.models)
        n_simulations += len(doc.simulations)
        n_tasks += len(doc.tasks)
        for output in doc.outputs:
            if isinstance(output, Report):
                n_reports += 1
            else:
                n_plots += 1
    summary = 'Archive contains {} SED-ML documents with {} models, {} simulations, {} tasks, {} reports, and {} plots:\n'.format(
        n_docs, n_models, n_simulations, n_tasks, n_reports, n_plots)

    for i_content, content in enumerate(sorted(contents, key=lambda content: content.location)):
        content_filename = os.path.join(archive_dir, content.location)
        doc = SedmlSimulationReader().run(content_filename, validate_models_with_languages=False)
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
