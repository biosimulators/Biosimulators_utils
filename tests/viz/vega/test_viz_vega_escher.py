from biosimulators_utils.viz.vega.escher.core import escher_to_vega, read_escher_map_config
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


class EscherVegaVisualizationTestCase(unittest.TestCase):
    ESCHER_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'escher', 'e_coli_core.Core metabolism.json')

    def setUp(self):
        self.temp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dirname)

    def gen_fluxes(self):
        with open(self.ESCHER_FILENAME, 'r') as file:
            map = json.load(file)
        reaction_fluxes = {}
        for reaction in map[1]["reactions"].values():
            reaction_fluxes[reaction['bigg_id']] = random.random() * 2 - 1
        return reaction_fluxes

    def test_escher_to_vega(self):
        reaction_fluxes_data_set = {
            'values': dict_to_vega_dataset(self.gen_fluxes()),
        }

        vega_filename = os.path.join(self.temp_dirname, 'vg.json')

        escher_to_vega(reaction_fluxes_data_set, self.ESCHER_FILENAME, vega_filename)

        # test that file was created
        self.assertTrue(os.path.isfile(vega_filename))

        # read file (and test that its valid JSON)
        with open(vega_filename, 'r') as file:
            vega = json.load(file)

        # read the Vega schema for the file
        schema_url = vega['$schema']
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()

        # validate that the file adheres to Vega's schema
        validate(instance=vega, schema=schema)

    def test_escher_to_vega_tall(self):
        reaction_fluxes_data_set = {
            'values': dict_to_vega_dataset(self.gen_fluxes()),
        }
        vega_filename = os.path.join(self.temp_dirname, 'vg.json')

        map = read_escher_map_config(self.ESCHER_FILENAME)
        node_id = list(map[1]['nodes'].keys())[0]
        map[1]['nodes'][node_id]['y'] = 10000

        with mock.patch('biosimulators_utils.viz.vega.escher.core.read_escher_map_config', return_value=map):
            escher_to_vega(reaction_fluxes_data_set, self.ESCHER_FILENAME, vega_filename)

    def test_escher_to_vega_save_map_data_to_external_file(self):
        reaction_flux_data_filename = os.path.join(self.temp_dirname, 'fluxes.json')
        with open(reaction_flux_data_filename, 'w') as file:
            json.dump({'data': dict_to_vega_dataset(self.gen_fluxes())}, file)

        reaction_fluxes_data_set = {
            'url': 'http://localhost:3334/fluxes.json',
            'format': {
                'type': 'json',
                'property': 'data',
            }
        }

        vega_filename = os.path.join(self.temp_dirname, 'vg.json')
        metabolic_map_data_file = {
            'filename': os.path.join(self.temp_dirname, 'map.json'),
            'url': 'http://localhost:3334/map.json',
        }

        escher_to_vega(reaction_fluxes_data_set, self.ESCHER_FILENAME, vega_filename,
                       metabolic_map_data_file=metabolic_map_data_file)

        # test that file was created
        self.assertTrue(os.path.isfile(vega_filename))

        # read file (and test that its valid JSON)
        with open(vega_filename, 'r') as file:
            vega = json.load(file)

        # read the Vega schema for the file
        schema_url = vega['$schema']
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()

        # validate that the file adheres to Vega's schema
        validate(instance=vega, schema=schema)

    def test_escher_to_vega_read_simulation_results_from_biosimulations(self):
        reaction_fluxes_data_set = {
            'sedmlUri': ['simulation.sedml', 'report']
        }

        vega_filename = os.path.join(self.temp_dirname, 'vg.json')

        escher_to_vega(reaction_fluxes_data_set, self.ESCHER_FILENAME, vega_filename)

        # test that file was created
        self.assertTrue(os.path.isfile(vega_filename))

        # read file (and test that its valid JSON)
        with open(vega_filename, 'r') as file:
            vega = json.load(file)

        # read the Vega schema for the file
        schema_url = vega['$schema']
        response = requests.get(schema_url)
        response.raise_for_status()
        schema = response.json()

        # remove non-standard data description
        for data in vega['data']:
            if 'sedmlUri' in data:
                del data['sedmlUri']
                data['values'] = []

        # validate that the file adheres to Vega's schema
        validate(instance=vega, schema=schema)
