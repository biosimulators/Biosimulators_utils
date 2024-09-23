from biosimulators_utils.simulator.io import read_simulator_specs
from unittest import mock
import json
import os
import requests
import unittest
import tempfile


class SimulatorIoTestCase(unittest.TestCase):
    def test_file(self):
        url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_COPASI/dev/biosimulators.json'
        response = requests.get(url)
        response.raise_for_status()
        file, filename = tempfile.mkstemp(suffix='.json')
        os.close(file)
        content: str = str(response.content, encoding='utf-8')
        content = content.replace("__COPASI_VERSION__", "0.0.0")
        content = content.replace("__CONTAINER_DIGEST__",
                        "sha256:bf684e81eb8e6e6a313f8cae2bbebb57d794405e0416059667c2bacf47dadc81")
        content = content.replace("\\n", "\n")
        byte_content = content.encode("utf-8")
        with open(filename, 'wb') as file:
            file.write(byte_content)
        read_simulator_specs(filename)

        with self.assertRaisesRegex(ValueError, 'must be encoded into JSON'):
            path = __file__
            read_simulator_specs(path)

        specs = response.json()
        for alg_specs in specs['algorithms']:
            for param_specs in alg_specs['parameters'][0:1]:
                param_specs['kisaoId']['id'] = 'KISAO_0000107'
        with open(filename, 'w') as file:
            json.dump(specs, file)
        with self.assertRaisesRegex(ValueError, 'not an id of a child term of KISAO_0000201'):
            read_simulator_specs(filename)

        specs = response.json()
        for alg_specs in specs['algorithms'][0:1]:
            alg_specs['kisaoId']['id'] = 'KISAO_0000107'
        with open(filename, 'w') as file:
            json.dump(specs, file)
        with self.assertRaisesRegex(ValueError, 'not an id of a child term of KISAO_0000000'):
            read_simulator_specs(filename)

        os.remove(filename)

    def test_url(self):
        patch_version = "0.0.0"
        url = ('https://raw.githubusercontent.com/biosimulators/Biosimulators_COPASI'
               '/ff7a177128db282706d79daa281591d53cb79268/biosimulators.json')
        specs = read_simulator_specs(url, patch={'version': patch_version})
        self.assertEqual(specs['version'], '0.0.0')

        with self.assertRaises(requests.RequestException):
            url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_COPASI/dev/__undefined__'
            read_simulator_specs(url)

        with self.assertRaisesRegex(ValueError, 'must be encoded into JSON'):
            url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_COPASI/dev/README.md'
            read_simulator_specs(url)

        with mock.patch('requests.get', return_value=mock.Mock(raise_for_status=lambda: True, json=lambda: {})):
            with self.assertRaises(ValueError):
                url = 'https://raw.githubusercontent.com/biosimulators/Biosimulators_COPASI/dev/README.md'
                read_simulator_specs(url)
