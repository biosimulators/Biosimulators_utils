from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.log import data_model
from biosimulators_utils.log import utils
from biosimulators_utils.log.warnings import StandardOutputNotLoggedWarning
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
import os
import shutil
import sys
import tempfile
import unittest


class ExecStatusDataModel(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_init_combine_archive_log(self):
        archive = combine_data_model.CombineArchive(contents=[
            combine_data_model.CombineArchiveContent(
                location='./exp_2.sedml',
                format=combine_data_model.CombineArchiveContentFormat.SED_ML,
                master=False),
            combine_data_model.CombineArchiveContent(
                location='./exp_1.sedml',
                format=combine_data_model.CombineArchiveContentFormat.SED_ML,
                master=False),
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
        data_gen_1 = sedml_data_model.DataGenerator(id='data_gen_1',
                                                    math='param_1',
                                                    parameters=[sedml_data_model.Parameter(id='param_1', value=1.)])
        data_gen_2 = sedml_data_model.DataGenerator(id='data_gen_2',
                                                    math='param_2',
                                                    parameters=[sedml_data_model.Parameter(id='param_2', value=2.)])
        exp_1.data_generators.append(data_gen_1)
        exp_1.data_generators.append(data_gen_2)
        exp_1.outputs.append(sedml_data_model.Report(id='report_1', data_sets=[
            sedml_data_model.DataSet(id='data_set_1', label='data_set_1', data_generator=data_gen_1),
            sedml_data_model.DataSet(id='data_set_2', label='data_set_2', data_generator=data_gen_2),
        ]))
        exp_1.outputs.append(sedml_data_model.Plot2D(id='plot_2', curves=[
            sedml_data_model.Curve(id='curve_1',
                                   x_data_generator=data_gen_1,
                                   y_data_generator=data_gen_1,
                                   x_scale=sedml_data_model.AxisScale.log,
                                   y_scale=sedml_data_model.AxisScale.log),
            sedml_data_model.Curve(id='curve_2',
                                   x_data_generator=data_gen_2,
                                   y_data_generator=data_gen_2,
                                   x_scale=sedml_data_model.AxisScale.log,
                                   y_scale=sedml_data_model.AxisScale.log),
        ]))
        SedmlSimulationWriter().run(exp_1, os.path.join(self.dirname, 'exp_1.sedml'), validate_models_with_languages=False)

        exp_2 = sedml_data_model.SedDocument()
        model_2 = sedml_data_model.Model(id='model_2', language=sedml_data_model.ModelLanguage.SBML.value, source='./model.xml')
        exp_2.models.append(model_2)
        sim_2 = sedml_data_model.SteadyStateSimulation(id='sim_2', algorithm=sedml_data_model.Algorithm(kisao_id='KISAO_0000019'))
        exp_2.simulations.append(sim_2)
        task_3 = sedml_data_model.Task(id='task_3', model=model_2, simulation=sim_2)
        exp_2.tasks.append(task_3)
        data_gen_3 = sedml_data_model.DataGenerator(id='data_gen_3',
                                                    math='param_3',
                                                    parameters=[sedml_data_model.Parameter(id='param_3', value=1.)])
        data_gen_4 = sedml_data_model.DataGenerator(id='data_gen_4',
                                                    math='param_4',
                                                    parameters=[sedml_data_model.Parameter(id='param_4', value=2.)])
        exp_2.data_generators.append(data_gen_3)
        exp_2.data_generators.append(data_gen_4)
        exp_2.outputs.append(sedml_data_model.Report(id='report_3'))
        exp_2.outputs.append(sedml_data_model.Plot2D(id='plot_4'))
        exp_2.outputs.append(sedml_data_model.Plot3D(id='plot_5', surfaces=[
            sedml_data_model.Surface(id='surface_1',
                                     x_data_generator=data_gen_3,
                                     y_data_generator=data_gen_3,
                                     z_data_generator=data_gen_4,
                                     x_scale=sedml_data_model.AxisScale.log,
                                     y_scale=sedml_data_model.AxisScale.log,
                                     z_scale=sedml_data_model.AxisScale.log),
        ]))
        SedmlSimulationWriter().run(exp_2, os.path.join(self.dirname, 'exp_2.sedml'),
                                    validate_semantics=False,
                                    validate_models_with_languages=False)

        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.Plot2D,
                sedml_data_model.Plot3D,
                sedml_data_model.DataSet,
                sedml_data_model.Curve,
                sedml_data_model.Surface,
            ),
            supported_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.DataSet,
            ),
        )
        expected = {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None, },
                    ],
                    'outputs': [
                        {'id': 'report_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': []},
                        {'id': 'plot_4', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': []},
                        {'id': 'plot_5', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'surfaces': [
                             {'id': 'surface_1', 'status': 'SKIPPED'},
                         ]},
                    ],
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                        {'id': 'task_2', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': [
                             {'id': 'data_set_1', 'status': 'QUEUED'},
                             {'id': 'data_set_2', 'status': 'QUEUED'},
                         ]},
                        {'id': 'plot_2', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': [
                             {'id': 'curve_1', 'status': 'SKIPPED'},
                             {'id': 'curve_2', 'status': 'SKIPPED'},
                         ]},
                    ],
                },
            ],
        }
        self.assertEqual(status.to_json()['sedDocuments'][1]['outputs'][1], expected['sedDocuments'][1]['outputs'][1])
        self.assertEqual(status.sed_documents['exp_1.sedml'].parent, status)
        self.assertEqual(status.sed_documents['exp_1.sedml'].tasks['task_1'].parent, status.sed_documents['exp_1.sedml'])
        self.assertEqual(status.sed_documents['exp_1.sedml'].outputs['report_1'].parent, status.sed_documents['exp_1.sedml'])

        status = utils.init_combine_archive_log(archive, self.dirname)
        for doc in status.sed_documents.values():
            doc.status = data_model.Status.QUEUED
            for task in doc.tasks.values():
                task.status = data_model.Status.QUEUED
            for output in doc.outputs.values():
                output.status = data_model.Status.QUEUED
                if isinstance(output, data_model.ReportLog):
                    els = output.data_sets
                elif isinstance(output, data_model.Plot2DLog):
                    els = output.curves
                elif isinstance(output, data_model.Plot3DLog):
                    els = output.surfaces
                else:
                    raise ValueError(output.__class__)
                for id in els.keys():
                    els[id] = data_model.Status.QUEUED
        status.finalize()
        self.assertEqual(status.to_json(), {
            'status': 'SKIPPED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'SKIPPED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_3', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_3', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': []},
                        {'id': 'plot_4', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': []},
                        {'id': 'plot_5', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'surfaces': [
                             {'id': 'surface_1', 'status': 'SKIPPED'},
                         ]},
                    ],
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'SKIPPED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_1', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                        {'id': 'task_2', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_1', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': [
                             {'id': 'data_set_1', 'status': 'SKIPPED'},
                             {'id': 'data_set_2', 'status': 'SKIPPED'},
                         ]},
                        {'id': 'plot_2', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': [
                             {'id': 'curve_1', 'status': 'SKIPPED'},
                             {'id': 'curve_2', 'status': 'SKIPPED'},
                         ]},
                    ],
                },
            ],
        })

        status = utils.init_combine_archive_log(archive, self.dirname)
        status.status = data_model.Status.RUNNING
        for doc in status.sed_documents.values():
            doc.status = data_model.Status.RUNNING
            for task in doc.tasks.values():
                task.status = data_model.Status.RUNNING
            for output in doc.outputs.values():
                output.status = data_model.Status.RUNNING
                if isinstance(output, data_model.ReportLog):
                    els = output.data_sets
                elif isinstance(output, data_model.Plot2DLog):
                    els = output.curves
                elif isinstance(output, data_model.Plot3DLog):
                    els = output.surfaces
                else:
                    raise ValueError(output.__class__)
                for id in els.keys():
                    els[id] = data_model.Status.RUNNING
        status.finalize()
        self.assertEqual(status.to_json(), {
            'status': 'FAILED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'FAILED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_3', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_3', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': []},
                        {'id': 'plot_4', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': []},
                        {'id': 'plot_5', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'surfaces': [
                             {'id': 'surface_1', 'status': 'FAILED'},
                         ]},
                    ],
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'FAILED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_1', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                        {'id': 'task_2', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_1', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': [
                             {'id': 'data_set_1', 'status': 'FAILED'},
                             {'id': 'data_set_2', 'status': 'FAILED'},
                         ]},
                        {'id': 'plot_2', 'status': 'FAILED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': [
                             {'id': 'curve_1', 'status': 'FAILED'},
                             {'id': 'curve_2', 'status': 'FAILED'},
                         ]},
                    ],
                },
            ],
        })

        # test logging subsets of possible features -- no data sets, curves, surfaces
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.Plot2D,
                sedml_data_model.Plot3D,
            ),
            supported_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.DataSet,
            ),
        )
        self.assertEqual(status.to_json(), {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None, },
                    ],
                    'outputs': [
                        {'id': 'report_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': None},
                        {'id': 'plot_4', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': None},
                        {'id': 'plot_5', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'surfaces': None},
                    ],
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                        {'id': 'task_2', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': None},
                        {'id': 'plot_2', 'status': 'SKIPPED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'curves': None},
                    ],
                },
            ],
        })

        # test logging subsets of possible features -- no plots
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
            ),
            supported_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.DataSet,
            ),
        )
        self.assertEqual(status.to_json(), {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None, },
                    ],
                    'outputs': [
                        {'id': 'report_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': None},
                    ],
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                        {'id': 'task_2', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': [
                        {'id': 'report_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'dataSets': None},
                    ],
                },
            ],
        })

        # test logging subsets of possible features -- no outputs
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
            ),
            supported_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.DataSet,
            ),
        )
        self.assertEqual(status.to_json(), {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_3', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None, },
                    ],
                    'outputs': None,
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': [
                        {'id': 'task_1', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                        {'id': 'task_2', 'status': 'QUEUED', 'exception': None, 'skipReason': None, 'output': None, 'duration': None,
                         'algorithm': None, 'simulatorDetails': None},
                    ],
                    'outputs': None,
                },
            ],
        })

        # test logging subsets of possible features -- no tasks or outputs
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sedml_data_model.SedDocument,
            ),
            supported_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.DataSet,
            ),
        )
        self.assertEqual(status.to_json(), {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': [
                {
                    'location': 'exp_2.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': None,
                    'outputs': None,
                },
                {
                    'location': 'exp_1.sedml',
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'tasks': None,
                    'outputs': None,
                },
            ],
        })

        # test logging subsets of possible features -- no SED documents
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
            ),
            supported_features=(
                sedml_data_model.SedDocument,
                sedml_data_model.Task,
                sedml_data_model.Report,
                sedml_data_model.DataSet,
            ),
        )
        self.assertEqual(status.to_json(), {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': None,
        })

    def test_get_summary_combine_archive_log_tasks_outputs_unknown_status(self):
        log = data_model.CombineArchiveLog(
            sed_documents={
                'doc_1': data_model.SedDocumentLog(
                    tasks={
                        'task_1': None,
                    },
                    outputs={
                        'output_1': None,
                    },
                ),
            }
        )
        summary = utils.get_summary_combine_archive_log(log)
        self.assertIn('Unknown: 1', summary)


class StandardOutputErrorCapturerTestCase(unittest.TestCase):
    def test(self):
        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c, relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c, relay=True) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertTrue(captured_outter.get_text().startswith('here i am'))

        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.python, relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.python, relay=True) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertTrue(captured_outter.get_text().startswith('here i am'))

        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c, relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c, relay=False) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertEqual(captured_outter.get_text(), '')

        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.python, relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.python, relay=False) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()                
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertEqual(captured_outter.get_text(), '')

        with self.assertWarns(StandardOutputNotLoggedWarning):
            with utils.StandardOutputErrorCapturer(disabled=True) as captured:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertEqual(captured.get_text(), None)
