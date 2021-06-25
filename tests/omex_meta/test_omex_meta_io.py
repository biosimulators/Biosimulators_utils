from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.omex_meta import data_model
from biosimulators_utils.omex_meta import io
from biosimulators_utils.utils.core import flatten_nested_list_of_strings
from unittest import mock
import os
import pyomexmeta
import shutil
import tempfile
import unittest


class OmexMetaIoTestCase(unittest.TestCase):
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta')
    FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta', 'biosimulations.rdf')
    WARNING_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta', 'warning.rdf')
    INVALID_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta', 'invalid.rdf')
    NO_ROOT_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'omex-meta', 'no-root.rdf')
    MULTIPLE_ROOTS_FIXTURE = os.path.join(
        os.path.dirname(__file__), '..', 'fixtures', 'omex-meta', 'multiple-roots.rdf')

    def setUp(self):
        self.dir_name = tempfile.mkdtemp()
        with open(os.path.join(self.dir_name, 'thumbnail.png'), 'w') as file:
            pass

        patcher = mock.patch('requests.get', return_value=mock.Mock(status_code=200))
        self.addCleanup(patcher.stop)
        patcher.start()

    def tearDown(self):
        shutil.rmtree(self.dir_name)

    def test_read_rdf(self):
        rdf, errors, warnings = io.OmexMetaReader.read_rdf(self.FIXTURE)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.OmexMetaReader.read_rdf('undefined')
        self.assertEqual(rdf, None)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.OmexMetaReader.read_rdf(self.INVALID_FIXTURE)
        self.assertEqual(rdf, None)
        self.assertIn('multiple object node elements', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.OmexMetaReader.read_rdf(self.WARNING_FIXTURE)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertIn('Unsupported version', flatten_nested_list_of_strings(warnings))

    def test_get_rdf_triples(self):
        rdf, errors, warnings = io.OmexMetaReader.read_rdf(self.FIXTURE)
        triples = io.OmexMetaReader.get_rdf_triples(rdf)
        self.assertGreater(len(triples), 1)
        self.assertIsInstance(triples[0], data_model.Triple)

    def test_TriplesOmexMetaReader_run(self):
        triples, rdf, errors, warnings = io.TriplesOmexMetaReader().run(self.FIXTURE)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        triples, rdf, errors, warnings = io.TriplesOmexMetaReader().run('undefined')
        self.assertEqual(rdf, None)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_BiosimulationsOmexMetaReader_get_combine_archive_uri(self):
        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.FIXTURE)
        triples = io.BiosimulationsOmexMetaReader.get_rdf_triples(rdf)
        root_uri, errors, warnings = io.BiosimulationsOmexMetaReader.get_combine_archive_uri(triples)
        self.assertEqual(root_uri, 'http://omex-libary.org/BioSim0001.omex')
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.NO_ROOT_FIXTURE)
        triples = io.BiosimulationsOmexMetaReader.get_rdf_triples(rdf)
        root_uri, errors, warnings = io.BiosimulationsOmexMetaReader.get_combine_archive_uri(triples)
        self.assertEqual(root_uri, None)
        self.assertIn('does not contain metadata', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        rdf, errors, warnings = io.BiosimulationsOmexMetaReader.read_rdf(self.MULTIPLE_ROOTS_FIXTURE)
        triples = io.BiosimulationsOmexMetaReader.get_rdf_triples(rdf)
        root_uri, errors, warnings = io.BiosimulationsOmexMetaReader.get_combine_archive_uri(triples)
        self.assertEqual(root_uri, None)
        self.assertIn('metadata about multiple', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_BiosimulationsOmexMetaReader_run(self):
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(self.FIXTURE, working_dir=self.dir_name)
        expected = [{
            'location': '.',
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
                    'uri': 'https://identifiers.org/CL:0001057',
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
                    'uri': 'https://identifiers.org/orcid:0000-0001-8254-4958',
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
                'uri': 'https://identifiers.org/spdx:MIT',
                'label': 'MIT',
            },
            'funders': [
                {
                    'uri': 'https://identifiers.org/doi:10.13039/100000001',
                    'label': 'National Science Foundation',
                },
            ],
            'created': '2020-06-18',
            'modified': ['2021-06-18'],
            'other': [
                {
                    'attribute_uri': 'http://ontology.eil.utoronto.ca/icity/OM/temporalUnit',
                    'attribute_label': 'Temporal unit',
                    'uri': 'http://www.w3.org/2006/time#second',
                    'label': 'second',
                },
            ],
        }]
        for key in expected[0].keys():
            self.assertEqual(metadata[0][key], expected[0][key], key)
        self.assertEqual(metadata, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'biosimulations-abbrev.rdf')
        metadata2, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertEqual(metadata2, metadata)

        filename = os.path.join(self.FIXTURE_DIR, 'abbrev.rdf')
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertEqual(metadata[0]['title'], 'Name')
        self.assertEqual(metadata[0]['funders'], [
            {
                'uri': 'https://identifiers.org/doi:10.13039/100000001',
                'label': 'National Science Foundation',
            },
        ])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        md, _, errors, warnings = io.BiosimulationsOmexMetaReader().run(
            os.path.join(self.FIXTURE_DIR, 'biosimulations-with-file-annotations.rdf'),
            working_dir=self.dir_name)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(len(md), 2)
        self.assertEqual(set(m['location'] for m in md), set(['.', './sim.sedml/figure1']))
        m = next(m for m in md if m['location'] == './sim.sedml/figure1')
        self.assertEqual(m, {
            'location': './sim.sedml/figure1',
            'title': None,
            'abstract': None,
            'keywords': [],
            'thumbnails': [],
            'description': None,
            'taxa': [],
            'encodes': [],
            'sources': [],
            'predecessors': [],
            'successors': [],
            'see_also': [],
            'identifiers': [{
                'uri': 'https://doi.org/10.1371/journal.pcbi.1008379.g001',
                'label': 'Figure 1a',
            }],
            'citations': [],
            'creators': [],
            'contributors': [],
            'license': None,
            'funders': [],
            'created': None,
            'modified': [],
            'other': [
            ],
        })

        filename = os.path.join(self.FIXTURE_DIR, 'missing-required.rdf')
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertIn('is required', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = os.path.join(self.FIXTURE_DIR, 'missing-label.rdf')
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertEqual(errors, [])
        self.assertIn('does not contain an rdf:label', flatten_nested_list_of_strings(warnings))

        filename = os.path.join(self.FIXTURE_DIR, 'missing-uri.rdf')
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertIn('is required', flatten_nested_list_of_strings(errors))
        self.assertIn('does not contain an URI', flatten_nested_list_of_strings(warnings))

        filename = os.path.join(self.FIXTURE_DIR, 'missing-label-2.rdf')
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertEqual(errors, [])
        self.assertIn('does not contain an rdf:label', flatten_nested_list_of_strings(warnings))

        filename = os.path.join(self.FIXTURE_DIR, 'too-many-objects.rdf')
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertIn('should only contain one instance of predicate', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = 'does not exist'
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertEqual(metadata, None)
        self.assertIn('is not a file', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

        filename = self.NO_ROOT_FIXTURE
        metadata, rdf, errors, warnings = io.BiosimulationsOmexMetaReader().run(filename, working_dir=self.dir_name)
        self.assertEqual(metadata, None)
        self.assertIn('does not contain metadata', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_read_omex_meta_file(self):
        triples, rdf, errors, warnings = io.read_omex_meta_file(
            self.FIXTURE,
            schema=data_model.OmexMetaSchema.triples)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        metadata, rdf, errors, warnings = io.read_omex_meta_file(
            self.FIXTURE,
            schema=data_model.OmexMetaSchema.biosimulations,
            working_dir=self.dir_name)
        self.assertIsInstance(rdf, pyomexmeta.RDF)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        metadata, rdf, errors, warnings = io.read_omex_meta_file(
            self.FIXTURE,
            schema=None)
        self.assertEqual(metadata, None)
        self.assertEqual(rdf, None)
        self.assertIn('is not supported', flatten_nested_list_of_strings(errors))
        self.assertEqual(warnings, [])

    def test_TriplesOmexMetaWriter_run(self):
        triples, _, _, _ = io.TriplesOmexMetaReader().run(self.FIXTURE)

        filename = os.path.join(self.dir_name, 'md.rdf')
        io.TriplesOmexMetaWriter().run(triples, filename, format=data_model.OmexMetaOutputFormat.rdfxml)

        md, _, _, _ = io.BiosimulationsOmexMetaReader().run(self.FIXTURE)
        md2, _, _, _ = io.BiosimulationsOmexMetaReader().run(filename)
        for key in md[0].keys():
            if isinstance(md[0][key], list) and md[0][key]:
                if isinstance(md[0][key][0], str):
                    md2[0][key].sort()
                    md[0][key].sort()
                elif isinstance(md[0][key][0], dict):
                    md2[0][key].sort(key=lambda obj: (obj['uri'], obj['label']))
                    md[0][key].sort(key=lambda obj: (obj['uri'], obj['label']))
            self.assertEqual(md2[0][key], md[0][key], key)
        self.assertEqual(md2, md)

        filename = os.path.join(self.dir_name, 'md')
        io.TriplesOmexMetaWriter().run(triples, filename, format=data_model.OmexMetaOutputFormat.turtle)

        filename = os.path.join(self.dir_name, 'md.xml')
        io.TriplesOmexMetaWriter().run(triples, filename, format=data_model.OmexMetaOutputFormat.rdfxml_abbrev)

        md2, _, _, _ = io.BiosimulationsOmexMetaReader().run(filename)
        for key in md[0].keys():
            if isinstance(md[0][key], list) and md[0][key]:
                if isinstance(md[0][key][0], str):
                    md2[0][key].sort()
                    md[0][key].sort()
                elif isinstance(md[0][key][0], dict):
                    md2[0][key].sort(key=lambda obj: (obj['uri'], obj['label']))
                    md[0][key].sort(key=lambda obj: (obj['uri'], obj['label']))
            self.assertEqual(md2[0][key], md[0][key], key)
        self.assertEqual(md2, md)

    def test_BiosimulationsOmexMetaWriter_run(self):
        md, _, _, _ = io.BiosimulationsOmexMetaReader().run(self.FIXTURE)

        filename = os.path.join(self.dir_name, 'md.rdf')
        io.BiosimulationsOmexMetaWriter().run(md, filename, format=data_model.OmexMetaOutputFormat.rdfxml)

        md2, _, _, _ = io.BiosimulationsOmexMetaReader().run(filename)
        for key in md[0].keys():
            if isinstance(md[0][key], list) and md[0][key]:
                if isinstance(md[0][key][0], str):
                    md2[0][key].sort()
                    md[0][key].sort()
                elif isinstance(md[0][key][0], dict):
                    md2[0][key].sort(key=lambda obj: (obj['uri'], obj['label']))
                    md[0][key].sort(key=lambda obj: (obj['uri'], obj['label']))
            self.assertEqual(md2[0][key], md[0][key], key)
        self.assertEqual(md2, md)

        filename = os.path.join(self.dir_name, 'md.rdf')
        md[0]['title'] = None
        md[0]['other'].append({
            'attribute_uri': 'http://www.collex.org/schema#thumbnail',
            'attribute_label': 'Image',
            'uri': 'https://website.com/image.png',
            'label': 'Big image',
        })
        io.BiosimulationsOmexMetaWriter().run(md, filename, format=data_model.OmexMetaOutputFormat.rdfxml)

        md, _, _, _ = io.BiosimulationsOmexMetaReader().run(
            os.path.join(self.FIXTURE_DIR, 'biosimulations-with-file-annotations.rdf'))
        filename = os.path.join(self.dir_name, 'md.rdf')
        io.BiosimulationsOmexMetaWriter().run(md, filename, format=data_model.OmexMetaOutputFormat.rdfxml)
        md2, _, _, _ = io.BiosimulationsOmexMetaReader().run(filename)

        md.sort(key=lambda file: file['location'])
        md2.sort(key=lambda file: file['location'])
        for i in range(len(md)):
            for key in md[i].keys():
                if isinstance(md[i][key], list) and md[i][key]:
                    if isinstance(md[i][key][0], str):
                        md2[i][key].sort()
                        md[i][key].sort()
                    elif isinstance(md[i][key][0], dict):
                        md2[i][key].sort(key=lambda obj: (obj['uri'], obj['label']))
                        md[i][key].sort(key=lambda obj: (obj['uri'], obj['label']))
        self.assertEqual(md2, md)

    def test_write_omex_meta_file(self):
        triples, _, _, _ = io.read_omex_meta_file(self.FIXTURE, data_model.OmexMetaSchema.triples)
        filename = os.path.join(self.dir_name, 'md.rdf')
        io.write_omex_meta_file(triples, data_model.OmexMetaSchema.triples, filename)

        md, _, _, _ = io.BiosimulationsOmexMetaReader().run(self.FIXTURE)
        filename = os.path.join(self.dir_name, 'md.rdf')
        io.write_omex_meta_file(md, data_model.OmexMetaSchema.biosimulations, filename)

        with self.assertRaises(NotImplementedError):
            io.write_omex_meta_file(triples, None, filename)

    def test_read_omex_meta_files_for_archive(self):
        shutil.copyfile(os.path.join(self.FIXTURE_DIR, 'biosimulations.rdf'),
                        os.path.join(self.dir_name, 'biosimulations.rdf'))
        shutil.copyfile(os.path.join(self.FIXTURE_DIR, 'biosimulations-with-file-annotations.rdf'),
                        os.path.join(self.dir_name, 'biosimulations-with-file-annotations.rdf'))

        archive = CombineArchive()
        archive.contents = [
            CombineArchiveContent(
                location='biosimulations.rdf',
                format=CombineArchiveContentFormat.OMEX_METADATA,
            ),
            CombineArchiveContent(
                location='biosimulations-with-file-annotations.rdf',
                format=CombineArchiveContentFormat.OMEX_METADATA,
            ),
        ]
        md, errors, warnings = io.read_omex_meta_files_for_archive(
            archive, self.dir_name, data_model.OmexMetaSchema.biosimulations)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(len(md), 3)
        self.assertEqual(sorted(m['location'] for m in md), sorted(['.', '.', './sim.sedml/figure1']))
