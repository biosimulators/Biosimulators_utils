from biosimulators_utils.report import data_model
from biosimulators_utils.report import io
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
            io.ReportWriter().run(None, None, None, format='TSV')

    def test_read_errors(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportReader().run(None, None, format='TSV')

    def test_get_ids(self):
        data = numpy.array([[1, 2, 3], [4, 5, 6]])
        df = pandas.DataFrame(data, index=['A', 'B'])

        for format in [data_model.ReportFormat.h5, data_model.ReportFormat.csv]:
            filename = os.path.join(self.dirname, 'test')
            io.ReportWriter().run(df, filename, 'a/b/c.sedml/report1', format=format)
            io.ReportWriter().run(df, filename, 'a/b/c.sedml/report2', format=format)
            io.ReportWriter().run(df, filename, 'a/b/c.sedml/report3', format=format)
            io.ReportWriter().run(df, filename, 'a/b/d.sedml/report4', format=format)
            io.ReportWriter().run(df, filename, 'a/b/report5', format=format)
            io.ReportWriter().run(df, filename, 'a/b/report6', format=format)

            self.assertEqual(io.ReportReader().get_ids(filename, format=format), set([
                'a/b/c.sedml/report1',
                'a/b/c.sedml/report2',
                'a/b/c.sedml/report3',
                'a/b/d.sedml/report4',
                'a/b/report5',
                'a/b/report6',
            ]))
