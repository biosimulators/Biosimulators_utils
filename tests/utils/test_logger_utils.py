from biosimulators_utils.utils import logging
import os
import shutil
import tempfile
import unittest


class LoggingTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        shutil.rmtree(self.tmp_dir)

    def tearDown(self):
        if os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test(self):
        filename_pattern = os.path.join(self.tmp_dir, '{}.log')
        log1 = logging.get_logger(filename_pattern=filename_pattern)
        log2 = logging.get_logger(filename_pattern=filename_pattern)
        self.assertIs(log1, log2)

        log1.info('test')
