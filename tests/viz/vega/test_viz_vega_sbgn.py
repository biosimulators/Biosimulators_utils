from biosimulators_utils.viz.vega.sbgn.core import sbgn_pd_map_to_vega
from biosimulators_utils.viz.vega.utils import dict_to_vega_dataset
from jsonschema import validate
from unittest import mock
import json
import os
import random
import requests
import shutil
import tempfile
import unittest


class SbgnVegaVisualizationTestCase(unittest.TestCase):
    SBGN_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'sbgn', 'Repressilator_PD_v6_color-modified.sbgn')

    def setUp(self):
        self.temp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dirname)

    def test(self):
        glyph_data_set = {
            'values': dict_to_vega_dataset({
                'LacI protein': self.gen_random_time_course(),
                'TetR protein': self.gen_random_time_course(),
                'cI protein': self.gen_random_time_course(),
                'LacI mRNA': self.gen_random_time_course(),
                'TetR mRNA': self.gen_random_time_course(),
                'cI mRNA': self.gen_random_time_course(),
            }),
        }

        vega_filename = os.path.join(self.temp_dirname, 'vg.json')

        # convert SBGN PD map to Vega
        sbgn_pd_map_to_vega(glyph_data_set, self.SBGN_FILENAME, vega_filename)

        # read visualization
        with open(vega_filename, 'r') as file:
            vega = json.load(file)

        # mock processing of SED-ML URIs
        signal_map = {signal['name']: i_signal for i_signal, signal in enumerate(vega['signals'])}
        vega['signals'][signal_map['OutputStartTime']] = {
            'name': 'OutputStartTime',
            'value': 5,
        }
        vega['signals'][signal_map['OutputEndTime']] = {
            'name': 'OutputEndTime',
            'value': 10,
        }
        vega['signals'][signal_map['NumberOfSteps']] = {
            'name': 'NumberOfSteps',
            'value': 5,
        }

        vega['signals'][signal_map['Time_step']] = {
            "name": "Time_step",
            "description": "Time step",
            "value": 0,
            "bind": {
                "input": "range",
                "min": 0,
                "max": 5,
                "step": 1
            }
        }

        # validate map is valid Vega
        schema_url = vega['$schema']
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()

        validate(instance=vega, schema=schema)

    def gen_random_time_course(self, len=6):
        return [random.random() for i in range(len)]
