from biosimulators_utils.sedml import data_model
from biosimulators_utils.sedml import utils
import unittest


class SedmlUtilsTestCase(unittest.TestCase):
    def test(self):
        doc = data_model.SedDocument(
            models=[
                data_model.Model(
                    id='model',
                    changes=[
                        data_model.ModelAttributeChange(),
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must define a target'):
            utils.validate_doc(doc)

        doc = data_model.SedDocument(
            simulations=[
                data_model.OneStepSimulation(
                    id='sim',
                    algorithm=data_model.Algorithm(
                        kisao_id='KISAO:0000029',
                    ),
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'invalid KiSAO id'):
            utils.validate_doc(doc)

        doc = data_model.SedDocument(
            simulations=[
                data_model.OneStepSimulation(
                    id='sim',
                    algorithm=data_model.Algorithm(
                        kisao_id='KISAO_0000029',
                        changes=[
                            data_model.AlgorithmParameterChange(
                                kisao_id='KISAO:0000001',
                            )
                        ],
                    ),
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'invalid KiSAO id'):
            utils.validate_doc(doc)

        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    id='data_gen',
                    variables=[
                        data_model.DataGeneratorVariable(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must define a target or symbol'):
            utils.validate_doc(doc)

        doc = data_model.SedDocument(
            data_generators=[
                data_model.DataGenerator(
                    id='data_gen',
                    variables=[
                        data_model.DataGeneratorVariable(
                            target="target",
                            symbol="symbol",
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must define a target or symbol'):
            utils.validate_doc(doc)
