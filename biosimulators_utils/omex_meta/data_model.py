""" Data model for working with OMEX Meta

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-23
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchiveContentFormat
import enum
import rdflib.term  # noqa: F401

__all__ = [
    'Triple',
    'OmexMetaInputFormat',
    'OmexMetaOutputFormat',
    'OmexMetaSchema',
    'BIOSIMULATIONS_ROOT_URI_FORMAT',
    'BIOSIMULATIONS_ROOT_URI_PATTERN',
    'BIOSIMULATIONS_PREDICATE_TYPES',
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


class OmexMetaInputFormat(str, enum.Enum):
    """ An format for reading an OMEX Meta file """
    ntriples = 'ntriples'
    nquads = 'nquads'
    rdfa = 'rdfa'
    rdfxml = 'rdfxml'
    turtle = 'turtle'


class OmexMetaOutputFormat(str, enum.Enum):
    """ An format for writing an OMEX Meta file """
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


class OmexMetaSchema(str, enum.Enum):
    """ Schema for OMEX Meta documents """
    biosimulations = 'BioSimulations'
    rdf_triples = 'rdf_triples'


BIOSIMULATIONS_ROOT_URI_FORMAT = 'http://omex-libary.org/{}.omex'
BIOSIMULATIONS_ROOT_URI_PATTERN = r'^http://omex-libary\.org/.*?\.omex$'

BIOSIMULATIONS_PREDICATE_TYPES = {
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/title': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/title',
        'attribute': 'title',
        'label': 'title',
        'multiple_allowed': False,
        'has_uri': False,
        'has_label': True,
        'required': True,
    },
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/abstract': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/abstract',
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
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/description': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/description',
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
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/source': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/source',
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
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/creator': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/creator',
        'attribute': 'creators',
        'label': 'Creators',
        'multiple_allowed': True,
        'has_uri': True,
        'has_label': True,
        'required': True,
    },
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/contributor': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/contributor',
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
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/license': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/license',
        'attribute': 'license',
        'label': 'License',
        'multiple_allowed': False,
        'has_uri': True,
        'has_label': True,
        'required': True
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
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/created': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/created',
        'attribute': 'created',
        'label': 'Created',
        'multiple_allowed': False,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
    'http://dublincore.org/specifications/dublin-core/dcmi-terms/modified': {
        'namespace': {
            'prefix': 'dc',
            'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/',
        },
        'uri': 'http://dublincore.org/specifications/dublin-core/dcmi-terms/modified',
        'attribute': 'modified',
        'label': 'Modified',
        'multiple_allowed': True,
        'has_uri': False,
        'has_label': True,
        'required': False,
    },
}

BIOSIMULATIONS_THUMBNAIL_FORMATS = [
    CombineArchiveContentFormat.GIF,
    CombineArchiveContentFormat.JPEG,
    CombineArchiveContentFormat.PNG,
    CombineArchiveContentFormat.WEBP,
]
