""" Methods for generating SED plots

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-12-23
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..sedml.data_model import Plot2D  # noqa: F401
from ..report.data_model import DataGeneratorResults  # noqa: F401
from .data_model import PlotFormat
from matplotlib import pyplot
import numpy
import os
import pandas
import seaborn


def write_plot_2d(data_generator_results, plot, base_path, rel_path, format=PlotFormat.pdf):
    """ Generate a 2D plot

    Args:
        data_generator_results (:obj:`DataGeneratorResults`): results of data generators
        plot (:obj:`Plot2D`): description of plot
        base_path (:obj:`str`): base path to save plot
        rel_path (:obj:`str`): path to save results relative to :obj:`base_path`
        format (:obj:`PlotFormat`, optional): format
    """
    x = data_generator_results['time']
    y = data_generator_results['species_a']
    data_frame = pandas.DataFrame(numpy.array([x, y]), index=["time", "species_a"]).transpose()
    g = seaborn.relplot(x="time", y="species_a", kind="line", data=data_frame)
    g.fig.autofmt_xdate()

    dirname = os.path.dirname(os.path.join(os.path.join(base_path, rel_path)))
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    pyplot.savefig(os.path.join(base_path, rel_path + '.' + format.value))
