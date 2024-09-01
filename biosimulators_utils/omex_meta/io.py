""" Methods for reading and writing OMEX Metadata files

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-23
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchive, CombineArchiveContentFormatPattern  # noqa: F401
from ..config import get_config, Config  # noqa: F401
from .data_model import (Triple, OmexMetadataOutputFormat, OmexMetadataSchema,
                         BIOSIMULATIONS_ROOT_URI_PATTERN,
                         BIOSIMULATIONS_PREDICATE_TYPES,
                         BIOSIMULATIONS_NAMESPACE_PREFIX_MAP,
                         BIOSIMULATIONS_NAMESPACE_ALIASES)
from .utils import get_local_combine_archive_content_uri, get_global_combine_archive_content_uri
from .validation import validate_biosimulations_metadata
from lxml import etree
import abc
import collections
import json
import os
import pyomexmeta
import rdflib
import re
import tempfile

__all__ = [
    'read_omex_meta_file',
    'write_omex_meta_file',
    'read_omex_meta_files_for_archive',
    'TriplesOmexMetaReader',
    'TriplesOmexMetaWriter',
    'BiosimulationsOmexMetaReader',
    'BiosimulationsOmexMetaWriter',
]


def read_omex_meta_file(filename_or_filenames, archive=None, working_dir=None, config=None):
    """ Read an OMEX Metadata file

    Args:
        filename_or_filenames (:obj:`str` or :obj:`list` of :obj:`str`): path or paths to OMEX Metadata files
        archive (:obj:`CombineArchive`, optional): parent COMBINE archive
        working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`object`: representation of the OMEX Metadata file in :obj:`schema`
            * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Metadata file
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Metadata file
    """
    content = None
    errors = []
    warnings = []

    if config is None:
        config = get_config()

    if config.OMEX_METADATA_SCHEMA == OmexMetadataSchema.biosimulations:
        return BiosimulationsOmexMetaReader().run(filename_or_filenames, archive=archive, working_dir=working_dir, config=config)

    elif config.OMEX_METADATA_SCHEMA == OmexMetadataSchema.rdf_triples:
        return TriplesOmexMetaReader().run(filename_or_filenames, archive=archive, working_dir=working_dir, config=config)

    else:
        errors.append(['Schema `{}` is not supported. The following schemas are supported:',
                       [['None']] + sorted([
                           [schema.value] for schema in OmexMetadataSchema.__members__.values()
                       ])])
        return (content, errors, warnings)


def write_omex_meta_file(content, filename, config=None):
    """ Write an OMEX Metadata file

    Args:
        content (:obj:`object`): representation of the OMEX Metadata file in :obj:`schema`
        filename (:obj:`str`): path to save OMEX Metadata file
        config (:obj:`Config`, optional): configuration
    """
    if config is None:
        config = get_config()

    if config.OMEX_METADATA_SCHEMA == OmexMetadataSchema.biosimulations:
        return BiosimulationsOmexMetaWriter().run(content, filename, config=config)

    elif config.OMEX_METADATA_SCHEMA == OmexMetadataSchema.rdf_triples:
        return TriplesOmexMetaWriter().run(content, filename, config=config)

    else:
        msg = 'Schema `{}` is not supported. The following schemas are supported:\n  {}'.format(
            config.OMEX_METADATA_SCHEMA.value if config.OMEX_METADATA_SCHEMA else None,
            '\n  '.join(['None'] + sorted([schema.value for schema in OmexMetadataSchema.__members__.values()])))
        raise NotImplementedError(msg)


def read_omex_meta_files_for_archive(archive, archive_dirname, config=None):
    """ Read all of the OMEX Metadata files in an archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dirname (:obj:`str`): directory with the content of the archive
        config (:obj:`Config`, optional): configuration

    Returns:
        :obj:`tuple`:

            * :obj:`object`: representation of the OMEX Metadata file in :obj:`schema`
            * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Metadata file
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Metadata file
    """
    content = []
    errors = []
    warnings = []

    if config is None:
        config = get_config()

    filenames = []
    for item in archive.contents:
        if item.format and re.match(CombineArchiveContentFormatPattern.OMEX_METADATA.value, item.format):
            filenames.append(os.path.join(archive_dirname, item.location))

    if filenames:
        return read_omex_meta_file(filenames, archive=archive, working_dir=archive_dirname, config=config)
    else:
        content = []
        errors = [[(
            'The COMBINE/OMEX does not contain an OMEX Metadata file. '
            'Archives must contain metadata for publication to BioSimulations.'
        )]]
        warnings = []
        return (content, errors, warnings)


class OmexMetaReader(abc.ABC):
    """ Base class for reading OMEX Metadata files """

    @abc.abstractmethod
    def run(self, filename_or_filenames, archive=None, working_dir=None, config=None):
        """ Read an OMEX Metadata file

        Args:
            filename_or_filenames (:obj:`str` or :obj:`list` of :obj:`str`): path or paths to OMEX Metadata files
            archive (:obj:`CombineArchive`, optional): parent COMBINE archive
            working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)
            config (:obj:`Config`, optional): configuration

        Returns:
            :obj:`tuple`:

                * :obj:`object`: representation of the OMEX Metadata file
                * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Metadata file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Metadata file
        """
        pass  # pragma: no cover

    @classmethod
    def read_rdf(cls, filename, config=None):
        """ Read an RDF file

        Args:
            filename (:obj:`str`): path to the RDF file
            config (:obj:`Config`, optional): configuration

        Returns:
            :obj:`tuple`:

                * :obj:`pyomexmeta.RDF`: RDF representation of the file
                * nested :obj:`list` of :obj:`str`: nested list of errors with the RDF file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the RDF file
        """
        if config is None:
            config = get_config()

        rdf = None
        errors = []
        warnings = []

        if not os.path.isfile(filename):
            errors.append(['`{}` is not a file.'.format(filename)])
            return (rdf, errors, warnings)

        pyomexmeta_log_level = pyomexmeta.Logger.get_level()
        pyomexmeta.Logger.clear()
        pyomexmeta.Logger.set_level(pyomexmeta.eLogLevel.warn)

        with open(filename, 'rb') as file:
            line = file.readline()

        temp_filename = None
        if line.startswith(b'<?xml ') and b'?>' in line:
            decl, sep, after_decl = line.partition(b'?>')
            if b' version="1.1"' in decl or b" version='1.1'" in decl:
                decl = decl.replace(b' version="1.1"', b' version="1.0"').replace(b" version='1.1'", b" version='1.0'")
                line = decl + sep + after_decl

                with open(filename, 'rb') as file:
                    lines = file.readlines()

                lines[0] = line

                temp_fid, temp_filename = tempfile.mkstemp(dir=os.path.dirname(filename))
                os.close(temp_fid)
                with open(temp_filename, 'wb') as file:
                    for line in lines:
                        file.write(line)

                filename = temp_filename

        rdf = pyomexmeta.RDF.from_file(filename, config.OMEX_METADATA_INPUT_FORMAT.value)

        if temp_filename:
            os.remove(temp_filename)

        pyomexmeta.Logger.set_level(pyomexmeta_log_level)

        logger = pyomexmeta.Logger()
        num_messages = len(logger)
        for i_message in range(num_messages):
            message = logger[i_message]
            type = message.get_level()
            message = message.get_message()

            if type in ['warn', 'warning']:
                warnings.append([message])
            else:
                rdf = None
                errors.append([message])

        return (rdf, errors, warnings)

    @classmethod
    def get_rdf_triples(cls, rdf):
        """ Read an RDF file

        Args:
            rdf (:obj:`pyomexmeta.RDF`): RDF representation of the file

        Returns:
            * :obj:`list` of :obj:`Triple`: representation of the OMEX Metadata file as list of triples
        """
        query = "SELECT ?subject ?predicate ?object WHERE { ?subject ?predicate ?object }"
        plain_triples = json.loads(rdf.query_results_as_string(query, 'json'))['results']['bindings']
        triples = []
        for plain_triple in plain_triples:
            subject = cls.make_rdf_node(plain_triple['subject'])
            predicate = cls.make_rdf_node(plain_triple['predicate'])
            object = cls.make_rdf_node(plain_triple['object'])

            triples.append(Triple(
                subject=subject,
                predicate=predicate,
                object=object,
            ))

        return triples

    @classmethod
    def make_rdf_node(cls, node):
        """ Make an RDF node

        Args:
            node (:obj:`dict`): node

        Returns:
            :obj:`rdflib.term.BNode`, :obj:`rdflib.term.Literal`, or :obj:`rdflib.term.URIRef`: node
        """
        if node['type'] == 'bnode':
            return rdflib.term.BNode(node['value'])

        elif node['type'] == 'literal':
            return rdflib.term.Literal(node['value'])

        else:
            return rdflib.term.URIRef(node['value'])


class OmexMetaWriter(abc.ABC):
    """ Base class for writing OMEX Metadata files """

    @abc.abstractmethod
    def run(self, content, filename, config=None):
        """ Write an OMEX Metadata file

        Args:
            content (:obj:`object`): representation of the OMEX Metadata file
            filename (:obj:`str`): path to save OMEX Metadata file
            config (:obj:`Config`, optional): configuration
        """
        pass  # pragma: no cover


class TriplesOmexMetaReader(OmexMetaReader):
    """ Utility for reading an OMEX Metadata file into a list of triples """

    def run(self, filename_or_filenames, archive=None, working_dir=None, config=None):
        """ Read an OMEX Metadata file into a list of triples

        Args:
            filename_or_filenames (:obj:`str` or :obj:`list` of :obj:`str`): path or paths to OMEX Metadata files
            archive (:obj:`CombineArchive`, optional): parent COMBINE archive
            working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)
            config (:obj:`Config`, optional): configuration

        Returns:
            :obj:`tuple`:

                * :obj:`list` of :obj:`dict`: representation of the OMEX Metadata file as list of triples
                * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Metadata file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Metadata file
        """
        if config is None:
            config = get_config()

        triples = None
        errors = []
        warnings = []

        if isinstance(filename_or_filenames, (tuple, list)):
            filenames = filename_or_filenames
        else:
            filenames = [filename_or_filenames]

        for filename in filenames:
            rdf, temp_errors, temp_warnings = self.read_rdf(filename, config=config)

            if working_dir:
                error_filename = os.path.relpath(filename, working_dir)
            else:
                error_filename = filename

            if temp_errors:
                if isinstance(filename_or_filenames, (tuple, list)):
                    errors.append(['The OMEX Metadata file at location `{}` is invalid.'.format(error_filename), temp_errors])
                else:
                    errors.extend(temp_errors)

            if temp_warnings:
                if isinstance(filename_or_filenames, (tuple, list)):
                    warnings.append(['The OMEX Metadata file at location `{}` has warnings.'.format(error_filename), temp_warnings])
                else:
                    warnings.extend(temp_warnings)

        if errors:
            return (triples, errors, warnings)

        triples = self.get_rdf_triples(rdf)

        return (triples, errors, warnings)


class TriplesOmexMetaWriter(OmexMetaWriter):
    """ Utility for writing a list of triples to an OMEX Metadata file """

    def run(self, triples, filename, namespaces=None, config=None):
        """ Write a list of triples to an OMEX Metadata file

        Args:
            triples (:obj:`list` of :obj:`Triple`): representation of the OMEX Metadata file as list of triples
            filename (:obj:`str`): path to OMEX Metadata file
            config (:obj:`Config`, optional): configuration
        """
        if config is None:
            config = get_config()

        if config.OMEX_METADATA_OUTPUT_FORMAT == OmexMetadataOutputFormat.turtle:
            graph = rdflib.Graph()
            for prefix, namespace in (namespaces or {}).items():
                graph.namespace_manager.bind(prefix, namespace)
            # graph.namespace_manager.bind('omexLibrary', rdflib.Namespace('http://omex-library.org/'))
            # graph.namespace_manager.bind('identifiers', rdflib.Namespace('http://identifiers.org/'))

            for triple in triples:
                graph.add((triple.subject, triple.predicate, triple.object))

            graph.serialize(filename, format="turtle")

        else:
            def get_uri_namespace_id(uri):
                if '#' in uri:
                    namespace, _, id = uri.rpartition('#')
                    namespace += '#'
                    return (namespace, id)
                elif '/' in uri:
                    namespace, _, id = uri.rpartition('/')
                    namespace += '/'
                    return (namespace, id)
                raise ValueError('URI `{}` does not belong to a namespace'.format(uri))

            namespace_prefix_map = dict(BIOSIMULATIONS_NAMESPACE_PREFIX_MAP)
            namespaces = namespaces or {}
            namespaces['rdf'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

            bnode_ids = collections.OrderedDict()

            for triple in triples:
                namespace, _ = get_uri_namespace_id(str(triple.predicate))
                if namespace in namespace_prefix_map:
                    prefix = namespace_prefix_map[namespace]
                else:
                    prefix = 'ns{}'.format(len(namespaces))
                    namespace_prefix_map[namespace] = prefix
                namespaces[prefix] = namespace

                if isinstance(triple.subject, rdflib.term.BNode) and triple.subject not in bnode_ids:
                    bnode_ids[triple.subject] = '{:07d}'.format(len(bnode_ids))

                if isinstance(triple.object, rdflib.term.BNode) and triple.object not in bnode_ids:
                    bnode_ids[triple.object] = '{:07d}'.format(len(bnode_ids))

            root = etree.Element("{{{}}}RDF".format(namespaces['rdf']), nsmap=namespaces)

            for id, node in bnode_ids.items():
                node = etree.Element("{{{}}}Description".format(namespaces['rdf']), nsmap=namespaces)
                root.append(node)

            for triple in triples:
                subject = etree.Element("{{{}}}Description".format(namespaces['rdf']), nsmap=namespaces)
                if isinstance(triple.subject, rdflib.term.URIRef):
                    subject.attrib["{{{}}}about".format(namespaces['rdf'])] = str(triple.subject)
                else:
                    subject.attrib["{{{}}}nodeID".format(namespaces['rdf'])] = bnode_ids[triple.subject]
                root.append(subject)

                namespace, id = get_uri_namespace_id(str(triple.predicate))
                predicate = etree.Element("{{{}}}{}".format(namespace, id), nsmap=namespaces)

                if isinstance(triple.object, rdflib.term.URIRef):
                    predicate.attrib["{{{}}}resource".format(namespaces['rdf'])] = str(triple.object)
                if isinstance(triple.object, rdflib.term.BNode):
                    predicate.attrib["{{{}}}nodeID".format(namespaces['rdf'])] = bnode_ids[triple.object]
                else:
                    predicate.text = str(triple.object)

                subject.append(predicate)

            etree.ElementTree(root).write(filename,
                                          xml_declaration=True,
                                          encoding="utf-8",
                                          standalone=False,
                                          pretty_print=True)

            if config.OMEX_METADATA_OUTPUT_FORMAT != OmexMetadataOutputFormat.rdfxml:
                rdf = pyomexmeta.RDF.from_file(filename, 'rdfxml')
                if rdf.to_file(filename, config.OMEX_METADATA_OUTPUT_FORMAT.value) != 0:
                    raise RuntimeError('Metadata could not be saved to `{}` in `{}` format.'.format(
                        filename, config.OMEX_METADATA_OUTPUT_FORMAT.value))


class BiosimulationsOmexMetaReader(OmexMetaReader):
    """ Utility for reading the metadata about a COMBINE/OMEX archive in an OMEX Metadata
    file into a dictionary with BioSimulations schema """

    def run(self, filename_or_filenames, archive=None, working_dir=None, config=None):
        """ Read the metadata about a COMBINE/OMEX archive in an OMEX Metadata file into a dictionary
         with BioSimulations schema

        Args:
            filename_or_filenames (:obj:`str` or :obj:`list` of :obj:`str`): path or paths to OMEX Metadata files
            archive (:obj:`CombineArchive`, optional): parent COMBINE archive
            working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)
            config (:obj:`Config`, optional): configuration

        Returns:
            :obj:`tuple`:

                * :obj:`dict`: representation of the metadata about a COMBINE/OMEX
                    archive in an OMEX Metadata file as a dictionary with BioSimulations schema
                * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Metadata file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Metadata file
        """
        if config is None:
            config = get_config()

        el_metadatas = None
        errors = []
        warnings = []

        if isinstance(filename_or_filenames, (tuple, list)):
            filenames = filename_or_filenames
        else:
            filenames = [filename_or_filenames]

        triples = []
        for filename in filenames:
            rdf, temp_errors, temp_warnings = self.read_rdf(filename, config=config)

            if working_dir:
                error_filename = os.path.relpath(filename, working_dir)
            else:
                error_filename = filename

            if temp_errors:
                if isinstance(filename_or_filenames, (tuple, list)):
                    errors.append(['The OMEX Metadata file at location `{}` is invalid.'.format(error_filename), temp_errors])
                else:
                    errors.extend(temp_errors)
            else:
                triples.extend(self.get_rdf_triples(rdf))

            if temp_warnings:
                if isinstance(filename_or_filenames, (tuple, list)):
                    warnings.append(['The OMEX Metadata file at location `{}` has warnings.'.format(error_filename), temp_warnings])
                else:
                    warnings.extend(temp_warnings)

        if errors:
            return (el_metadatas, errors, warnings)

        combine_archive_uri, temp_errors, temp_warnings = self.get_combine_archive_uri(triples)
        errors.extend(temp_errors)
        warnings.extend(temp_warnings)
        if errors:
            return (el_metadatas, errors, warnings)

        el_metadatas, temp_errors, temp_warnings = self.parse_triples_to_schema(triples, combine_archive_uri)
        errors.extend(temp_errors)
        warnings.extend(temp_warnings)
        if errors:
            return (el_metadatas, errors, warnings)

        temp_errors, temp_warnings = validate_biosimulations_metadata(el_metadatas, archive=archive, working_dir=working_dir)
        errors.extend(temp_errors)
        warnings.extend(temp_warnings)

        return (el_metadatas, errors, warnings)

    @classmethod
    def get_combine_archive_uri(cls, triples):
        """ Get the URI used to the describe the COMBINE/OMEX archive in a list of RDF triples

        Args:
            triples (:obj:`list` of :obj:`dict`): representation of the OMEX Metadata file as list of triples

        Returns:
            :obj:`str`: URI used to the describe the COMBINE/OMEX archive in the list of triples
        """
        archive_uris = set()
        for triple in triples:
            if isinstance(triple.subject, rdflib.term.URIRef):
                archive_uri = re.match(BIOSIMULATIONS_ROOT_URI_PATTERN, str(triple.subject))
                if archive_uri:
                    archive_uris.add(archive_uri.group(1))

        if len(archive_uris) == 0:
            msg = 'File does not contain metadata about an OMEX archive.'
            return (None, [[msg]], [])

        elif len(archive_uris) > 1:
            msg = 'File contains metadata about multiple OMEX archives. File must contain data about 1 archive.'
            return (None, [[msg, [[uri] for uri in archive_uris]]], [])

        else:
            return (list(archive_uris)[0], [], [])

    @classmethod
    def parse_triples_to_schema(cls, triples, combine_archive_uri):
        """ Convert a graph of RDF triples into BioSimulations' metadata schema

        Args:
            triples (:obj:`list` of :obj:`dict`): representation of the OMEX Meta file as list of triples
            combine_archive_uri (:obj:`str`): URI used to the describe the COMBINE/OMEX archive in the list of triples

        Returns:
            :obj:`list` of :obj:`object`: representation of the triples in BioSimulations' metadata schema
        """
        errors = []
        warnings = []

        for triple in triples:
            subject = str(triple.subject)
            predicate = str(triple.predicate)
            object = str(triple.object)

            for ns, alias in BIOSIMULATIONS_NAMESPACE_ALIASES.items():
                if isinstance(triple.subject, rdflib.term.URIRef) and subject.startswith(ns):
                    subject = alias + subject[len(ns):]
                    triple.subject = rdflib.term.URIRef(subject)

                if isinstance(triple.predicate, rdflib.term.URIRef) and predicate.startswith(ns):
                    predicate = alias + predicate[len(ns):]
                    triple.predicate = rdflib.term.URIRef(predicate)

                if isinstance(triple.object, rdflib.term.URIRef) and object.startswith(ns):
                    object = alias + object[len(ns):]
                    triple.object = rdflib.term.URIRef(object)

        objects = {}
        for triple in triples:
            for node, is_subject in [(triple.subject, True), (triple.object, False)]:
                object = objects.get(str(node), None)
                if object is None:
                    object = objects[str(node)] = {
                        'type': node.__class__.__name__,
                        'is_subject': is_subject,
                        'is_object': not is_subject,
                    }
                    if isinstance(node, (rdflib.term.BNode, rdflib.term.URIRef)):
                        object['uri'] = str(node)
                    else:
                        object['label'] = str(node)
                object['is_subject'] = object['is_subject'] or is_subject
                object['is_object'] = object['is_object'] or not is_subject

        for triple in triples:
            subject = str(triple.subject)
            predicate = str(triple.predicate)
            object = str(triple.object)

            predicate_type = BIOSIMULATIONS_PREDICATE_TYPES.get(predicate, None)
            if predicate_type is None:
                attr = 'other'
                value = objects[object]
            else:
                attr = predicate_type['attribute']
                value = objects[object]

            if attr not in objects[subject]:
                objects[subject][attr] = []

            objects[subject][attr].append({
                'predicate': predicate,
                'value': value,
            })

        el_metadatas = []
        for uri, raw_metadata in objects.items():
            if (
                raw_metadata['type'] != 'URIRef'
                or raw_metadata['uri'].startswith('local:')
                or not raw_metadata['is_subject']
            ):
                continue

            metadata = {}
            metadata['uri'], metadata['combine_archive_uri'] = get_local_combine_archive_content_uri(uri, combine_archive_uri)
            el_metadatas.append(metadata)
            ignored_statements = []
            for predicate_uri, predicate_type in BIOSIMULATIONS_PREDICATE_TYPES.items():
                metadata[predicate_type['attribute']] = raw_metadata.get(predicate_type['attribute'], [])

                values = []
                for el in metadata[predicate_type['attribute']]:
                    if predicate_type['has_uri'] and predicate_type['has_label']:
                        value = {
                            'uri': None,
                            'label': None,
                        }
                        for sub_el in el['value'].get('other', []):
                            if (
                                sub_el['predicate'] == 'http://purl.org/dc/elements/1.1/identifier'
                                and 'uri' in sub_el['value']
                            ):
                                value['uri'] = sub_el['value']['uri']
                            elif (
                                sub_el['predicate'] == 'http://www.w3.org/2000/01/rdf-schema#label'
                                and 'label' in sub_el['value']
                            ):
                                value['label'] = sub_el['value']['label']
                        if value['label'] is None:
                            if el['value']['type'] != 'BNode':
                                msg = '({}, {}, {}) does not contain an rdf:label.'.format(
                                    uri, predicate_uri, el['value'].get('uri', None)
                                )
                                ignored_statements.append([msg])
                        else:
                            values.append(value)
                    else:
                        if predicate_type['has_uri']:
                            value = el['value'].get('uri', None)
                            if value is None:
                                msg = '({}, {}) does not contain an URI.'.format(
                                    uri, predicate_uri
                                )
                                ignored_statements.append([msg])
                            else:
                                values.append(value)

                            for sub_el in el['value'].get('other', []):
                                if 'uri' in sub_el['value']:
                                    values.append(sub_el['value']['uri'])

                        else:
                            value = el['value'].get('label', None) or None
                            if value is None:
                                if el['value']['type'] != 'BNode':
                                    msg = '({}, {}, {}) does not contain an rdf:label.'.format(
                                        uri, predicate_uri, el['value'].get('uri', None)
                                    )
                                    ignored_statements.append([msg])
                            else:
                                values.append(value)

                            for sub_el in el['value'].get('other', []):
                                if 'label' in sub_el['value']:
                                    values.append(sub_el['value']['label'])

                metadata[predicate_type['attribute']] = values

                if not predicate_type['multiple_allowed']:
                    if len(metadata[predicate_type['attribute']]) == 0:
                        metadata[predicate_type['attribute']] = None

                    elif len(metadata[predicate_type['attribute']]) == 1:
                        metadata[predicate_type['attribute']] = metadata[predicate_type['attribute']][0]

                    else:
                        metadata[predicate_type['attribute']] = metadata[predicate_type['attribute']][0]
                        msg = 'The COMBINE archive should only contain one instance of predicate `{}`.'.format(
                            predicate_uri
                        )
                        errors.append([msg])

            metadata['other'] = []
            for other_md in raw_metadata.get('other', []):
                value = {
                    'attribute': {
                        'uri': other_md['predicate'],
                        'label': None,
                    },
                    'value': {
                        'uri': None,
                        'label': None
                    },
                }
                for el in other_md['value'].get('description', []):
                    if (
                        el['predicate'] == 'http://purl.org/dc/elements/1.1/description'
                        and 'label' in el['value']
                    ):
                        value['attribute']['label'] = el['value']['label']
                for el in other_md['value'].get('other', []):
                    if (
                        el['predicate'] == 'http://purl.org/dc/elements/1.1/identifier'
                        and 'uri' in el['value']
                    ):
                        value['value']['uri'] = el['value']['uri']
                    if (
                        el['predicate'] == 'http://www.w3.org/2000/01/rdf-schema#label'
                        and 'label' in el['value']
                    ):
                        value['value']['label'] = el['value']['label']
                if value['attribute']['label'] is None or value['value']['label'] is None:
                    msg = '({}, {}, {}) does not contain an rdf:label.'.format(
                        uri, other_md['predicate'],
                        other_md['value'].get('label', None)
                        if other_md['value']['type'] == 'Literal'
                        else other_md['value'].get('uri', None)
                    )
                    ignored_statements.append([msg])
                else:
                    metadata['other'].append(value)

            for i_thumbnail, thumbnail in enumerate(metadata['thumbnails']):
                if thumbnail.startswith(combine_archive_uri + '/'):
                    metadata['thumbnails'][i_thumbnail] = './' + thumbnail[len(combine_archive_uri)+1:]
                else:
                    msg = 'Thumbnail URIs must begin with the URI of their parent archive ({}), not `{}`'.format(
                        combine_archive_uri, thumbnail)
                    errors.append([msg])

        if ignored_statements:
            warnings.append(['Some statements were ignored:', ignored_statements])

        if errors:
            return (el_metadatas, errors, warnings)

        return (el_metadatas, errors, warnings)


class BiosimulationsOmexMetaWriter(OmexMetaWriter):
    """ Utility for writing the metadata about a COMBINE/OMEX archive to an OMEX Metadata
    file """

    def run(self, el_metadatas, filename, config=None):
        """ Write an OMEX Metadata file

        Args:
            el_metadatas (:obj:`list` of :obj:`dict`): representation of the metadata about the elements in
                a COMBINE/OMEX archive in an OMEX Metadata file
            filename (:obj:`str`): path to save OMEX Metadata file
            config (:obj:`Config`, optional): configuration
        """
        if config is None:
            config = get_config()

        # convert to triples
        triples = []

        local_id = 0

        namespaces = {
            'dc': rdflib.Namespace('http://purl.org/dc/elements/1.1/'),
            'dcterms': rdflib.Namespace('http://purl.org/dc/terms/'),
            'foaf': rdflib.Namespace('http://xmlns.com/foaf/0.1/'),
            'rdfs': rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#'),
        }
        for predicate_type in BIOSIMULATIONS_PREDICATE_TYPES.values():
            namespaces[predicate_type['namespace']['prefix']] = rdflib.Namespace(predicate_type['namespace']['uri'])

        for el_metadata in el_metadatas:
            el_uri = get_global_combine_archive_content_uri(el_metadata['uri'], el_metadata['combine_archive_uri'])

            file_uri_ref = rdflib.term.URIRef(el_uri)
            for predicate_type in BIOSIMULATIONS_PREDICATE_TYPES.values():
                namespace = namespaces[predicate_type['namespace']['prefix']]
                predicate = getattr(namespace, predicate_type['uri'].replace(predicate_type['namespace']['uri'], ''))

                if predicate_type['multiple_allowed']:
                    values = el_metadata.get(predicate_type['attribute'], [])
                else:
                    value = el_metadata.get(predicate_type['attribute'], None)
                    if value is None:
                        values = []
                    else:
                        values = [value]

                for value in values:
                    if predicate_type['has_uri'] and predicate_type['has_label']:
                        local_id += 1
                        object = rdflib.term.URIRef('local:{:05d}'.format(local_id))

                        if value.get('uri', None) is not None:
                            triples.append(Triple(
                                object,
                                namespaces['dc'].identifier,
                                rdflib.term.URIRef(value['uri'])
                            ))

                        if value.get('label', None) is not None:
                            triples.append(Triple(
                                object,
                                namespaces['rdfs'].label,
                                rdflib.term.Literal(value['label'])
                            ))

                        if predicate_type['uri'] in [
                            'http://purl.org/dc/elements/1.1/creator',
                            'http://purl.org/dc/elements/1.1/contributor',
                        ]:
                            if value.get('uri', None) is not None:
                                if value['uri'].lower().startswith('mailto:'):
                                    triples.append(Triple(
                                        object,
                                        namespaces['foaf'].mbox,
                                        rdflib.term.URIRef(value['uri'])
                                    ))
                                if value['uri'].lower().startswith('tel:'):
                                    triples.append(Triple(
                                        object,
                                        namespaces['foaf'].phone,
                                        rdflib.term.URIRef(value['uri'])
                                    ))
                                else:
                                    triples.append(Triple(
                                        object,
                                        namespaces['foaf'].accountName,
                                        rdflib.term.URIRef(value['uri']
                                                           .replace('http://identifiers.org/orcid:',
                                                                    'https://orcid.org/')
                                                           .replace('https://identifiers.org/orcid:',
                                                                    'https://orcid.org/')
                                                           )
                                    ))

                            if value.get('label', None) is not None:
                                triples.append(Triple(
                                    object,
                                    namespaces['foaf'].name,
                                    rdflib.term.Literal(value['label'])
                                ))

                    elif predicate_type['has_uri']:
                        if predicate_type['uri'] == 'http://www.collex.org/schema#thumbnail':
                            value = get_global_combine_archive_content_uri(value, el_metadata['combine_archive_uri'])

                        object = rdflib.term.URIRef(value)

                    else:
                        object = rdflib.term.Literal(value)

                    triples.append(Triple(
                        subject=file_uri_ref,
                        predicate=predicate,
                        object=object,
                    ))

            for other in el_metadata.get('other', []):
                if '#' in other['attribute']['uri']:
                    namespace, _, predicate = other['attribute']['uri'].partition('#')
                    namespace += '#'
                else:
                    namespace, _, predicate = other['attribute']['uri'].rpartition('/')
                    namespace += '/'

                namespace = rdflib.Namespace(namespace)
                predicate = getattr(namespace, predicate)

                local_id += 1
                object = rdflib.term.URIRef('local:{:05d}'.format(local_id))

                triples.append(Triple(
                    subject=file_uri_ref,
                    predicate=predicate,
                    object=object,
                ))

                if other.get('attribute', {}).get('label', None) is not None:
                    triples.append(Triple(
                        object,
                        namespaces['dc'].description,
                        rdflib.term.Literal(other['attribute']['label'])
                    ))

                if other.get('value', {}).get('uri', None) is not None:
                    triples.append(Triple(
                        object,
                        namespaces['dc'].identifier,
                        rdflib.term.URIRef(other['value']['uri'])
                    ))

                if other.get('value', {}).get('label', None) is not None:
                    triples.append(Triple(
                        object,
                        namespaces['rdfs'].label,
                        rdflib.term.Literal(other['value']['label'])
                    ))

        # save triples to file
        TriplesOmexMetaWriter().run(triples, filename, namespaces=namespaces, config=config)
