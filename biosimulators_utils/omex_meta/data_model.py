""" Data model for working with OMEX Metadata

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-23
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import enum
import rdflib.term  # noqa: F401

__all__ = [
    'Triple',
    'OmexMetadataInputFormat',
    'OmexMetadataOutputFormat',
    'OmexMetadataSchema',
    'BIOSIMULATIONS_ROOT_URI_FORMAT',
    'BIOSIMULATIONS_ROOT_URI_PATTERN',
    'BIOSIMULATIONS_PREDICATE_TYPES',
    'BIOSIMULATIONS_THUMBNAIL_FORMATS',
    'BIOSIMULATIONS_NAMESPACE_PREFIX_MAP',
    'BIOSIMULATIONS_NAMESPACE_ALIASES',
    'BIOSIMULATIONS_THUMBNAIL_FORMATS',
]


class Triple(object):
    """ An RDF triple

    Attributes:
        subject (:obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`): subject
        predicate (:obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`): predict
        object (:obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`): object
    """

    def __init__(self, subject, predicate, object):
        """
        Args:
            subject (:obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`): subject
            predicate (:obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`): predict
            object (:obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`): object
        """
        self.subject = subject
        self.predicate = predicate
        self.object = object


class OmexMetadataInputFormat(str, enum.Enum):
    """ An format for reading an OMEX Metadata file """
    ntriples = 'ntriples'
    nquads = 'nquads'
    rdfa = 'rdfa'
    rdfxml = 'rdfxml'
    turtle = 'turtle'


class OmexMetadataOutputFormat(str, enum.Enum):
    """ An format for writing an OMEX Metadata file """
    dot = 'dot'
    json = 'json'
    json_triples = 'json-triples'
    html = 'html'
    ntriples = 'ntriples'
    nquads = 'nquads'
    rdfxml = 'rdfxml'
    rdfxml_abbrev = 'rdfxml-abbrev'
    rdfxml_xmp = 'rdfxml-xmp'
    turtle = 'turtle'


class OmexMetadataSchema(str, enum.Enum):
    """ Schema for OMEX Metadata documents """
    biosimulations = 'BioSimulations'
    rdf_triples = 'rdf_triples'


BIOSIMULATIONS_ROOT_URI_FORMAT = 'http://omex-library.org/{}.omex'
BIOSIMULATIONS_ROOT_URI_PATTERN = r'^(http://omex-library\.org/.*?\.omex)(/|$)'

BIOSIMULATIONS_PREDICATE_TYPES = {
    'http://purl.org/dc/elements/1.1/title': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/title',
        'attribute': 'title',
        'label': 'title',
        'multiple_allowed': False,
        'has_uri': False,
        'has_label': True,
        'required': True,
    },
    'http://purl.org/dc/elements/1.1/abstract': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/abstract',
        'attribute': 'abstract',
        'label': 'Abstract',
        'multiple_allowed': False,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
    'http://prismstandard.org/namespaces/basic/2.0/keyword': {
        'namespace': {
            'prefix': 'prism',
            'uri': 'http://prismstandard.org/namespaces/basic/2.0/',
        },
        'uri': 'http://prismstandard.org/namespaces/basic/2.0/keyword',
        'attribute': 'keywords',
        'label': 'Keywords',
        'multiple_allowed': True,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/description': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/description',
        'attribute': 'description',
        'label': 'Description',
        'multiple_allowed': False,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
    'http://biomodels.net/biology-qualifiers/hasTaxon': {
        'namespace': {
            'prefix': 'bqbiol',
            'uri': 'http://biomodels.net/biology-qualifiers/',
        },
        'uri': 'http://biomodels.net/biology-qualifiers/hasTaxon',
        'attribute': 'taxa',
        'label': 'Taxa',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://biomodels.net/biology-qualifiers/encodes': {
        'namespace': {
            'prefix': 'bqbiol',
            'uri': 'http://biomodels.net/biology-qualifiers/',
        },
        'uri': 'http://biomodels.net/biology-qualifiers/encodes',
        'attribute': 'encodes',
        'label': 'Encodes',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://www.collex.org/schema#thumbnail': {
        'namespace': {
            'prefix': 'collex',
            'uri': 'http://www.collex.org/schema#',
        },
        'uri': 'http://www.collex.org/schema#thumbnail',
        'attribute': 'thumbnails',
        'label': 'Thumbnails',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': False,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/source': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/source',
        'attribute': 'sources',
        'label': 'Sources',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://biomodels.net/model-qualifiers/isDerivedFrom': {
        'namespace': {
            'prefix': 'bqmodel',
            'uri': 'http://biomodels.net/model-qualifiers/',
        },
        'uri': 'http://biomodels.net/model-qualifiers/isDerivedFrom',
        'attribute': 'predecessors',
        'label': 'Predecessors',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/terms/references': {
        'namespace': {
            'prefix': 'dcterms',
            'uri': 'http://purl.org/dc/terms/',
        },
        'uri': 'http://purl.org/dc/terms/references',
        'attribute': 'references',
        'label': 'References',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/spar/scoro/successor': {
        'namespace': {
            'prefix': 'scoro',
            'uri': 'http://purl.org/spar/scoro/',
        },
        'uri': 'http://purl.org/spar/scoro/successor',
        'attribute': 'successors',
        'label': 'Successors',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://www.w3.org/2000/01/rdf-schema#seeAlso': {
        'namespace': {
            'prefix': 'rdfs',
            'uri': 'http://www.w3.org/2000/01/rdf-schema#',
        },
        'uri': 'http://www.w3.org/2000/01/rdf-schema#seeAlso',
        'attribute': 'see_also',
        'label': 'See also',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/creator': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/creator',
        'attribute': 'creators',
        'label': 'Creators',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/contributor': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/contributor',
        'attribute': 'contributors',
        'label': 'Contributors',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://biomodels.net/model-qualifiers/is': {
        'namespace': {
            'prefix': 'bqmodel',
            'uri': 'http://biomodels.net/model-qualifiers/',
        },
        'uri': 'http://biomodels.net/model-qualifiers/is',
        'attribute': 'identifiers',
        'label': 'Identifiers',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://biomodels.net/model-qualifiers/isDescribedBy': {
        'namespace': {
            'prefix': 'bqmodel',
            'uri': 'http://biomodels.net/model-qualifiers/',
        },
        'uri': 'http://biomodels.net/model-qualifiers/isDescribedBy',
        'attribute': 'citations',
        'label': 'Citations',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/license': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/license',
        'attribute': 'license',
        'label': 'License',
        'multiple_allowed': False,
        'has_uri': True,
        'has_label': True,
        'required': False
    },
    'http://purl.org/spar/scoro/funder': {
        'namespace': {
            'prefix': 'scoro',
            'uri': 'http://purl.org/spar/scoro/',
        },
        'uri': 'http://purl.org/spar/scoro/funder',
        'attribute': 'funders',
        'label': 'Funders',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/created': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/created',
        'attribute': 'created',
        'label': 'Created',
        'multiple_allowed': False,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
    'http://purl.org/dc/elements/1.1/modified': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://purl.org/dc/elements/1.1/',
        },
        'uri': 'http://purl.org/dc/elements/1.1/modified',
        'attribute': 'modified',
        'label': 'Modified',
        'multiple_allowed': True,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
}

BIOSIMULATIONS_NAMESPACE_PREFIX_MAP = {
    'http://biomodels.net/biology-qualifiers/': 'bqbiol',
    'http://biomodels.net/model-qualifiers/': 'biomodel',
    'http://purl.org/dc/elements/1.1/': 'dc',
    'http://prismstandard.org/namespaces/basic/2.0/': 'prism',
    'http://purl.org/dc/terms/': 'dcterms',
    'http://purl.org/spar/scoro/': 'scoro',
    'http://www.collex.org/schema#': 'collex',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
    'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
    'http://xmlns.com/foaf/0.1/': 'foaf',
}

BIOSIMULATIONS_NAMESPACE_ALIASES = {
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/': 'http://purl.org/dc/elements/1.1/',
    'http://sempublishing.sourceforge.net/scoro/': 'http://purl.org/spar/scoro/',
}

BIOSIMULATIONS_THUMBNAIL_FORMATS = [
    'GIF',
    'JPEG',
    'PNG',
    'WEBP',
]
