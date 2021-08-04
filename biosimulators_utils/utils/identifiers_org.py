""" Utilities for working with Identifiers.org

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-08-04
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from ..config import get_app_dirs
import dataclasses
import datetime
import dateutil.parser
import functools
import os.path
import re
import requests_cache

__all__ = [
    'IdentifiersOrgCountry',
    'IdentifiersOrgInstitution',
    'IdentifiersOrgNamespaceResource',
    'IdentifiersOrgNamespace',
    'InvalidIdentifiersOrgUri',
    'get_identifiers_org_namespaces',
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
    resources: list[IdentifiersOrgNamespaceResource]
    deprecated: bool
    deprecated_date: datetime.datetime
    created: datetime.datetime
    modified: datetime.datetime


class InvalidIdentifiersOrgUri(Exception):
    """ An invalid Identifers.org URI """
    pass


@functools.cache
def get_identifiers_org_namespaces():
    """ Get the namespaces registered with `Identifiers.org <https://identifiers.org/>`_.

    Returns:
        :obj:`dict`: dictionary that maps the prefix of each Identifiers.org namespace or
            a tuple of its provider code and its prefix to its attributes
    """
    filename = os.path.join(get_app_dirs().user_cache_dir, 'identifiers-org')
    session = requests_cache.CachedSession(filename, expire_after=7*24*60*60)

    response = session.get(NAMESPACES_ENDPOINT)
    response.raise_for_status()

    namespaces = {}
    for namespace in response.json()['payload']['namespaces']:
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

        namespace_obj = IdentifiersOrgNamespace(
            id=namespace['id'],
            mir_id=namespace['mirId'],
            prefix=namespace['prefix'],
            name=namespace['name'],
            description=namespace['description'],
            pattern=re.compile(namespace['pattern']),
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

    return namespaces


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
