""" Utilities for working with Identifiers.org

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-04
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..warnings import warn, BioSimulatorsWarning
import dataclasses
import datetime
import dateutil.parser
import json
import os.path
import pkg_resources
import regex as re
import requests
import typing

__all__ = [
    'IdentifiersOrgCountry',
    'IdentifiersOrgInstitution',
    'IdentifiersOrgNamespaceResource',
    'IdentifiersOrgNamespace',
    'InvalidIdentifiersOrgUri',
    'get_identifiers_org_namespaces',
    'download_identifiers_org_namespaces',
    'get_identifiers_org_namespace',
    'validate_identifiers_org_uri',
]


NAMESPACES_ENDPOINT = 'https://registry.api.identifiers.org/resolutionApi/getResolverDataset'


@dataclasses.dataclass
class IdentifiersOrgCountry(object):
    code: str
    name: str


@dataclasses.dataclass
class IdentifiersOrgInstitution(object):
    id: int
    name: str
    home_url: str
    description: str
    ror_id: str
    country: IdentifiersOrgCountry


@dataclasses.dataclass
class IdentifiersOrgNamespaceResource(object):
    id: int
    mir_id: str
    name: str
    description: str
    url_pattern: str
    official: bool
    provider_code: str
    sample_id: str
    home_url: str
    institution: IdentifiersOrgInstitution
    country: IdentifiersOrgCountry
    deprecated: bool
    deprecated_date: datetime.datetime


@dataclasses.dataclass
class IdentifiersOrgNamespace(object):
    id: int
    mir_id: str
    prefix: str
    name: str
    description: str
    pattern: re.Pattern
    embedded_in_lui: bool
    sample_id: str
    resources: typing.List[IdentifiersOrgNamespaceResource]
    deprecated: bool
    deprecated_date: datetime.datetime
    created: datetime.datetime
    modified: datetime.datetime


class InvalidIdentifiersOrgUri(Exception):
    """ An invalid Identifers.org URI """
    pass


IDENTIFIERS_ORG_NAMESPACES = None


def get_identifiers_org_namespaces(reload=False):
    """ Get the namespaces registered with `Identifiers.org <https://identifiers.org/>`_.

    Args:
        reload (:obj:`bool`, optional): whether to reload the namespaces from the Identifiers.org API

    Returns:
        :obj:`dict`: dictionary that maps the prefix of each Identifiers.org namespace or
            a tuple of its provider code and its prefix to its attributes
    """
    global IDENTIFIERS_ORG_NAMESPACES

    if IDENTIFIERS_ORG_NAMESPACES is None or reload:
        filename = pkg_resources.resource_filename('biosimulators_utils', os.path.join('utils', 'identifiers_org.json'))

        if os.path.isfile(filename) and not reload:
            with open(filename, 'r') as file:
                raw_namespaces = json.load(file)
        else:
            raw_namespaces = download_identifiers_org_namespaces()
            with open(filename, 'w') as file:
                json.dump(raw_namespaces, file)

        namespaces = {}
        skipped_namespaces = []
        for namespace in raw_namespaces:
            resources = []
            for resource in namespace['resources']:
                resources.append(IdentifiersOrgNamespaceResource(
                    id=resource['id'],
                    mir_id=resource['mirId'],
                    name=resource['name'],
                    description=resource['description'],
                    url_pattern=resource['urlPattern'],
                    official=resource['official'],
                    provider_code=resource['providerCode'],
                    sample_id=resource['sampleId'],
                    home_url=resource['resourceHomeUrl'],
                    institution=IdentifiersOrgInstitution(
                        id=resource['institution']['id'],
                        name=resource['institution']['name'],
                        home_url=resource['institution']['homeUrl'],
                        description=resource['institution']['description'],
                        ror_id=resource['institution']['rorId'],
                        country=IdentifiersOrgCountry(
                            code=resource['institution']['location']['countryCode'],
                            name=resource['institution']['location']['countryName'],
                        ),
                    ),
                    country=IdentifiersOrgCountry(
                        code=resource['location']['countryCode'],
                        name=resource['location']['countryName'],
                    ),
                    deprecated=resource['deprecated'],
                    deprecated_date=dateutil.parser.parse(resource['deprecationDate']) if resource['deprecationDate'] else None,
                ))

            try:
                pattern = re.compile(namespace['pattern'])
            except re.error as exception:
                msg = "'{}' (prefix '{}'): '{}' is not valid: {}.".format(
                    namespace['name'], namespace['prefix'], namespace['pattern'], str(exception))
                skipped_namespaces.append(msg)
                continue

            namespace_obj = IdentifiersOrgNamespace(
                id=namespace['id'],
                mir_id=namespace['mirId'],
                prefix=namespace['prefix'],
                name=namespace['name'],
                description=namespace['description'],
                pattern=pattern,
                embedded_in_lui=namespace['namespaceEmbeddedInLui'],
                sample_id=namespace['sampleId'],
                resources=resources,
                deprecated=namespace['deprecated'],
                deprecated_date=dateutil.parser.parse(namespace['deprecationDate']) if namespace['deprecationDate'] else None,
                created=dateutil.parser.parse(namespace['created']),
                modified=dateutil.parser.parse(namespace['modified']),
            )
            namespaces[namespace['prefix'].lower()] = namespace_obj
            for resource in namespace['resources']:
                namespaces[resource['providerCode'].lower() + '/' + namespace['prefix'].lower()] = namespace_obj

        if skipped_namespaces:
            msg = '{} namespaces will not be validated because their regular expression patterns are not valid:\n  - {}'.format(
                len(skipped_namespaces), '\n  - '.join(sorted(skipped_namespaces)))
            warn(msg, BioSimulatorsWarning)

        IDENTIFIERS_ORG_NAMESPACES = namespaces

    return IDENTIFIERS_ORG_NAMESPACES


def download_identifiers_org_namespaces():
    """ Get the namespaces registered with `Identifiers.org <https://identifiers.org/>`_.

    Returns:
        :obj:`dict`: dictionary that maps the prefix of each Identifiers.org namespace or
            a tuple of its provider code and its prefix to its attributes
    """
    response = requests.get(NAMESPACES_ENDPOINT)
    response.raise_for_status()
    return response.json()['payload']['namespaces']


def get_identifiers_org_namespace(prefix):
    """ Get an Identifiers.org namespace

    Args:
        prefix (:obj:`str`): prefix (e.g., ``biosimulators``) or ``/``-separated tuple of a
            provider code and prefix (e.g, ``icahn/biosimulators``)

    Returns:
        :obj:`IdentifiersOrgNamespace`: namespace

    Raises:
        :obj:`InvalidIdentifiersOrgUri`: if the prefix is not defined
    """
    try:
        return get_identifiers_org_namespaces()[prefix]
    except KeyError:
        raise InvalidIdentifiersOrgUri('`{}` is not a valid prefix of a Identifiers.org namespace.'.format(prefix))


def validate_identifiers_org_uri(uri):
    """ Determine whether a URI is a validate for one of the namespaces registered with Identifiers.org

    Raises:
        :obj:`InvalidIdentifiersOrgUri`: if the URI is not a valid with one of the namespaces registered with Identifiers.org
    """
    match = re.match(r'^https?://identifiers\.org/((([^/:]+)/([^/:]+)|[^/:]+)([/:])(.+))$', uri)
    try:
        namespace = get_identifiers_org_namespace(match.group(2).lower())
    except InvalidIdentifiersOrgUri:
        if match.group(3):
            namespace = get_identifiers_org_namespace(match.group(3).lower())
        else:
            raise

    if (
        not (
            not (match.group(5) in [':', '/'] and ':' in match.group(6)) and
            re.match(namespace.pattern, match.group(6))
        ) and
        not re.match(namespace.pattern, match.group(1)) and
        not (match.group(4) and re.match(namespace.pattern, match.group(4) + match.group(5) + match.group(6)))
    ):
        raise InvalidIdentifiersOrgUri('Identifier `{}` is not valid for the `{}` namespace.'.format(
            match.group(4) + match.group(5) + match.group(6) if match.group(4) else match.group(6),
            namespace.prefix))
