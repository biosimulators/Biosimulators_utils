from biosimulators_utils.combine import utils
from biosimulators_utils.combine import data_model
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from unittest import mock
import os
import shutil
import tempfile
import unittest


class CombineUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_get_sedml_contents(self):
        archive = data_model.CombineArchive(contents=[
            data_model.CombineArchiveContent(location='file_1', format=data_model.CombineArchiveContentFormat.SED_ML, master=True),
            data_model.CombineArchiveContent(location='file_2', format=data_model.CombineArchiveContentFormat.SED_ML, master=False),
            data_model.CombineArchiveContent(location='file_3', format=data_model.CombineArchiveContentFormat.SBML, master=False),
            data_model.CombineArchiveContent(location='file_4', format=data_model.CombineArchiveContentFormat.BNGL, master=False),
        ])
        self.assertEqual(utils.get_sedml_contents(archive), archive.contents[0:1])
        self.assertEqual(utils.get_sedml_contents(archive, always_include_all_sed_docs=True), archive.contents[0:2])

        archive.contents[0].master = False
        self.assertEqual(utils.get_sedml_contents(archive), archive.contents[0:2])
        self.assertEqual(utils.get_sedml_contents(archive, always_include_all_sed_docs=True), archive.contents[0:2])

        archive.contents[2].master = True
        self.assertEqual(utils.get_sedml_contents(archive), archive.contents[0:2])
        self.assertEqual(utils.get_sedml_contents(archive, include_all_sed_docs_when_no_sed_doc_is_master=False), [])

    def test_get_summary_sedml_contents(self):
        archive = data_model.CombineArchive(contents=[
            data_model.CombineArchiveContent(location='./exp_2.sedml', format=data_model.CombineArchiveContentFormat.SED_ML, master=False),
            data_model.CombineArchiveContent(location='./exp_1.sedml', format=data_model.CombineArchiveContentFormat.SED_ML, master=False),
        ])

        exp_1 = sedml_data_model.SedDocument()
        model_1 = sedml_data_model.Model(id='model_1', language=sedml_data_model.ModelLanguage.SBML.value, source='./model.xml')
        exp_1.models.append(model_1)
        sim_1 = sedml_data_model.SteadyStateSimulation(id='sim_1', algorithm=sedml_data_model.Algorithm(kisao_id='KISAO_0000019'))
        exp_1.simulations.append(sim_1)
        task_1 = sedml_data_model.Task(id='task_1', model=model_1, simulation=sim_1)
        task_2 = sedml_data_model.Task(id='task_2', model=model_1, simulation=sim_1)
        exp_1.tasks.append(task_1)
        exp_1.tasks.append(task_2)
        exp_1.outputs.append(sedml_data_model.Report(id='report_1'))
        exp_1.outputs.append(sedml_data_model.Plot2D(id='plot_2'))
        SedmlSimulationWriter().run(exp_1, os.path.join(self.dirname, 'exp_1.sedml'),
                                    validate_semantics=False, validate_models_with_languages=False)

        exp_2 = sedml_data_model.SedDocument()
        model_2 = sedml_data_model.Model(id='model_2', language=sedml_data_model.ModelLanguage.SBML.value, source='./model.xml')
        exp_2.models.append(model_2)
        sim_2 = sedml_data_model.SteadyStateSimulation(id='sim_2', algorithm=sedml_data_model.Algorithm(kisao_id='KISAO_0000019'))
        exp_2.simulations.append(sim_2)
        task_3 = sedml_data_model.Task(id='task_3', model=model_2, simulation=sim_2)
        exp_2.tasks.append(task_3)
        exp_2.outputs.append(sedml_data_model.Report(id='report_3'))
        exp_2.outputs.append(sedml_data_model.Plot3D(id='plot_5'))
        exp_2.outputs.append(sedml_data_model.Plot2D(id='plot_4'))
        SedmlSimulationWriter().run(exp_2, os.path.join(self.dirname, 'exp_2.sedml'),
                                    validate_semantics=False, validate_models_with_languages=False)

        with mock.patch('biosimulators_utils.sedml.validation.validate_output', return_value=([], [])):
            summary = utils.get_summary_sedml_contents(archive, self.dirname)
        self.assertTrue(summary.startswith(
            'Archive contains 2 SED-ML documents with 2 models, 2 simulations, 3 tasks, 2 reports, and 3 plots:\n'))
        self.assertGreater(summary.index('exp_2.sedml'), summary.index('exp_1.sedml'))
        self.assertGreater(summary.index('plot_5'), summary.index('plot_4'))
