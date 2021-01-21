from biosimulators_utils.report import data_model
from biosimulators_utils.report import io
from biosimulators_utils.sedml.data_model import Report, DataSet
import numpy
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

    def test_write_errors(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportWriter().run(Report(), None, None, None, format='TSV')

    def test_read_errors(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportReader().run(Report(), None, None, format='TSV')

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

            self.assertEqual(io.ReportReader().get_ids(filename, format=format), set([
                'a/b/c.sedml/report1',
                'a/b/c.sedml/report2',
                'a/b/c.sedml/report3',
                'a/b/d.sedml/report4',
                'a/b/report5',
                'a/b/report6',
            ]))

        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportReader().get_ids(filename, format=None)
