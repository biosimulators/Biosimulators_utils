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
        utils.append_all_nested_children_to_doc(doc)
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
        utils.append_all_nested_children_to_doc(doc)
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
        utils.append_all_nested_children_to_doc(doc)
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
        utils.append_all_nested_children_to_doc(doc)
        with self.assertRaisesRegex(ValueError, 'must define a target or symbol'):
            utils.validate_doc(doc)

        doc = data_model.SedDocument(
            outputs=[
                data_model.Report(
                    id='Report',
                    datasets=[
                        data_model.Dataset(
                        )
                    ],
                ),
            ],
        )
        with self.assertRaisesRegex(ValueError, 'must have ids'):
            utils.validate_doc(doc)
