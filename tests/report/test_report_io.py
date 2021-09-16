from biosimulators_utils.report import data_model
from biosimulators_utils.report import io
from biosimulators_utils.report.warnings import MissingDataWarning, ExtraDataWarning, CannotExportMultidimensionalTableWarning
from biosimulators_utils.sedml.data_model import Report, DataSet
import h5py
import numpy
import numpy.testing
import os
import pandas
import shutil
import tempfile
import unittest


class ReportIoTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_read_write(self):
        report_1 = Report(
            id='report_1',
            name='report 1',
            data_sets=[
                DataSet(id='w', label='W'),
                DataSet(id='x', label='X'),
                DataSet(id='y', label='Y'),
                DataSet(id='z', label='Z'),
            ],
        )
        report_2 = Report(
            id='report_2',
            name='report 2',
            data_sets=[
                DataSet(id='a', label='A'),
                DataSet(id='b', label='B'),
                DataSet(id='c', label='C'),
                DataSet(id='d', label='D'),
            ],
        )
        report_3 = Report(
            id='report_3',
            data_sets=[
                DataSet(id='a', label='A'),
                DataSet(id='b', label='B'),
                DataSet(id='c', label='C'),
                DataSet(id='d', label='D'),
            ],
        )
        data_set_results_1 = data_model.DataSetResults({
            'w': None,
            'x': numpy.array([1, 2, 3]),
            'y': numpy.array([4., numpy.nan]),
            'z': numpy.array(6.),
        })
        data_set_results_2 = data_model.DataSetResults({
            'a': numpy.array([1, 2]),
            'b': numpy.array([7., 8., 9.]),
            'c': numpy.array(True),
            'd': None,
        })
        data_set_results_3 = data_model.DataSetResults({
            'a': numpy.array([[1, 2], [3, 4], [5, 6]]),
            'b': numpy.array([7., 8., 9.]),
            'c': numpy.array(True),
            'd': None,
        })

        # CSV, TSV
        for format in [data_model.ReportFormat.csv, data_model.ReportFormat.tsv, data_model.ReportFormat.xlsx]:
            rel_path_1 = os.path.join(format.value, 'a/b/c.sedml', report_1.id)
            rel_path_2 = os.path.join(format.value, 'a/d.sedml', report_2.id)
            rel_path_3 = os.path.join(format.value, 'e.sedml', report_2.id)

            io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=format)
            io.ReportWriter().run(report_2, data_set_results_2, self.dirname, rel_path_2, format=format)
            with self.assertWarnsRegex(CannotExportMultidimensionalTableWarning, 'Multidimensional reports cannot be exported'):
                io.ReportWriter().run(report_3, data_set_results_3, self.dirname, rel_path_3, format=format)
            data_set_results_1_b = io.ReportReader().run(report_1, self.dirname, rel_path_1, format=format)
            data_set_results_2_b = io.ReportReader().run(report_2, self.dirname, rel_path_2, format=format)

            self.assertEqual(set(io.ReportReader().get_ids(self.dirname, format=format)), set([rel_path_1, rel_path_2]))

            numpy.testing.assert_allclose(data_set_results_1_b['w'], numpy.array([numpy.nan, numpy.nan, numpy.nan]))
            numpy.testing.assert_allclose(data_set_results_1_b['x'], numpy.array([1., 2., 3.]))
            numpy.testing.assert_allclose(data_set_results_1_b['y'], numpy.array([4., numpy.nan, numpy.nan]))
            numpy.testing.assert_allclose(data_set_results_1_b['z'], numpy.array([6., numpy.nan, numpy.nan]))

            self.assertEqual(data_set_results_1_b['w'].dtype.name, 'float64')
            self.assertEqual(data_set_results_1_b['x'].dtype.name, 'float64')
            self.assertEqual(data_set_results_1_b['y'].dtype.name, 'float64')
            self.assertEqual(data_set_results_1_b['z'].dtype.name, 'float64')

            numpy.testing.assert_allclose(data_set_results_2_b['a'], numpy.array([1., 2., numpy.nan]))
            numpy.testing.assert_allclose(data_set_results_2_b['b'], numpy.array([7., 8., 9.]))
            numpy.testing.assert_allclose(data_set_results_2_b['c'], numpy.array([1., numpy.nan, numpy.nan]))
            numpy.testing.assert_allclose(data_set_results_2_b['d'], numpy.array([numpy.nan, numpy.nan, numpy.nan]))

            self.assertEqual(data_set_results_2_b['a'].dtype.name, 'float64')
            self.assertEqual(data_set_results_2_b['b'].dtype.name, 'float64')
            self.assertEqual(data_set_results_2_b['c'].dtype.name, 'float64')
            self.assertEqual(data_set_results_2_b['d'].dtype.name, 'float64')

        # HDF
        for format in [data_model.ReportFormat.h5]:
            rel_path_1 = os.path.join(format.value, 'a/b/c.sedml', report_1.id)
            rel_path_2 = os.path.join(format.value, 'a/d.sedml', report_2.id)
            rel_path_3 = os.path.join(format.value, 'e.sedml', report_3.id)

            io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=format)
            io.ReportWriter().run(report_2, data_set_results_2, self.dirname, rel_path_2, format=format)
            io.ReportWriter().run(report_3, data_set_results_3, self.dirname, rel_path_3, format=format)
            data_set_results_1_b = io.ReportReader().run(report_1, self.dirname, rel_path_1, format=format)
            data_set_results_2_b = io.ReportReader().run(report_2, self.dirname, rel_path_2, format=format)
            data_set_results_3_b = io.ReportReader().run(report_3, self.dirname, rel_path_3, format=format)

            self.assertEqual(set(io.ReportReader().get_ids(self.dirname, format=format)), set([rel_path_1, rel_path_2, rel_path_3]))

            self.assertEqual(data_set_results_1_b['w'], None)
            numpy.testing.assert_allclose(data_set_results_1_b['x'], numpy.array([1, 2, 3]))
            numpy.testing.assert_allclose(data_set_results_1_b['y'], numpy.array([4., numpy.nan]))
            numpy.testing.assert_allclose(data_set_results_1_b['z'], numpy.array(6.))

            self.assertEqual(data_set_results_1_b['x'].dtype.name, 'int64')
            self.assertEqual(data_set_results_1_b['y'].dtype.name, 'float64')
            self.assertEqual(data_set_results_1_b['z'].dtype.name, 'float64')

            numpy.testing.assert_allclose(data_set_results_2_b['a'], numpy.array([1, 2]))
            numpy.testing.assert_allclose(data_set_results_2_b['b'], numpy.array([7., 8., 9.]))
            numpy.testing.assert_allclose(data_set_results_2_b['c'], numpy.array(True))
            self.assertEqual(data_set_results_2_b['d'], None)

            self.assertEqual(data_set_results_2_b['a'].dtype.name, 'int64')
            self.assertEqual(data_set_results_2_b['b'].dtype.name, 'float64')
            self.assertEqual(data_set_results_2_b['c'].dtype.name, 'bool')

            numpy.testing.assert_allclose(data_set_results_3_b['a'], numpy.array([[1, 2], [3, 4], [5, 6]]))
            numpy.testing.assert_allclose(data_set_results_3_b['b'], numpy.array([7., 8., 9.]))
            numpy.testing.assert_allclose(data_set_results_3_b['c'], numpy.array(True))
            self.assertEqual(data_set_results_3_b['d'], None)

            self.assertEqual(data_set_results_3_b['a'].dtype.name, 'int64')
            self.assertEqual(data_set_results_3_b['b'].dtype.name, 'float64')
            self.assertEqual(data_set_results_3_b['c'].dtype.name, 'bool')

            with h5py.File(os.path.join(self.dirname, 'reports.h5'), 'r') as file:
                self.assertEqual(file[format.value + '/a'].attrs, {
                    'uri': format.value + '/a',
                    'combineArchiveLocation': format.value + '/a',
                })
                self.assertEqual(file[format.value + '/a/b'].attrs, {
                    'uri': format.value + '/a/b',
                    'combineArchiveLocation': format.value + '/a/b',
                })
                self.assertEqual(file[format.value + '/a/b/c.sedml'].attrs, {
                    'uri': format.value + '/a/b/c.sedml',
                    'combineArchiveLocation': format.value + '/a/b/c.sedml',
                })
                self.assertEqual(file[format.value + '/a/d.sedml'].attrs, {
                    'uri': format.value + '/a/d.sedml',
                    'combineArchiveLocation': format.value + '/a/d.sedml',
                })
                self.assertEqual(file[format.value + '/e.sedml'].attrs, {
                    'uri': format.value + '/e.sedml',
                    'combineArchiveLocation': format.value + '/e.sedml',
                })

                self.assertEqual(file[format.value + '/a/b/c.sedml/' + report_1.id].attrs['uri'],
                                 format.value + '/a/b/c.sedml/' + report_1.id)
                self.assertEqual(file[format.value + '/a/b/c.sedml/' + report_1.id].attrs['sedmlId'], report_1.id)
                self.assertEqual(file[format.value + '/a/b/c.sedml/' + report_1.id].attrs['sedmlName'], report_1.name)

                self.assertEqual(file[format.value + '/a/d.sedml/' + report_2.id].attrs['uri'], format.value + '/a/d.sedml/' + report_2.id)
                self.assertEqual(file[format.value + '/a/d.sedml/' + report_2.id].attrs['sedmlId'], report_2.id)
                self.assertEqual(file[format.value + '/a/d.sedml/' + report_2.id].attrs['sedmlName'], report_2.name)

                self.assertEqual(file[format.value + '/e.sedml/' + report_3.id].attrs['uri'], format.value + '/e.sedml/' + report_3.id)
                self.assertEqual(file[format.value + '/e.sedml/' + report_3.id].attrs['sedmlId'], report_3.id)
                self.assertNotIn('sedmlName', file[format.value + '/e.sedml/' + report_3.id].attrs)

    def test_read_write_error_handling(self):
        report_1 = Report(
            id='report_1',
            data_sets=[
                DataSet(id='x', label='X'),
                DataSet(id='y', label='Y'),
                DataSet(id='z', label='Z'),
            ],
        )
        data_set_results_1 = data_model.DataSetResults({
            'x': numpy.array([1., 2.]),
            'y': numpy.array([3., 4.]),
            'z': numpy.array([5., 6.]),
        })

        rel_path_1 = os.path.join('a/b/c.sedml', report_1.id)

        io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)

        report_1.data_sets.append(DataSet(id='w', label='W'))
        with self.assertWarns(MissingDataWarning):
            io.ReportReader().run(report_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)

        report_1.data_sets.pop()
        report_1.data_sets.pop()
        with self.assertWarns(ExtraDataWarning):
            io.ReportReader().run(report_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)

        data_set_results_1['x'] = numpy.array([1., 2.], dtype=numpy.dtype('object'))
        with self.assertRaisesRegex(TypeError, 'NumPy dtype should be '):
            io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)

    def test_read_write_duplicate_labels(self):
        # labels in same order
        report_1 = Report(
            id='report_1',
            data_sets=[
                DataSet(id='x', label='A'),
                DataSet(id='y', label='A'),
                DataSet(id='z', label='A'),
            ],
        )
        data_set_results_1 = data_model.DataSetResults({
            'x': numpy.array([1., 2.]),
            'y': numpy.array([3., 4.]),
            'z': numpy.array([5., 6.]),
        })

        rel_path_1 = os.path.join('a/b/c.sedml', report_1.id)

        io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=data_model.ReportFormat.csv)
        data_set_results_2 = io.ReportReader().run(report_1, self.dirname, rel_path_1, format=data_model.ReportFormat.csv)

        numpy.testing.assert_allclose(data_set_results_2['x'], numpy.array([1., 2.]))
        numpy.testing.assert_allclose(data_set_results_2['y'], numpy.array([3., 4.]))
        numpy.testing.assert_allclose(data_set_results_2['z'], numpy.array([5., 6.]))

        # labels in different order
        report_1 = Report(
            id='report_1',
            data_sets=[
                DataSet(id='x', label='X'),
                DataSet(id='y', label='X'),
                DataSet(id='z', label='Z'),
            ],
        )
        data_set_results_1 = data_model.DataSetResults({
            'x': numpy.array([1., 2.]),
            'y': numpy.array([3., 4.]),
            'z': numpy.array([5., 6.]),
        })

        rel_path_1 = os.path.join('a/b/c.sedml', report_1.id)

        io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=data_model.ReportFormat.csv)

        report_2 = Report(
            id='report_1',
            data_sets=[
                DataSet(id='x', label='X'),
                DataSet(id='z', label='Z'),
                DataSet(id='y', label='X'),
            ],
        )
        data_set_results_2 = io.ReportReader().run(report_2, self.dirname, rel_path_1, format=data_model.ReportFormat.csv)

        self.assertEqual(set(data_set_results_2.keys()), set(['z']))
        numpy.testing.assert_allclose(data_set_results_2['z'], numpy.array([5., 6.]))

    def test_overwrite_report(self):
        report_1 = Report(
            id='report_1',
            data_sets=[
                DataSet(id='x', label='X'),
                DataSet(id='y', label='Y'),
                DataSet(id='z', label='Z'),
            ],
        )
        data_set_results_1 = data_model.DataSetResults({
            'x': numpy.array([1., 2.]),
            'y': numpy.array([3., 4.]),
            'z': numpy.array([5., 6.]),
        })

        rel_path_1 = os.path.join('a/b/c.sedml', report_1.id)

        io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)
        data_set_results_2 = io.ReportReader().run(report_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)

        numpy.testing.assert_allclose(data_set_results_2['x'], numpy.array([1., 2.]))
        numpy.testing.assert_allclose(data_set_results_2['y'], numpy.array([3., 4.]))
        numpy.testing.assert_allclose(data_set_results_2['z'], numpy.array([5., 6.]))

        data_set_results_1 = data_model.DataSetResults({
            'x': numpy.array([1., 2.]) + 1.,
            'y': numpy.array([3., 4.]) + 1.,
            'z': numpy.array([5., 6.]) + 1.,
        })

        io.ReportWriter().run(report_1, data_set_results_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)
        data_set_results_2 = io.ReportReader().run(report_1, self.dirname, rel_path_1, format=data_model.ReportFormat.h5)

        numpy.testing.assert_allclose(data_set_results_2['x'], numpy.array([1., 2.]) + 1.)
        numpy.testing.assert_allclose(data_set_results_2['y'], numpy.array([3., 4.]) + 1.)
        numpy.testing.assert_allclose(data_set_results_2['z'], numpy.array([5., 6.]) + 1.)

    def test_write_error_handling(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportWriter().run(Report(), None, None, 'a', format='TSV')

        report = Report(data_sets=[DataSet(id='x', label='x')])

        data_set_results = data_model.DataSetResults({'x': numpy.zeros((3, ))})
        io.ReportWriter().run(report, data_set_results, self.dirname, '.', format=data_model.ReportFormat.csv)

        data_set_results['x'] = data_set_results['x'].reshape((3, 1))
        with self.assertWarnsRegex(CannotExportMultidimensionalTableWarning, 'Multidimensional reports cannot be exported'):
            io.ReportWriter().run(report, data_set_results, self.dirname, '.', format=data_model.ReportFormat.csv)

    def test_read_error_handling(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportReader().run(Report(), None, 'a', format='TSV')

    def test_get_ids(self):
        report = Report(
            data_sets=[
                DataSet(id='A', label='A'),
                DataSet(id='B', label='A'),
            ],
        )

        results = data_model.DataSetResults({
            report.data_sets[0].id: numpy.array([1, 2, 3]),
            report.data_sets[1].id: numpy.array([4, 5, 6]),
        })

        for format in [data_model.ReportFormat.h5, data_model.ReportFormat.csv]:
            filename = os.path.join(self.dirname, 'test')
            io.ReportWriter().run(report, results, filename, 'a/b/c.sedml/report1', format=format)
            io.ReportWriter().run(report, results, filename, 'a/b/c.sedml/report2', format=format)
            io.ReportWriter().run(report, results, filename, 'a/b/c.sedml/report3', format=format)
            io.ReportWriter().run(report, results, filename, 'a/b/d.sedml/report4', format=format)
            io.ReportWriter().run(report, results, filename, 'a/b/report5', format=format)
            io.ReportWriter().run(report, results, filename, 'a/b/report6', format=format)

            self.assertEqual(set(io.ReportReader().get_ids(filename, format=format)), set([
                'a/b/c.sedml/report1',
                'a/b/c.sedml/report2',
                'a/b/c.sedml/report3',
                'a/b/d.sedml/report4',
                'a/b/report5',
                'a/b/report6',
            ]))

        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportReader().get_ids(filename, format=None)
