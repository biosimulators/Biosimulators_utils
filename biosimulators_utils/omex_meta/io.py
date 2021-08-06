""" Methods for reading and writing OMEX Meta files

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-23
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..combine.data_model import CombineArchive, CombineArchiveContentFormatPattern  # noqa: F401
from ..log.data_model import StandardOutputErrorCapturerLevel
from ..log.utils import StandardOutputErrorCapturer
from .data_model import (Triple, OmexMetaInputFormat, OmexMetaOutputFormat, OmexMetaSchema,
                         BIOSIMULATIONS_ROOT_URI_FORMAT,
                         BIOSIMULATIONS_ROOT_URI_PATTERN,
                         BIOSIMULATIONS_PREDICATE_TYPES)
from .validation import validate_biosimulations_metadata
import abc
import json
import os
import pyomexmeta
import rdflib
import re

__all__ = [
    'read_omex_meta_file',
    'write_omex_meta_file',
    'read_omex_meta_files_for_archive',
    'TriplesOmexMetaReader',
    'TriplesOmexMetaWriter',
    'BiosimulationsOmexMetaReader',
    'BiosimulationsOmexMetaWriter',
]


def read_omex_meta_file(filename, schema, format=OmexMetaInputFormat.rdfxml, archive=None, working_dir=None):
    """ Read an OMEX Meta file

    Args:
        filename (:obj:`str`): path to OMEX Meta file
        schema (:obj:`OmexMetaSchema`): schema to parse :obj:`filename` into
        format (:obj:`OmexMetaInputFormat`, optional): format for :obj:`filename`
        archive (:obj:`CombineArchive`, optional): parent COMBINE archive
        working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)

    Returns:
        :obj:`tuple`:

            * :obj:`object`: representation of the OMEX Meta file in :obj:`schema`
            * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Meta file
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Meta file
    """
    content = None
    errors = []
    warnings = []

    if schema == OmexMetaSchema.biosimulations:
        return BiosimulationsOmexMetaReader().run(filename, format=format, archive=archive, working_dir=working_dir)

    elif schema == OmexMetaSchema.rdf_triples:
        return TriplesOmexMetaReader().run(filename, format=format, archive=archive, working_dir=working_dir)

    else:
        errors.append(['Schema `{}` is not supported. The following schemas are supported:',
                       [['None']] + sorted([
                           [schema.value] for schema in OmexMetaSchema.__members__.values()
                       ])])
        return (content, errors, warnings)


def write_omex_meta_file(content, schema, filename, format=OmexMetaOutputFormat.rdfxml_abbrev):
    """ Write an OMEX Meta file

    Args:
        content (:obj:`object`): representation of the OMEX Meta file in :obj:`schema`
        schema (:obj:`OmexMetaSchema`): schema for :obj:`content` into
        filename (:obj:`str`): path to save OMEX Meta file
        format (:obj:`OmexMetaOutputFormat`, optional): format for :obj:`filename`
    """
    if schema == OmexMetaSchema.biosimulations:
        return BiosimulationsOmexMetaWriter().run(content, filename, format=format)

    elif schema == OmexMetaSchema.rdf_triples:
        return TriplesOmexMetaWriter().run(content, filename, format=format)

    else:
        msg = 'Schema `{}` is not supported. The following schemas are supported:\n  {}'.format(
            schema,
            '\n  '.join(['None'] + sorted([schema.value for schema in OmexMetaSchema.__members__.values()])))
        raise NotImplementedError(msg)


def read_omex_meta_files_for_archive(archive, archive_dirname, schema):
    """ Read all of the OMEX Meta files in an archive

    Args:
        archive (:obj:`CombineArchive`): COMBINE/OMEX archive
        archive_dirname (:obj:`str`): directory with the content of the archive
        schema (:obj:`OmexMetaSchema`): schema to parse :obj:`filename` into

    Returns:
        :obj:`tuple`:

            * :obj:`object`: representation of the OMEX Meta file in :obj:`schema`
            * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Meta file
            * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Meta file
    """
    content = []
    errors = []
    warnings = []

    for item in archive.contents:
        if item.format and re.match(CombineArchiveContentFormatPattern.OMEX_METADATA.value, item.format):
            temp_content, temp_errors, temp_warnings = read_omex_meta_file(
                os.path.join(archive_dirname, item.location),
                schema=schema, archive=archive, working_dir=archive_dirname)

            if temp_errors:
                errors.append(['OMEX Meta file `{}` is invalid.'.format(item.location), temp_errors])
            else:
                content.extend(temp_content)

            if temp_warnings:
                warnings.append(['OMEX Meta file `{}` may be invalid.'.format(item.location), temp_warnings])

    return (content, errors, warnings)


class OmexMetaReader(abc.ABC):
    """ Base class for reading OMEX Meta files """

    @ abc.abstractmethod
    def run(self, filename, format=OmexMetaInputFormat.rdfxml, archive=None, working_dir=None):
        """ Read an OMEX Meta file

        Args:
            filename (:obj:`str`): path to OMEX Meta file
            format (:obj:`OmexMetaInputFormat`, optional): format for :obj:`filename`
            archive (:obj:`CombineArchive`, optional): parent COMBINE archive
            working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)

        Returns:
            :obj:`tuple`:

                * :obj:`object`: representation of the OMEX Meta file
                * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Meta file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Meta file
        """
        pass  # pragma: no cover

    @ classmethod
    def read_rdf(cls, filename, format=OmexMetaInputFormat.rdfxml):
        """ Read an RDF file

        Args:
            filename (:obj:`str`): path to the RDF file
            format (:obj:`OmexMetaInputFormat`, optional): format for :obj:`filename`

        Returns:
            :obj:`tuple`:

                * :obj:`pyomexmeta.RDF`: RDF representation of the file
                * nested :obj:`list` of :obj:`str`: nested list of errors with the RDF file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the RDF file
        """
        rdf = None
        errors = []
        warnings = []

        if not os.path.isfile(filename):
            errors.append(['`{}` is not a file.'.format(filename)])
            return (rdf, errors, warnings)

        with StandardOutputErrorCapturer(relay=False, level=StandardOutputErrorCapturerLevel.c) as captured:
            rdf = pyomexmeta.RDF.from_file(filename, format.value)
            stdout = captured.get_text().strip()
        if stdout:
            errors_warnings = re.split(r'((^|\n)librdf (error|warning)) *-? *', stdout)
            for type, message in zip(errors_warnings[3::4], errors_warnings[4::4]):
                message = message.strip()
                if 'error' in type:
                    rdf = None
                    errors.append([message])
                else:
                    warnings.append([message])

        return (rdf, errors, warnings)

    @ classmethod
    def get_rdf_triples(cls, rdf):
        """ Read an RDF file

        Args:
            rdf (:obj:`pyomexmeta.RDF`): RDF representation of the file

        Returns:
            * :obj:`list` of :obj:`Triple`: representation of the OMEX Meta file as list of triples
        """
        query = "SELECT ?subject ?predicate ?object WHERE { ?subject ?predicate ?object }"
        plain_triples = json.loads(rdf.query(query, 'json'))['results']['bindings']
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

    @ classmethod
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
    """ Base class for writing OMEX Meta files """

    @ abc.abstractmethod
    def run(self, content, filename, format=OmexMetaOutputFormat.rdfxml_abbrev):
        """ Write an OMEX Meta file

        Args:
            content (:obj:`object`): representation of the OMEX Meta file
            filename (:obj:`str`): path to save OMEX Meta file
            format (:obj:`OmexMetaOutputFormat`, optional): format for :obj:`filename`
        """
        pass  # pragma: no cover


class TriplesOmexMetaReader(OmexMetaReader):
    """ Utility for reading an OMEX Meta file into a list of triples """

    def run(self, filename, format=OmexMetaInputFormat.rdfxml, archive=None, working_dir=None):
        """ Read an OMEX Meta file into a list of triples

        Args:
            filename (:obj:`str`): path to OMEX Meta file
            format (:obj:`OmexMetaInputFormat`, optional): format for :obj:`filename`
            archive (:obj:`CombineArchive`, optional): parent COMBINE archive
            working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)

        Returns:
            :obj:`tuple`:

                * :obj:`list` of :obj:`dict`: representation of the OMEX Meta file as list of triples
                * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Meta file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Meta file
        """
        triples = None
        errors = []
        warnings = []

        rdf, tmp_errors, tmp_warnings = self.read_rdf(filename, format=format)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (triples, errors, warnings)

        triples = self.get_rdf_triples(rdf)

        return (triples, errors, warnings)


class TriplesOmexMetaWriter(OmexMetaWriter):
    """ Utility for writing a list of triples to an OMEX Meta file """

    def run(self, triples, filename, namespaces=None, format=OmexMetaOutputFormat.rdfxml):
        """ Write a list of triples to an OMEX Meta file

        Args:
            triples (:obj:`list` of :obj:`Triple`): representation of the OMEX Meta file as list of triples
            filename (:obj:`str`): path to OMEX Meta file
            format (:obj:`OmexMetaOutputFormat`, optional): format for :obj:`filename`
        """
        graph = rdflib.Graph()
        for prefix, namespace in (namespaces or {}).items():
            graph.namespace_manager.bind(prefix, namespace)
        # graph.namespace_manager.bind('omexLibrary', rdflib.Namespace('http://omex-library.org/'))
        # graph.namespace_manager.bind('identifiers', rdflib.Namespace('http://identifiers.org/'))

        for triple in triples:
            graph.add((triple.subject, triple.predicate, triple.object))

        if format == OmexMetaOutputFormat.rdfxml:
            graph.serialize(filename, format="xml")

        elif format == OmexMetaOutputFormat.turtle:
            graph.serialize(filename, format="turtle")

        else:
            graph.serialize(filename, format="xml")
            rdf = pyomexmeta.RDF.from_file(filename, 'rdfxml')
            if rdf.to_file(filename, format.value) != 0:
                raise RuntimeError('Metadata could not be saved to `{}` in `{}` format.'.format(
                    filename, format.value))


class BiosimulationsOmexMetaReader(OmexMetaReader):
    """ Utility for reading the metadata about a COMBINE/OMEX archive in an OMEX Meta
    file into a dictionary with BioSimulations schema """

    def run(self, filename, format=OmexMetaInputFormat.rdfxml, archive=None, working_dir=None):
        """ Read the metadata about a COMBINE/OMEX archive in an OMEX Meta file into a dictionary
         with BioSimulations schema

        Args:
            filename (:obj:`str`): path to OMEX Meta file
            format (:obj:`OmexMetaInputFormat`, optional): format for :obj:`filename`
            archive (:obj:`CombineArchive`, optional): parent COMBINE archive
            working_dir (:obj:`str`, optional): working directory (e.g., directory of the parent COMBINE/OMEX archive)

        Returns:
            :obj:`tuple`:

                * :obj:`dict`: representation of the metadata about a COMBINE/OMEX
                    archive in an OMEX Meta file as a dictionary with BioSimulations schema
                * nested :obj:`list` of :obj:`str`: nested list of errors with the OMEX Meta file
                * nested :obj:`list` of :obj:`str`: nested list of warnings with the OMEX Meta file
        """
        el_metadatas = None
        errors = []
        warnings = []

        rdf, tmp_errors, tmp_warnings = self.read_rdf(filename, format=format)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (el_metadatas, errors, warnings)

        triples = self.get_rdf_triples(rdf)

        root_uri, tmp_errors, tmp_warnings = self.get_combine_archive_uri(triples)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (el_metadatas, errors, warnings)

        el_metadatas, tmp_errors, tmp_warnings = self.parse_triples_to_schema(triples, root_uri)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (el_metadatas, errors, warnings)

        for el_metadata in el_metadatas:
            temp_errors, temp_warnings = validate_biosimulations_metadata(el_metadata, archive=archive, working_dir=working_dir)

            if temp_errors:
                errors.append(['The metadata for URI `{}` is invalid.'.format(
                    el_metadata['uri']), temp_errors])

            if temp_warnings:
                warnings.append(['The metadata for URI `{}` may be invalid.'.format(
                    el_metadata['uri']),  temp_warnings])

        return (el_metadatas, errors, warnings)

    @ classmethod
    def get_combine_archive_uri(cls, triples):
        """ Get the URI used to the describe the COMBINE/OMEX archive in a list of RDF triples

        Args:
            triples (:obj:`list` of :obj:`dict`): representation of the OMEX Meta file as list of triples

        Returns:
            :obj:`str`: URI used to the describe the COMBINE/OMEX archive in the list of triples
        """
        root_uris = set()
        for triple in triples:
            if (
                isinstance(triple.subject, rdflib.term.URIRef)
                and re.match(BIOSIMULATIONS_ROOT_URI_PATTERN, str(triple.subject))
            ):
                root_uris.add(str(triple.subject))

        if len(root_uris) == 0:
            msg = 'File does not contain metadata about an OMEX archive.'
            return(None, [[msg]], [])

        elif len(root_uris) > 1:
            msg = 'File contains metadata about multiple OMEX archives. File must contains data about 1 archive.'
            return(None, [[msg]], [])

        else:
            return (list(root_uris)[0], [], [])

    @classmethod
    def parse_triples_to_schema(cls, triples, root_uri):
        """ Convert a graph of RDF triples into BioSimulations' metadata schema

        Args:
            triples (:obj:`list` of :obj:`dict`): representation of the OMEX Meta file as list of triples
            root_uri (:obj:`str`): URI used to the describe the COMBINE/OMEX archive in the list of triples

        Returns:
            :obj:`list` of :obj:`object`: representation of the triples in BioSimulations' metadata schema
        """
        errors = []
        warnings = []

        objects = {}
        for triple in triples:
            if (
                isinstance(triple.subject, rdflib.term.URIRef)
                and re.match(BIOSIMULATIONS_ROOT_URI_PATTERN, str(triple.subject))
            ):
                root_uri = str(triple.subject)

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
            if (uri != root_uri and not uri.startswith(root_uri + '/')) or not raw_metadata['is_subject']:
                continue

            metadata = {
                'uri': '.' + uri[len(root_uri):]
            }
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
                                sub_el['predicate'] == 'http://dublincore.org/specifications/dublin-core/dcmi-terms/identifier'
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
                                    root_uri, predicate_uri, el['value']['uri']
                                )
                                ignored_statements.append([msg])
                        else:
                            values.append(value)
                    else:
                        if predicate_type['has_uri']:
                            value = el['value'].get('uri', None)
                            if value is None:
                                msg = '({}, {}) does not contain an URI.'.format(
                                    root_uri, predicate_uri
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
                                        root_uri, predicate_uri, el['value']['uri']
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
                        el['predicate'] == 'http://dublincore.org/specifications/dublin-core/dcmi-terms/description'
                        and 'label' in el['value']
                    ):
                        value['attribute']['label'] = el['value']['label']
                for el in other_md['value'].get('other', []):
                    if (
                        el['predicate'] == 'http://dublincore.org/specifications/dublin-core/dcmi-terms/identifier'
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
                        root_uri, other_md['predicate'],
                        other_md['value']['label']
                        if other_md['value']['type'] == 'Literal'
                        else other_md['value']['uri']
                    )
                    ignored_statements.append([msg])
                else:
                    metadata['other'].append(value)

            for i_thumbnail, thumbnail in enumerate(metadata['thumbnails']):
                if thumbnail.startswith(root_uri):
                    metadata['thumbnails'][i_thumbnail] = './' + thumbnail[len(root_uri)+1:]
                else:
                    msg = 'Thumbnail URIs must begin with the URI of their parent archive ({}), not `{}`'.format(
                        root_uri, thumbnail)
                    errors.append([msg])

        if ignored_statements:
            warnings.append(['Some statements were ignored:', ignored_statements])

        if errors:
            return (el_metadatas, errors, warnings)

        return (el_metadatas, errors, warnings)


class BiosimulationsOmexMetaWriter(OmexMetaWriter):
    """ Utility for writing the metadata about a COMBINE/OMEX archive to an OMEX Meta
    file """

    def run(self, el_metadatas, filename, format=OmexMetaOutputFormat.rdfxml_abbrev):
        """ Write an OMEX Meta file

        Args:
            el_metadatas (:obj:`list` of :obj:`dict`): representation of the metadata about the elements in
                a COMBINE/OMEX archive in an OMEX Meta file
            filename (:obj:`str`): path to save OMEX Meta file
            format (:obj:`OmexMetaOutputFormat`, optional): format for :obj:`filename`
        """
        # convert to triples
        triples = []

        combine_archive_uri = BIOSIMULATIONS_ROOT_URI_FORMAT.format('archive')
        local_id = 0

        namespaces = {
            'dc': rdflib.Namespace('http://dublincore.org/specifications/dublin-core/dcmi-terms/'),
            'dcterms': rdflib.Namespace('http://purl.org/dc/terms/'),
            'foaf': rdflib.Namespace('http://xmlns.com/foaf/0.1/'),
            'rdfs': rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#'),
        }
        for predicate_type in BIOSIMULATIONS_PREDICATE_TYPES.values():
            namespaces[predicate_type['namespace']['prefix']] = rdflib.Namespace(predicate_type['namespace']['uri'])

        for el_metadata in el_metadatas:
            file_uri_ref = rdflib.term.URIRef(combine_archive_uri + el_metadata['uri'][1:])
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
                            'http://dublincore.org/specifications/dublin-core/dcmi-terms/creator',
                            'http://dublincore.org/specifications/dublin-core/dcmi-terms/contributor',
                        ]:
                            if value.get('uri', None) is not None:
                                triples.append(Triple(
                                    object,
                                    namespaces['foaf'].accountName,
                                    rdflib.term.URIRef(value['uri']
                                                       .replace('https://identifiers.org/orcid:',
                                                                'https://orcid.org/'))
                                ))

                            if value.get('label', None) is not None:
                                triples.append(Triple(
                                    object,
                                    namespaces['foaf'].name,
                                    rdflib.term.Literal(value['label'])
                                ))

                    elif predicate_type['has_uri']:
                        if predicate_type['uri'] == 'http://www.collex.org/schema#thumbnail':
                            value = combine_archive_uri + '/' + value

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
        TriplesOmexMetaWriter().run(triples, filename, namespaces=namespaces, format=format)
