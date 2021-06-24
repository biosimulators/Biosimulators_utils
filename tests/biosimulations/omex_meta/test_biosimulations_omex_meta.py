from biosimulators_utils.biosimulations.omex_meta import io
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
import datetime
import os
import pyomexmeta
import shutil
import tempfile
import unittest


class BiosimulationsOmexMetaIoTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'omex-meta')
    FIXTURE = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'omex-meta', 'biosimulations.rdf')
    WARNING_FIXTURE = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'omex-meta', 'warning.rdf')
    INVALID_FIXTURE = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'omex-meta', 'invalid.rdf')
    NO_ROOT_FIXTURE = os.path.join(os.path.dirname(__file__), '..', '..', 'fixtures', 'omex-meta', 'no-root.rdf')
    MULTIPLE_ROOTS_FIXTURE = os.path.join(
        os.path.dirname(__file__), '..', '..', 'fixtures', 'omex-meta', 'multiple-roots.rdf')

    def setUp(self):
        self.dir_name = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir_name)

    def test_read_rdf(self):
        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.FIXTURE)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf('undefined')
        self.assertEqual(rdf, None)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.INVALID_FIXTURE)
        self.assertEqual(rdf, None)
        self.assertIn('multiple object node elements', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.WARNING_FIXTURE)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertIn('Unsupported version', flatten_nested_list_of_strings(warnings))

    def test_get_rdf_graph(self):
        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.FIXTURE)
        graph = io.BiosimulationsOmexMetaReader.get_rdf_graph(rdf)
        self.assertGreater(len(graph), 1)
        self.assertEqual(set(graph[0].keys()), set(['subject', 'predicate', 'object']))

    def test_get_omex_uri(self):
        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.FIXTURE)
        graph = io.BiosimulationsOmexMetaReader.get_rdf_graph(rdf)
        root_uri, errors, warnings = io.BiosimulationsOmexMetaReader.get_omex_uri(graph)
        self.assertEqual(root_uri, 'http://omex-libary.org/BioSim0001.omex')
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.NO_ROOT_FIXTURE)
        graph = io.BiosimulationsOmexMetaReader.get_rdf_graph(rdf)
        root_uri, errors, warnings = io.BiosimulationsOmexMetaReader.get_omex_uri(graph)
        self.assertEqual(root_uri, None)
        self.assertIn('does not contain metadata', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.MULTIPLE_ROOTS_FIXTURE)
        graph = io.BiosimulationsOmexMetaReader.get_rdf_graph(rdf)
        root_uri, errors, warnings = io.BiosimulationsOmexMetaReader.get_omex_uri(graph)
        self.assertEqual(root_uri, None)
        self.assertIn('metadata about multiple', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_read(self):
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(self.FIXTURE)
        expected = {
            'title': 'Name',
            'abstract': 'Short summary',
            'keywords': ['tag 1', 'tag 2'],
            'thumbnails': ['./thumbnail.png'],
            'description': 'Description',
            'taxa': [
                {
                    'uri': 'https://identifiers.org/taxonomy/9606',
                    'label': 'Homo sapiens',
                }
            ],
            'encodes': [
                {
                    'uri': 'http://purl.obolibrary.org/obo/CL_0001057',
                    'label': 'myeloid dendritic cell, human',
                }
            ],
            'sources': [
                {
                    'uri': 'https://github.org/lab/project',
                    'label': 'Tsur 2019 model source code',
                }
            ],
            'predecessors': [
                {
                    'uri': 'https://identifiers.org/biomodels.db:BIOMD0000000837',
                    'label': 'Hanson2016 - Toxicity Management in CAR T cell therapy for B-ALL',
                }
            ],
            'successors': [
                {
                    'uri': 'https://identifiers.org/biomodels.db:BIOMD0000000839',
                    'label': 'Almeida2019 - Transcription-based circadian ...',
                }
            ],
            'see_also': [
                {
                    'uri': 'https://identifiers.org/biomodels.db:BIOMD0000000836',
                    'label': 'Radosavljevic2009_BioterroristAttack_PanicProtection_1',
                }
            ],
            'identifiers': [
                {
                    'uri': 'https://identifiers.org/biomodels.db:BIOMD0000000838',
                    'label': 'biomodels.db:BIOMD0000000838',
                }
            ],
            'citations': [
                {
                    'uri': 'https://identifiers.org/doi:10.1016/j.copbio.2017.12.013',
                    'label': (
                        'Goldberg AP, Szigeti B, Chew YH, Sekar JA, Roth YD & Karr JR. '
                        'Emerging whole-cell modeling principles and methods. '
                        'Curr Opin Biotechnol 2018, 51:97-102.'
                    ),
                },
                {
                    'uri': 'https://identifiers.org/pubmed:29275251',
                    'label': (
                        'Goldberg AP, Szigeti B, Chew YH, Sekar JA, Roth YD & Karr JR. '
                        'Emerging whole-cell modeling principles and methods. '
                        'Curr Opin Biotechnol 2018, 51:97-102.'
                    ),
                }
            ],
            'creators': [
                {
                    'uri': 'https://orcid.org/0000-0001-8254-4958',
                    'label': 'Jonathan Karr',
                }
            ],
            'contributors': [
                {
                    'uri': None,
                    'label': 'Name of person with no ORCID account',
                }
            ],
            'license': {
                'uri': 'http://identifiers.org/spdx:MIT',
                'label': 'MIT',
            },
            'funders': [
                {
                    'uri': 'http://dx.doi.org/10.13039/100000001',
                    'label': 'National Science Foundation',
                },
            ],
            'created': datetime.datetime(2020, 6, 18),
            'modified': [datetime.datetime(2021, 6, 18)],
            'other': [
                {
                    'attribute': 'http://ontology.eil.utoronto.ca/icity/OM/temporalUnit',
                    'attribute_label': 'Temporal unit',
                    'uri': 'http://www.w3.org/2006/time#second',
                    'label': 'second',
                },
            ],
        }
        for key in expected.keys():
            self.assertEqual(metadata[key], expected[key], key)
        self.assertEqual(metadata, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'abbrev.rdf')
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertEqual(metadata['title'], 'Name')
        self.assertEqual(metadata['funders'], [
            {
                'uri': 'http://dx.doi.org/10.13039/100000001',
                'label': 'National Science Foundation',
            },
        ])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'missing-required.rdf')
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertIn('must be annotated with', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'missing-label.rdf')
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertEqual(errors, [])
        self.assertIn('does not contain an rdf:label', flatten_nested_list_of_strings(warnings))

        filename = os.path.join(self.FIXTURE_DIR, 'missing-uri.rdf')
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertIn('must be annotated with', flatten_nested_list_of_strings(errors))
        self.assertIn('does not contain an URI', flatten_nested_list_of_strings(warnings))

        filename = os.path.join(self.FIXTURE_DIR, 'missing-label-2.rdf')
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertEqual(errors, [])
        self.assertIn('does not contain an rdf:label', flatten_nested_list_of_strings(warnings))

        filename = os.path.join(self.FIXTURE_DIR, 'too-many-objects.rdf')
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertIn('should only contain one instance of predicate', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = 'does not exist'
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertEqual(metadata, None)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = self.NO_ROOT_FIXTURE
        metadata, errors, warnings = io.BiosimulationsOmexMetaReader.run(filename)
        self.assertEqual(metadata, None)
        self.assertIn('does not contain metadata', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])