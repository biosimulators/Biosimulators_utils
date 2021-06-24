""" Methods for reading and writing OMEX Meta files

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-23
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ...log.data_model import StandardOutputErrorCapturerLevel
from ...log.utils import StandardOutputErrorCapturer
from .data_model import ROOT_URI_PATTERN, PREDICATE_TYPES
import dateutil.parser
import json
import os
import pyomexmeta
import re


class BiosimulationsOmexMetaReader(object):
    @classmethod
    def run(cls, filename):
        errors = []
        warnings = []

        rdf, tmp_errors, tmp_warnings = cls.read_rdf(filename)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (None, errors, warnings)

        graph = cls.get_rdf_graph(rdf)

        root_uri, tmp_errors, tmp_warnings = cls.get_omex_uri(graph)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (None, errors, warnings)

        metadata, tmp_errors, tmp_warnings = cls.parse_graph_for_uri(graph, root_uri)
        errors.extend(tmp_errors)
        warnings.extend(tmp_warnings)
        if errors:
            return (None, errors, warnings)

        return (metadata, errors, warnings)

    @staticmethod
    def read_rdf(filename, format='rdfxml'):
        rdf = None
        errors = []
        warnings = []

        if not os.path.isfile(filename):
            errors.append(['`{}` is not a file.'.format(filename)])
            return (rdf, errors, warnings)

        with StandardOutputErrorCapturer(relay=False, level=StandardOutputErrorCapturerLevel.c) as captured:
            rdf = pyomexmeta.RDF.from_file(filename, format)
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

    @staticmethod
    def get_rdf_graph(rdf):
        query = "SELECT ?subject ?predicate ?object WHERE { ?subject ?predicate ?object }"
        return json.loads(rdf.query(query, 'json'))['results']['bindings']

    @staticmethod
    def get_omex_uri(graph):
        root_uris = set()
        for triple in graph:
            if triple['subject']['type'] == 'uri' and re.match(ROOT_URI_PATTERN, triple['subject']['value']):
                root_uris.add(triple['subject']['value'])

        if len(root_uris) == 0:
            msg = 'File does not contain metadata about an OMEX archive.'
            return(None, [[msg]], [])

        elif len(root_uris) > 1:
            msg = 'File contains metadata about multiple OMEX archives. File must contains data about 1 archive.'
            return(None, [[msg]], [])

        else:
            return (list(root_uris)[0], [], [])

    @staticmethod
    def parse_graph_for_uri(graph, root_uri):
        errors = []
        warnings = []

        objects = {}
        for triple in graph:
            if triple['subject']['type'] == 'uri' and re.match(ROOT_URI_PATTERN, triple['subject']['value']):
                root_uri = triple['subject']['value']

            for node in [triple['subject'], triple['object']]:
                if node['type'] in ['uri', 'bnode']:
                    objects[node['value']] = {
                        'type': node['type'],
                        'uri': node['value'],
                    }
                else:
                    objects[node['value']] = {
                        'type': node['type'],
                        'label': node['value'],
                    }

        for triple in graph:
            subject = triple['subject']
            predicate = triple['predicate']
            object = triple['object']

            subject = subject['value']
            predicate = predicate['value']
            object = object['value']

            predicate_type = PREDICATE_TYPES.get(predicate, None)
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

        raw_metadata = objects[root_uri]
        metadata = {}
        ignored_statements = []
        for predicate_uri, predicate_type in PREDICATE_TYPES.items():
            metadata[predicate_type['attribute']] = raw_metadata.get(predicate_type['attribute'], [])

            values = []
            for el in metadata[predicate_type['attribute']]:
                if predicate_type['has_uri'] and predicate_type['has_label']:
                    value = {
                        'uri': None,
                        'label': None,
                    }
                    for sub_el in el['value'].get('other', []):
                        if 'uri' in sub_el['value']:
                            value['uri'] = sub_el['value']['uri']
                        elif 'label' in sub_el['value']:
                            value['label'] = sub_el['value']['label']
                    if value['label'] is None:
                        if el['value']['type'] != 'bnode':
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
                            if el['value']['type'] != 'bnode':
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

            if predicate_type['required'] and (
                (not predicate_type['multiple_allowed'] and metadata[predicate_type['attribute']] is None)
                or (predicate_type['multiple_allowed'] and metadata[predicate_type['attribute']] == [])
            ):
                errors.append(['The COMBINE archive must be annotated with the predicate `{}`.'.format(
                    predicate_type['uri'])])

        metadata['other'] = []
        for other_md in raw_metadata['other']:
            value = {'attribute': other_md['predicate'], 'attribute_label': None, 'uri': None, 'label': None}
            for el in other_md['value'].get('description', []):
                if 'label' in el['value']:
                    value['attribute_label'] = el['value']['label']
            for el in other_md['value'].get('other', []):
                if 'uri' in el['value']:
                    value['uri'] = el['value']['uri']
                if 'label' in el['value']:
                    value['label'] = el['value']['label']
            if value['attribute_label'] is None or value['label'] is None:
                msg = '({}, {}, {}) does not contain an rdf:label.'.format(
                    root_uri, other_md['predicate'], other_md['value']['uri']
                )
                ignored_statements.append([msg])
            else:
                metadata['other'].append(value)

        metadata['thumbnails'] = [re.sub(ROOT_URI_PATTERN[0:-1], '.', thumbnail) for thumbnail in metadata['thumbnails']]
        if metadata['created'] is not None:
            metadata['created'] = dateutil.parser.parse(metadata['created'])
        metadata['modified'] = [dateutil.parser.parse(d) for d in metadata['modified']]

        if ignored_statements:
            warnings.append(['Some statements were ignored:', ignored_statements])

        return (metadata, errors, warnings)
