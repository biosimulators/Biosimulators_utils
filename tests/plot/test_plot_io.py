from biosimulators_utils.plot import io
from biosimulators_utils.plot.data_model import PlotFormat
from biosimulators_utils.report.data_model import DataGeneratorResults
from biosimulators_utils.sedml.data_model import Plot2D, Curve, AxisScale, DataGenerator
import numpy
import os
import shutil
import tempfile
import unittest


class PlotIoTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_write_plot_2d(self):
        time = DataGenerator(id='time')
        species_a = DataGenerator(id='species_a')

        plot = Plot2D(
            id='plot_1',
            curves=[
                Curve(
                    id='curve_1',
                    name='Curve 1',
                    x_data_generator=time,
                    y_data_generator=species_a,
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                ),
            ]
        )

        data_gen_results = DataGeneratorResults()
        data_gen_results[time.id] = numpy.linspace(0., 10., 100 + 1)
        data_gen_results[species_a.id] = numpy.sin(data_gen_results[time.id])

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = PlotFormat.pdf

        io.write_plot_2d(data_gen_results, plot, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))
