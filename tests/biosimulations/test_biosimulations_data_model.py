import unittest
from biosimulators_utils.biosimulations import data_model
from biosimulators_utils.data_model import Person, Identifier


class DataModelTestCase(unittest.TestCase):
    def test(self):
        identifier1 = Identifier(namespace='KISAO', id='KISAO_0000029')
        identifier2 = Identifier(namespace='KISAO', id='KISAO_0000029')
        identifier3 = Identifier(namespace='KISAO', id='KISAO_0000028')

        citation1 = data_model.Citation(title='title', authors='authors')
        citation2 = data_model.Citation(title='title', authors='authors')
        citation3 = data_model.Citation(title='title2', authors='authors2')
        self.assertTrue(citation1.is_equal(citation2))
        self.assertFalse(citation1.is_equal(citation3))

        refs1 = data_model.ExternalReferences(
            identifiers=[identifier1, identifier3],
            citations=[citation1, citation3],
        )
        refs2 = data_model.ExternalReferences(
            identifiers=[identifier1, identifier3],
            citations=[citation1, citation3],
        )
        refs3 = data_model.ExternalReferences(
            identifiers=[identifier1, identifier2],
            citations=[citation1, citation3],
        )
        self.assertTrue(refs1.is_equal(refs2))
        self.assertFalse(refs1.is_equal(refs3))
        self.assertEqual(refs1.to_tuple(), (
            (identifier3.to_tuple(), identifier1.to_tuple()),
            (citation1.to_tuple(), citation3.to_tuple()),
        ))

        person1 = Person(given_name='first', family_name='last')
        person2 = Person(given_name='first3', family_name='last3')

        metadata1 = data_model.Metadata(
            description="description",
            tags=["tag1", "tag2"],
            authors=[person1, person2],
            references=refs1,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="MIT",
            ))
        metadata2 = data_model.Metadata(
            description="description",
            tags=["tag1", "tag2"],
            authors=[person1, person2],
            references=refs1,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="MIT",
            ))
        self.assertTrue(metadata1.is_equal(metadata2))

        metadata3 = data_model.Metadata(
            description="description2",
            tags=["tag1", "tag2"],
            authors=[person1, person2],
            references=refs1,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="MIT",
            ))
        self.assertFalse(metadata1.is_equal(metadata3))

        metadata3 = data_model.Metadata(
            description="description",
            tags=["tag2", "tag2"],
            authors=[person1, person2],
            references=refs1,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="MIT",
            ))
        self.assertFalse(metadata1.is_equal(metadata3))

        metadata3 = data_model.Metadata(
            description="description",
            tags=["tag1", "tag2"],
            authors=[person1, person1],
            references=refs1,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="MIT",
            ))
        self.assertFalse(metadata1.is_equal(metadata3))

        metadata3 = data_model.Metadata(
            description="description",
            tags=["tag1", "tag2"],
            authors=[person1, person2],
            references=refs3,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="MIT",
            ))
        self.assertFalse(metadata1.is_equal(metadata3))

        metadata3 = data_model.Metadata(
            description="description",
            tags=["tag1", "tag2"],
            authors=[person1, person2],
            references=refs1,
            license=data_model.OntologyTerm(
                namespace="SPDX",
                id="Apache-2.0",
            ))
        self.assertFalse(metadata1.is_equal(metadata3))

        self.assertEqual(metadata1.to_tuple()[0], metadata1.description)
        self.assertEqual(metadata1.to_tuple()[1], tuple(metadata1.tags))
        self.assertEqual(metadata1.to_tuple()[2], tuple([person1.to_tuple(), person2.to_tuple()]))
        self.assertEqual(metadata1.to_tuple()[3], tuple(refs1.to_tuple(),))
        self.assertEqual(metadata1.to_tuple()[4], metadata1.license.to_tuple())
