""" Utilities for working with models referenced by SED documents

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-04-05
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from ..combine.io import CombineArchiveWriter
from ..config import Config  # noqa: F401
from .data_model import (  # noqa: F401
    SedDocument, Model, ModelLanguage, ModelLanguagePattern, ModelAttributeChange, Simulation,
    Task, Variable, DataGenerator, Report, DataSet, Plot, Plot2D, Curve, Surface)
from .exceptions import UnsupportedModelLanguageError
from .io import SedmlSimulationWriter
import copy
import os
import re
import shutil
import tempfile
import types  # noqa: F401


__all__ = ['get_parameters_variables_outputs_for_simulation', 'build_combine_archive_for_model']


def get_parameters_variables_outputs_for_simulation(model_filename, model_language, simulation_type, algorithm_kisao_id=None,
                                                    change_level=SedDocument, native_ids=False, native_data_types=False,
                                                    model_language_options=None):
    """ Get the possible observables for a simulation of a model

    This method supports the following formats

    * SBML
    * SBML-fbc
    * SBML-qual

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`str`): model language (e.g., ``urn:sedml:language:sbml``)
        simulation_type (:obj:`types.Type`): subclass of :obj:`Simulation`
        algorithm_kisao_id (:obj:`str`, optional): KiSAO id of the algorithm for simulating the model (e.g., ``KISAO_0000019``
            for CVODE)
        change_level (:obj:`types.Type`, optional): level at which model changes will be made (:obj:`SedDocument` or :obj:`Task`)
        native_ids (:obj:`bool`, optional): whether to return the raw id and name of each model component rather than the suggested name
            for the variable of an associated SED-ML data generator
        native_data_types (:obj:`bool`, optional): whether to return new_values in their native data types
        model_language_options (:obj:`dict`, optional): additional options to pass to the methods for individual model formats.
            Dictionary that maps model languages (:obj:`ModelLanguage`) to dictionaries of optional keyword arguments for
            each language

    Returns:
        :obj:`list` of :obj:`ModelAttributeChange`: possible attributes of a model that can be changed and their default values
        :obj:`list` of :obj:`Simulation`: simulation of the model
        :obj:`list` of :obj:`Variable`: possible observables for a simulation of the model
        :obj:`list` of :obj:`Plot`: possible plots of the results of a simulation of the model

    Raises:
        :obj:`UnsupportedModelLanguageError`: if :obj:`model_language` is not a supported language
    """
    if model_language_options is None:
        model_language_options = {}

    # functions are imported here to only import libraries for required model languages
    if model_language and re.match(ModelLanguagePattern.BNGL.value, model_language):
        from biosimulators_utils.model_lang.bngl.utils import get_parameters_variables_outputs_for_simulation

    elif model_language and re.match(ModelLanguagePattern.CellML.value, model_language):
        from biosimulators_utils.model_lang.cellml.utils import get_parameters_variables_outputs_for_simulation

    elif model_language and re.match(ModelLanguagePattern.LEMS.value, model_language):
        # from biosimulators_utils.model_lang.lems.utils import get_parameters_variables_outputs_for_simulation
        raise UnsupportedModelLanguageError(
            'Models of language `{}` are not supported'.format(model_language))

    elif model_language and re.match(ModelLanguagePattern.RBA.value, model_language):
        from biosimulators_utils.model_lang.rba.utils import get_parameters_variables_outputs_for_simulation

    elif model_language and re.match(ModelLanguagePattern.SBML.value, model_language):
        from biosimulators_utils.model_lang.sbml.utils import get_parameters_variables_outputs_for_simulation

    elif model_language and re.match(ModelLanguagePattern.Smoldyn.value, model_language):
        from biosimulators_utils.model_lang.smoldyn.utils import get_parameters_variables_outputs_for_simulation

    elif model_language and re.match(ModelLanguagePattern.XPP.value, model_language):
        from biosimulators_utils.model_lang.xpp.utils import get_parameters_variables_outputs_for_simulation

    else:
        raise UnsupportedModelLanguageError(
            'Models of language `{}` are not supported'.format(model_language))

    return get_parameters_variables_outputs_for_simulation(
        model_filename, model_language, simulation_type, algorithm_kisao_id=algorithm_kisao_id,
        change_level=change_level, native_ids=native_ids, native_data_types=native_data_types,
        **model_language_options.get(model_language, {}),
    )


def build_combine_archive_for_model(model_filename, model_language, simulation_type, archive_filename, extra_contents=None,
                                    config=None,
                                    **model_language_options):
    """ Build A COMBINE/OMEX archive with a SED-ML file for a model

    Args:
        model_filename (:obj:`str`): path to model file
        model_language (:obj:`ModelLanguage`): model language
        simulation_type (:obj:`type`): subclass of :obj:`Simulation`
        archive_filename (:obj:`str`): path to save COMBINE/OMEX archive
        extra_contents (:obj:`dict` of :obj:`str` -> :obj:`CombineArchiveContent`, optional): dictionary that maps the
            local paths of additional files to include in the COMBINE/OMEX archive to their intended locations within the
            COMBINE/OMEX archive
        config (:obj:`Config`, optional): whether to fail on missing includes
        **model_language_options: additional options to pass to the methods for individual model formats
    """

    # make a SED-ML document for the model
    params, sims, vars, plots = get_parameters_variables_outputs_for_simulation(
        model_filename, model_language, simulation_type, **model_language_options)

    sedml_doc = SedDocument()
    model = Model(
        id='model',
        source=os.path.basename(model_filename),
        language=model_language.value,
        changes=params,
    )
    sedml_doc.models.append(model)
    for i_sim, sim in enumerate(sims):
        sedml_doc.simulations.append(sim)

        if len(sims) > 1:
            sim_suffix = '_' + str(i_sim)
        else:
            sim_suffix = ''

        task = Task(
            id='task' + sim_suffix,
            model=model,
            simulation=sim,
        )
        sedml_doc.tasks.append(task)

        report = Report(
            id='report' + sim_suffix,
        )
        sedml_doc.outputs.append(report)

        var_data_gen_map = {}

        for var in vars:
            var_copy = copy.copy(var)
            var_copy.id = '{}{}'.format(var_copy.id, sim_suffix)
            var_copy.task = task
            data_gen = DataGenerator(
                id='data_generator{}_{}'.format(sim_suffix, var_copy.id),
                name=var_copy.name,
                variables=[var_copy],
                math=var_copy.id,
            )
            sedml_doc.data_generators.append(data_gen)
            var_data_gen_map[var] = data_gen

            report.data_sets.append(DataSet(
                id='data_set{}_{}'.format(sim_suffix, var_copy.id),
                label=var_copy.id,
                name=var_copy.name,
                data_generator=data_gen,
            ))

        for plot in plots:
            plot_copy = copy.copy(plot)
            plot_copy.id = '{}{}'.format(plot_copy.id, sim_suffix)

            if isinstance(plot, Plot2D):
                plot_copy.curves = []
                for curve in plot.curves:
                    assert len(curve.x_data_generator.variables) == 1
                    assert len(curve.y_data_generator.variables) == 1
                    assert curve.x_data_generator.math == curve.x_data_generator.variables[0].id
                    assert curve.y_data_generator.math == curve.y_data_generator.variables[0].id

                    plot_copy.curves.append(Curve(
                        id='{}{}'.format(curve.id, sim_suffix),
                        name=curve.name,
                        x_data_generator=var_data_gen_map[curve.x_data_generator.variables[0]],
                        y_data_generator=var_data_gen_map[curve.y_data_generator.variables[0]],
                        x_scale=curve.x_scale,
                        y_scale=curve.y_scale,
                    ))

            else:
                plot_copy.surfaces = []
                for surface in plot.surfaces:
                    assert len(curve.x_data_generator.variables) == 1
                    assert len(curve.y_data_generator.variables) == 1
                    assert len(curve.z_data_generator.variables) == 1
                    assert curve.x_data_generator.math == curve.x_data_generator.variables[0].id
                    assert curve.y_data_generator.math == curve.y_data_generator.variables[0].id
                    assert curve.z_data_generator.math == curve.z_data_generator.variables[0].id

                    plot_copy.curves.append(Surface(
                        id='{}{}'.format(curve.id, sim_suffix),
                        name=curve.name,
                        x_data_generator=var_data_gen_map[curve.x_data_generator.variables[0]],
                        y_data_generator=var_data_gen_map[curve.y_data_generator.variables[0]],
                        z_data_generator=var_data_gen_map[curve.z_data_generator.variables[0]],
                        x_scale=curve.x_scale,
                        y_scale=curve.y_scale,
                        z_scale=curve.z_scale,
                    ))

            sedml_doc.outputs.append(plot_copy)

    # make temporary directory for archive
    archive_dirname = tempfile.mkdtemp()
    shutil.copyfile(model_filename, os.path.join(archive_dirname, os.path.basename(model_filename)))

    SedmlSimulationWriter().run(sedml_doc, os.path.join(archive_dirname, 'simulation.sedml'), config=config)

    # form a description of the archive
    archive = CombineArchive()
    archive.contents.append(CombineArchiveContent(
        location=os.path.basename(model_filename),
        format=CombineArchiveContentFormat[model_language.name].value,
    ))
    archive.contents.append(CombineArchiveContent(
        location='simulation.sedml',
        format=CombineArchiveContentFormat.SED_ML.value,
    ))
    for local_path, extra_content in (extra_contents or {}).items():
        shutil.copyfile(local_path, os.path.join(archive_dirname, extra_content.location))
        archive.contents.append(extra_content)

    # save archive to file
    CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

    # clean up temporary directory for archive
    shutil.rmtree(archive_dirname)
