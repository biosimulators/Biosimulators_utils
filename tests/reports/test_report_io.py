from biosimulators_utils.report import data_model
from biosimulators_utils.report import io
import unittest


class ReportIoTestCase(unittest.TestCase):
    def test_write_errors(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportWriter().run(None, None, None, format='TSV')

    def test_read_errors(self):
        with self.assertRaisesRegex(NotImplementedError, 'is not supported'):
            io.ReportReader().run(None, None, format='TSV')
