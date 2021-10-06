from biosimulators_utils.viz.vega.ginml import ginml_to_vega
import os
import shutil
import tempfile
import unittest


class GinmlVegaTestCase(unittest.TestCase):
    FIXTURES_DIRNAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'ginml')

    def setUp(self):
        self.temp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dirname)

    def test(self):
        data = {
            'values': []
        }

        # GINSim model 35
        ginml_filename = os.path.join(self.FIXTURES_DIRNAME, 'ginsim-35-regulatoryGraph.ginml')
        vega_filename = os.path.join(self.temp_dirname, 'vg.json')
        ginml_to_vega(data, ginml_filename, vega_filename)

        # GINSim model 79
        ginml_filename = os.path.join(self.FIXTURES_DIRNAME, 'ginsim-79-regulatoryGraph-expanded comments.ginml')
        vega_filename = os.path.join(self.temp_dirname, 'vg.json')
        ginml_to_vega(data, ginml_filename, vega_filename)
