from biosimulators_utils.report.data_model import DataGeneratorResults
from biosimulators_utils.sedml.data_model import Plot2D, Curve, Plot3D, Surface, AxisScale, DataGenerator
from biosimulators_utils.viz import io
from biosimulators_utils.viz.data_model import VizFormat
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

    def test_write_plot_2d_one_curve(self):
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
        format = VizFormat.pdf

        io.write_plot_2d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

    def test_write_plot_2d_multiple_curves(self):
        time = DataGenerator(id='time')
        species_a = DataGenerator(id='species_a')
        species_b = DataGenerator(id='species_b')

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
                Curve(
                    id='curve_2',
                    name='Curve 2',
                    x_data_generator=time,
                    y_data_generator=species_b,
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                ),
            ]
        )

        data_gen_results = DataGeneratorResults()
        data_gen_results[time.id] = numpy.linspace(0., 10., 100 + 1)
        data_gen_results[species_a.id] = numpy.sin(data_gen_results[time.id])
        data_gen_results[species_b.id] = numpy.cos(data_gen_results[time.id])

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = VizFormat.pdf

        io.write_plot_2d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

    def test_write_plot_2d_mixed_axes(self):
        species_a = DataGenerator(id='species_a')
        species_b = DataGenerator(id='species_b')

        plot = Plot2D(
            id='plot_1',
            curves=[
                Curve(
                    id='curve_1',
                    name='Curve 1',
                    x_data_generator=species_a,
                    y_data_generator=species_a,
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.log,
                ),
                Curve(
                    id='curve_2',
                    name='Curve 2',
                    x_data_generator=species_b,
                    y_data_generator=species_b,
                    x_scale=AxisScale.log,
                    y_scale=AxisScale.linear,
                ),
            ]
        )

        data_gen_results = DataGeneratorResults()
        time = numpy.linspace(0., 10., 100 + 1)
        data_gen_results[species_a.id] = numpy.sin(time)
        data_gen_results[species_b.id] = numpy.cos(time)

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = VizFormat.pdf

        io.write_plot_2d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

    def test_write_plot_2d_multidimensional(self):
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
        time_data = numpy.linspace(0., 10., 100 + 1)
        shape = (1, 1, 101)
        data_gen_results[time.id] = numpy.concatenate(
            (
                numpy.concatenate(
                    (
                        time_data.reshape(shape),
                        time_data.reshape(shape),
                        time_data.reshape(shape),
                    ),
                    1),
                numpy.concatenate(
                    (
                        time_data.reshape(shape),
                        time_data.reshape(shape),
                        time_data.reshape(shape),
                    ),
                    1)
            ),
            0
        )
        data_gen_results[species_a.id] = numpy.concatenate(
            (
                numpy.concatenate(
                    (
                        numpy.sin(time_data + 0/16 * numpy.pi).reshape(shape),
                        numpy.sin(time_data + 1/16 * numpy.pi).reshape(shape),
                        numpy.sin(time_data + 2/16 * numpy.pi).reshape(shape),
                    ),
                    1),
                numpy.concatenate(
                    (
                        numpy.sin(time_data + 3/16 * numpy.pi).reshape(shape),
                        numpy.sin(time_data + 4/16 * numpy.pi).reshape(shape),
                        numpy.sin(time_data + 5/16 * numpy.pi).reshape(shape),
                    ),
                    1)
            ),
            0
        )
        self.assertEqual(data_gen_results[time.id].shape, (2, 3, 101))

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = VizFormat.pdf

        io.write_plot_2d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

        data_gen_results[species_a.id] = numpy.sin(time_data + 0/16 * numpy.pi).reshape(shape)
        io.write_plot_2d(plot, data_gen_results, base_path, rel_path, format=format)

    def test_write_plot_3d_one_surface(self):
        x = DataGenerator(id='x')
        y = DataGenerator(id='y')
        species_a = DataGenerator(id='species_a')

        plot = Plot3D(
            id='plot_1',
            surfaces=[
                Surface(
                    id='surface_1',
                    name='Surface 1',
                    x_data_generator=x,
                    y_data_generator=y,
                    z_data_generator=species_a,
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                    z_scale=AxisScale.linear,
                ),
            ]
        )

        X = numpy.arange(-5, 5, 0.25)
        Y = numpy.arange(-5, 5, 0.25)
        X, Y = numpy.meshgrid(X, Y)
        Z = numpy.sin(numpy.sqrt(X**2 + Y**2))

        data_gen_results = DataGeneratorResults()
        data_gen_results[x.id] = X
        data_gen_results[y.id] = Y
        data_gen_results[species_a.id] = Z

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = VizFormat.pdf

        io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

    def test_write_plot_3d_multiple_surfaces(self):
        x = DataGenerator(id='x')
        y = DataGenerator(id='y')
        species_a = DataGenerator(id='species_a')
        species_b = DataGenerator(id='species_b')

        plot = Plot3D(
            id='plot_1',
            surfaces=[
                Surface(
                    id='surface_1',
                    name='Surface 1',
                    x_data_generator=x,
                    y_data_generator=y,
                    z_data_generator=species_a,
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                    z_scale=AxisScale.linear,
                ),
                Surface(
                    id='surface_2',
                    name='Surface 2',
                    x_data_generator=y,
                    y_data_generator=x,
                    z_data_generator=species_b,
                    x_scale=AxisScale.log,
                    y_scale=AxisScale.log,
                    z_scale=AxisScale.log,
                ),
            ],
        )

        X = numpy.arange(-5, 5, 0.25)
        Y = numpy.arange(-5, 5, 0.25)
        X, Y = numpy.meshgrid(X, Y)
        A = numpy.sin(numpy.sqrt(X**2 + Y**2))
        B = numpy.cos(numpy.sqrt(X**2 + Y**2))

        data_gen_results = DataGeneratorResults()
        data_gen_results[x.id] = X
        data_gen_results[y.id] = Y
        data_gen_results[species_a.id] = A
        data_gen_results[species_b.id] = B

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = VizFormat.pdf

        io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

    def test_write_plot_3d_multidimensional(self):
        x = DataGenerator(id='x')
        y = DataGenerator(id='y')
        species_a = DataGenerator(id='species_a')

        plot = Plot3D(
            id='plot_1',
            surfaces=[
                Surface(
                    id='surface_1',
                    name='Surface 1',
                    x_data_generator=x,
                    y_data_generator=y,
                    z_data_generator=species_a,
                    x_scale=AxisScale.linear,
                    y_scale=AxisScale.linear,
                    z_scale=AxisScale.linear,
                ),
            ]
        )

        X = numpy.arange(-5, 5, 0.25)
        Y = numpy.arange(-5, 5, 0.25)
        X, Y = numpy.meshgrid(X, Y)
        Z = numpy.sin(numpy.sqrt(X**2 + Y**2))

        X = X.reshape((1, 40, 40))
        Y = Y.reshape((1, 40, 40))
        Z = Z.reshape((1, 40, 40))

        data_gen_results = DataGeneratorResults()
        data_gen_results[x.id] = numpy.concatenate((X, X + 50), 0)
        data_gen_results[y.id] = numpy.concatenate((Y, Y + 50), 0)
        data_gen_results[species_a.id] = numpy.concatenate((Z, Z), 0)

        base_path = self.dirname
        rel_path = 'path/to/sim.sedml/' + plot.id
        format = VizFormat.pdf

        io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)

        self.assertTrue(os.path.isfile(os.path.join(base_path, 'path/to/sim.sedml/plot_1.pdf')))

        data_gen_results[x.id] = numpy.concatenate((X, X, X + 50), 0)
        data_gen_results[y.id] = Y
        data_gen_results[species_a.id] = Z
        io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)

        data_gen_results[x.id] = X
        data_gen_results[y.id] = numpy.concatenate((Y, Y, Y + 50), 0)
        data_gen_results[species_a.id] = Z
        io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)

        data_gen_results[x.id] = numpy.concatenate((X, X, X + 50), 0)
        data_gen_results[y.id] = numpy.concatenate((Y, Y, Y + 50), 0)
        data_gen_results[species_a.id] = Z
        io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)

        data_gen_results[x.id] = numpy.concatenate((X, X, X + 50), 0)
        data_gen_results[y.id] = numpy.concatenate((Y, Y), 0)
        data_gen_results[species_a.id] = numpy.concatenate((Z, Z), 0)
        with self.assertRaisesRegex(ValueError, 'must have consistent shapes'):
            io.write_plot_3d(plot, data_gen_results, base_path, rel_path, format=format)
