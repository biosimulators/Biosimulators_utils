from biosimulators_utils.utils.identifiers_org import (
    IdentifiersOrgNamespace,
    InvalidIdentifiersOrgUri,
    get_identifiers_org_namespaces,
    get_identifiers_org_namespace,
    validate_identifiers_org_uri,
)
import unittest


class IdentifiersOrgUtilsTestCase(unittest.TestCase):
    def test_get_identifiers_org_namespaces(self):
        namespaces = get_identifiers_org_namespaces()
        self.assertIsInstance(namespaces, dict)
        self.assertIsInstance(namespaces['biosimulators'], IdentifiersOrgNamespace)

        get_identifiers_org_namespaces()

    def test_get_identifiers_org_namespace(self):
        namespace = get_identifiers_org_namespace('pubmed')
        self.assertIsInstance(namespace, IdentifiersOrgNamespace)

        namespace = get_identifiers_org_namespace('ncbi/pubmed')
        self.assertIsInstance(namespace, IdentifiersOrgNamespace)

    def test_validate_identifiers_org_uri(self):
        validate_identifiers_org_uri('http://identifiers.org/pubmed:1234')
        validate_identifiers_org_uri('https://identifiers.org/pubmed:1234')
        validate_identifiers_org_uri('http://identifiers.org/PUBMED:1234')
        validate_identifiers_org_uri('http://identifiers.org/pubmed/1234')
        validate_identifiers_org_uri('http://identifiers.org/ncbi/pubmed:1234')
        validate_identifiers_org_uri('http://identifiers.org/NCBI/pubmed:1234')
        validate_identifiers_org_uri('http://identifiers.org/NCBI/PUBMED:1234')

        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('https://identifiers.org/pubmed:abc')
        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('https://identifiers.org/ncbi/pubmed:abc')
        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('http://identifiers.org/ncbi:1234')
        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('http://identifiers.org/ncbi/1234')

        validate_identifiers_org_uri('http://identifiers.org/CL:0001057')
        validate_identifiers_org_uri('http://identifiers.org/cl/CL:0001057')
        validate_identifiers_org_uri('http://identifiers.org/ols/CL:0001057')

        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('http://identifiers.org/cl:0001057')
        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('http://identifiers.org/cl:CL:0001057')
        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('http://identifiers.org/ols/cl:CL:0001057')
        with self.assertRaises(InvalidIdentifiersOrgUri):
            validate_identifiers_org_uri('http://identifiers.org/ols/cl/CL:0001057')
