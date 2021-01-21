""" Methods for generating SED plots

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import Plot2D, Plot3D  # noqa: F401
from ..report.data_model import DataGeneratorResults  # noqa: F401
from ..warnings import warn
from .data_model import PlotFormat
from .warnings import IllogicalPlotWarning
from matplotlib import cm as ColorMap
from matplotlib import pyplot
import matplotlib  # noqa: F401
import os


__all__ = ['write_plot_2d', 'write_plot_3d']


def write_plot_2d(plot, data_generator_results, base_path, rel_path, format=PlotFormat.pdf, style='seaborn-paper'):
    """ Generate a 2D plot

    Args:
        plot (:obj:`Plot2D`): description of plot
        data_generator_results (:obj:`DataGeneratorResults`): results of data generators
        base_path (:obj:`str`): base path to save plot
        rel_path (:obj:`str`): path to save results relative to :obj:`base_path`
        format (:obj:`PlotFormat`, optional): format
        style (:obj:`str`, optional): matplotlib style
    """
    figure = pyplot.figure()
    axes = figure.gca()

    x_names = set()
    y_names = set()

    x_scales = set()
    y_scales = set()

    curve_names = []
    for curve in plot.curves:
        x_id = curve.x_data_generator.id
        y_id = curve.y_data_generator.id

        x_result = data_generator_results[x_id]
        y_result = data_generator_results[y_id]

        with pyplot.style.context(style):
            axes.plot(x_result, y_result)

        x_name = curve.x_data_generator.name or x_id
        y_name = curve.y_data_generator.name or y_id
        x_names.add(x_name)
        y_names.add(y_name)

        x_scales.add(curve.x_scale)
        y_scales.add(curve.y_scale)

        curve_names.append(curve.name or curve.id)

    with pyplot.style.context(style):
        if len(x_names) == 1:
            axes.set_xlabel(list(x_names)[0])
        else:
            warn('A title could not be inferred for the X axis because the X data generators have inconsistent names.',
                 IllogicalPlotWarning)
            axes.set_xlabel('X')
        if len(y_names) == 1:
            axes.set_ylabel(list(y_names)[0])
        else:
            warn('A title could not be inferred for the Y axis because the Y data generators have inconsistent names.',
                 IllogicalPlotWarning)
            axes.set_ylabel('Y')

        if len(x_scales) == 1:
            axes.set_xscale(list(x_scales)[0].value)
        else:
            warn('Curves have inconsistent x axis scales. All curves will be plotted in linear scale.',
                 IllogicalPlotWarning)
        if len(y_scales) == 1:
            axes.set_yscale(list(y_scales)[0].value)
        else:
            warn('Curves have inconsistent y axis scales. All curves will be plotted in linear scale.',
                 IllogicalPlotWarning)

        if len(plot.curves) > 1:
            axes.legend(curve_names)

    dirname = os.path.dirname(os.path.join(os.path.join(base_path, rel_path)))
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    figure.savefig(os.path.join(base_path, rel_path + '.' + format.value))


def write_plot_3d(plot, data_generator_results, base_path, rel_path, format=PlotFormat.pdf,
                  style='seaborn-paper',
                  colormaps=[ColorMap.viridis, ColorMap.plasma, ColorMap.inferno, ColorMap.magma, ColorMap.cividis]):
    """ Generate a 3D plot

    Args:
        plot (:obj:`Plot3D`): description of plot
        data_generator_results (:obj:`DataGeneratorResults`): results of data generators
        base_path (:obj:`str`): base path to save plot
        rel_path (:obj:`str`): path to save results relative to :obj:`base_path`
        format (:obj:`PlotFormat`, optional): format
        style (:obj:`str`, optional): matplotlib style
        colormaps (:obj:`list` of :obj:`matplotlib.colors.LinearSegmentedColormap`, optional): colormaps
    """
    figure = pyplot.figure()
    axes = figure.gca(projection='3d')

    x_names = set()
    y_names = set()
    z_names = set()

    x_scales = set()
    y_scales = set()
    z_scales = set()

    plotted_surfaces = []
    surface_names = []
    for i_surfacce, surface in enumerate(plot.surfaces):
        x_id = surface.x_data_generator.id
        y_id = surface.y_data_generator.id
        z_id = surface.z_data_generator.id

        x_result = data_generator_results[x_id]
        y_result = data_generator_results[y_id]
        z_result = data_generator_results[z_id]

        with pyplot.style.context(style):
            plotted_surfaces.append(axes.plot_surface(x_result, y_result, z_result, cmap=colormaps[i_surfacce % len(colormaps)]))

        x_name = surface.x_data_generator.name or x_id
        y_name = surface.y_data_generator.name or y_id
        z_name = surface.z_data_generator.name or z_id
        x_names.add(x_name)
        y_names.add(y_name)
        z_names.add(z_name)

        x_scales.add(surface.x_scale)
        y_scales.add(surface.y_scale)
        z_scales.add(surface.z_scale)

        surface_names.append(surface.name or surface.id)

    with pyplot.style.context(style):
        if len(x_names) == 1:
            axes.set_xlabel(list(x_names)[0])
        else:
            warn('A title could not be inferred for the X axis because the X data generators have inconsistent names.',
                 IllogicalPlotWarning)
            axes.set_xlabel('X')
        if len(y_names) == 1:
            axes.set_ylabel(list(y_names)[0])
        else:
            warn('A title could not be inferred for the Y axis because the Y data generators have inconsistent names.',
                 IllogicalPlotWarning)
            axes.set_ylabel('Y')
        if len(z_names) == 1:
            axes.set_zlabel(list(z_names)[0])
        else:
            warn('A title could not be inferred for the Z axis because the Z data generators have inconsistent names.',
                 IllogicalPlotWarning)
            axes.set_zlabel('Z')

        if len(x_scales) == 1:
            axes.set_xscale(list(x_scales)[0].value)
        else:
            warn('Curves have inconsistent x axis scales. All surfaces will be plotted in linear scale.',
                 IllogicalPlotWarning)
        if len(y_scales) == 1:
            axes.set_yscale(list(y_scales)[0].value)
        else:
            warn('Curves have inconsistent y axis scales. All surfaces will be plotted in linear scale.',
                 IllogicalPlotWarning)
        if len(z_scales) == 1:
            axes.set_zscale(list(z_scales)[0].value)
        else:
            warn('Curves have inconsistent z axis scales. All surfaces will be plotted in linear scale.',
                 IllogicalPlotWarning)

        for plotted_surface, surface_name in zip(plotted_surfaces, surface_names):
            colorbar = figure.colorbar(plotted_surface)
            colorbar.ax.set_title(surface_name)

    dirname = os.path.dirname(os.path.join(os.path.join(base_path, rel_path)))
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    figure.savefig(os.path.join(base_path, rel_path + '.' + format.value))
