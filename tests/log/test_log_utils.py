from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.log import data_model
from biosimulators_utils.log import utils
from biosimulators_utils.log.warnings import StandardOutputNotLoggedWarning
from biosimulators_utils.sedml import data_model as sed_spec
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
        experiment_a_name = 'experiment_a.sedml'
        experiment_b_name = 'experiment_b.sedml'

        archive = combine_data_model.CombineArchive(contents=[
            combine_data_model.CombineArchiveContent(
                location=f'./{experiment_a_name}',
                format=combine_data_model.CombineArchiveContentFormat.SED_ML,
                master=False),
            combine_data_model.CombineArchiveContent(
                location=f'./{experiment_b_name}',
                format=combine_data_model.CombineArchiveContentFormat.SED_ML,
                master=False),
        ])

        experiment_1 = sed_spec.SedDocument()
        model_a = sed_spec.Model(id='model_A', name="Test Archive 1 Model",
                                 language=sed_spec.ModelLanguage.SBML.value, source='./model.xml')
        experiment_1.models.append(model_a)

        sim_1 = sed_spec.SteadyStateSimulation(id='sim_1', name="Simulation 1",
                                               algorithm=sed_spec.Algorithm(kisao_id='KISAO_0000019'))
        experiment_1.simulations.append(sim_1)

        task_a1 = sed_spec.Task(id='task_A1', name="Task 1", model=model_a, simulation=sim_1)
        experiment_1.tasks.append(task_a1)

        task_a2 = sed_spec.Task(id='task_A2', name="Task 2", model=model_a, simulation=sim_1)
        experiment_1.tasks.append(task_a2)

        var_at1 = sed_spec.Variable(id="var_t1", name="Variable Time", task=task_a1, symbol=sed_spec.Symbol.time)
        var_at2 = sed_spec.Variable(id="var_t2", name="Variable Time", task=task_a2, symbol=sed_spec.Symbol.time)
        var_a1_location = "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='V']"
        var_a1 = sed_spec.Variable(id="var_a1", name="Variable 1 (V)", task=task_a1, target=var_a1_location,
                                   target_namespaces={"sbml": "http://www.sbml.org/sbml/level2/version4"})
        var_a2_location = "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='P']"
        var_a2 = sed_spec.Variable(id="var_a2", name="Variable 2 (P)", task=task_a2, target=var_a2_location,
                                   target_namespaces={"sbml": "http://www.sbml.org/sbml/level2/version4"})

        data_gen_a1 = sed_spec.DataGenerator(id='data_gen_A1',
                                             name="Data Generator 1",
                                             math='param_1',
                                             parameters=[sed_spec.Parameter(id='param_1', value=1.)],
                                             variables=[var_at1, var_a1])
        experiment_1.data_generators.append(data_gen_a1)

        data_gen_a2 = sed_spec.DataGenerator(id='data_gen_A2',
                                             name="Data Generator 2",
                                             math='param_2',
                                             parameters=[sed_spec.Parameter(id='param_2', value=2.)],
                                             variables=[var_at2, var_a2])
        experiment_1.data_generators.append(data_gen_a2)

        experiment_1.outputs.append(sed_spec.Report(id='report_A1', name="Report 1", data_sets=[
            sed_spec.DataSet(id='data_set_A1', name="Data Set 1", label='data_set_1', data_generator=data_gen_a1),
            sed_spec.DataSet(id='data_set_A2', name="Data Set 2", label='data_set_2', data_generator=data_gen_a2),
        ]))

        experiment_1.outputs.append(sed_spec.Plot2D(id='plot_A2', curves=[
            sed_spec.Curve(id='curve_A1',
                           name="Curve 1",
                           x_data_generator=data_gen_a1,
                           y_data_generator=data_gen_a1,
                           x_scale=sed_spec.AxisScale.log,
                           y_scale=sed_spec.AxisScale.log),
            sed_spec.Curve(id='curve_A2',
                           name="Curve 2",
                           x_data_generator=data_gen_a2,
                           y_data_generator=data_gen_a2,
                           x_scale=sed_spec.AxisScale.log,
                           y_scale=sed_spec.AxisScale.log),
        ]))

        SedmlSimulationWriter().run(experiment_1, os.path.join(self.dirname, experiment_a_name),
                                    validate_models_with_languages=False)

        experiment_b = sed_spec.SedDocument()
        model_b = sed_spec.Model(id='model_B', language=sed_spec.ModelLanguage.SBML.value, source='./model.xml')
        experiment_b.models.append(model_b)

        sim_b = sed_spec.SteadyStateSimulation(id='sim_B', algorithm=sed_spec.Algorithm(kisao_id='KISAO_0000019'))
        experiment_b.simulations.append(sim_b)

        task_b1 = sed_spec.Task(id='task_B1', name="Task 1", model=model_b, simulation=sim_b)
        experiment_b.tasks.append(task_b1)

        task_b2 = sed_spec.Task(id='task_B2', name="Task 2", model=model_b, simulation=sim_b)
        experiment_b.tasks.append(task_b2)

        var_bt1 = sed_spec.Variable(id="var_t1", name="Variable Time", task=task_b1, symbol=sed_spec.Symbol.time)
        var_bt2 = sed_spec.Variable(id="var_t2", name="Variable Time", task=task_b2, symbol=sed_spec.Symbol.time)
        var_b1_location = "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='N']"
        var_b1 = sed_spec.Variable(id="var_b1", name="Variable 1 (N)", task=task_b1, target=var_b1_location,
                                   target_namespaces={"sbml": "http://www.sbml.org/sbml/level2/version4"})
        var_b2_location = "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='S']"
        var_b2 = sed_spec.Variable(id="var_b2", name="Variable 2 (S)", task=task_b2, target=var_b2_location,
                                   target_namespaces={"sbml": "http://www.sbml.org/sbml/level2/version4"})

        data_gen_b1 = sed_spec.DataGenerator(id='data_gen_B1',
                                             math='param_3',
                                             parameters=[sed_spec.Parameter(id='param_3', value=1.)],
                                             variables=[var_bt1, var_b1])
        data_gen_b2 = sed_spec.DataGenerator(id='data_gen_B2',
                                             math='param_4',
                                             parameters=[sed_spec.Parameter(id='param_4', value=2.)],
                                             variables=[var_bt2, var_b2])
        experiment_b.data_generators.append(data_gen_b1)
        experiment_b.data_generators.append(data_gen_b2)
        experiment_b.outputs.append(sed_spec.Report(id='report_B1'))
        experiment_b.outputs.append(sed_spec.Plot2D(id='plot_B2'))
        experiment_b.outputs.append(sed_spec.Plot3D(id='plot_B3', surfaces=[
            sed_spec.Surface(id='surface_B1',
                             x_data_generator=data_gen_b1,
                             y_data_generator=data_gen_b1,
                             z_data_generator=data_gen_b2,
                             x_scale=sed_spec.AxisScale.log,
                             y_scale=sed_spec.AxisScale.log,
                             z_scale=sed_spec.AxisScale.log),
        ]))
        SedmlSimulationWriter().run(experiment_b, os.path.join(self.dirname, experiment_b_name),
                                    validate_semantics=False,
                                    validate_models_with_languages=False)

        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.Plot2D,
                sed_spec.Plot3D,
                sed_spec.DataSet,
                sed_spec.Curve,
                sed_spec.Surface,
            ),
            supported_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.DataSet,
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
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_A1',
                            'dataSets': [
                                {
                                    'id': 'data_set_A1',
                                    'status': 'QUEUED'
                                },
                                {
                                    'id': 'data_set_A2',
                                    'status': 'QUEUED'
                                }
                            ]
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_A2',
                            'curves': [
                                {
                                    'id': 'curve_A1',
                                    'status': 'SKIPPED'
                                },
                                {
                                    'id': 'curve_A2',
                                    'status': 'SKIPPED'
                                }
                            ]
                        }
                    ]
                },
                {
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_B1',
                            'dataSets': []
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B2',
                            'curves': []
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B3',
                            'surfaces': [
                                {
                                    'id': 'surface_B1',
                                    'status': 'SKIPPED'
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        self.assertEqual(status.to_json()['sedDocuments'][1]['outputs'][1], expected['sedDocuments'][1]['outputs'][1])
        self.assertEqual(status.sed_documents[experiment_a_name].parent, status)

        self.assertEqual(status.sed_documents[experiment_a_name].tasks['task_A1'].parent,
                         status.sed_documents[experiment_a_name])
        self.assertEqual(status.sed_documents[experiment_a_name].outputs['report_A1'].parent,
                         status.sed_documents[experiment_a_name])
        self.assertTrue(experiment_a_name not in status.sed_documents[experiment_a_name].tasks)

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
                    'status': 'SKIPPED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': [
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_A1',
                            'dataSets': [
                                {
                                    'id': 'data_set_A1',
                                    'status': 'SKIPPED'
                                },
                                {
                                    'id': 'data_set_A2',
                                    'status': 'SKIPPED'
                                }
                            ]
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_A2',
                            'curves': [
                                {
                                    'id': 'curve_A1',
                                    'status': 'SKIPPED'
                                },
                                {
                                    'id': 'curve_A2',
                                    'status': 'SKIPPED'
                                }
                            ]
                        }
                    ]
                },
                {
                    'status': 'SKIPPED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': [
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_B1',
                            'dataSets': [

                            ]
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B2',
                            'curves': [

                            ]
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B3',
                            'surfaces': [
                                {
                                    'id': 'surface_B1',
                                    'status': 'SKIPPED'
                                }
                            ]
                        }
                    ]
                }
            ]
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
                    'status': 'FAILED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': [
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_A1',
                            'dataSets': [
                                {
                                    'id': 'data_set_A1',
                                    'status': 'FAILED'
                                },
                                {
                                    'id': 'data_set_A2',
                                    'status': 'FAILED'
                                }
                            ]
                        },
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_A2',
                            'curves': [
                                {
                                    'id': 'curve_A1',
                                    'status': 'FAILED'
                                },
                                {
                                    'id': 'curve_A2',
                                    'status': 'FAILED'
                                }
                            ]
                        }
                    ]
                },
                {
                    'status': 'FAILED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': [
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_B1',
                            'dataSets': [

                            ]
                        },
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B2',
                            'curves': [

                            ]
                        },
                        {
                            'status': 'FAILED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B3',
                            'surfaces': [
                                {
                                    'id': 'surface_B1',
                                    'status': 'FAILED'
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        # test logging subsets of possible features -- no data sets, curves, surfaces
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.Plot2D,
                sed_spec.Plot3D,
            ),
            supported_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.DataSet,
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
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_A1',
                            'dataSets': None
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_A2',
                            'curves': None
                        }
                    ]
                },
                {
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_B1',
                            'dataSets': None
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B2',
                            'curves': None
                        },
                        {
                            'status': 'SKIPPED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'plot_B3',
                            'surfaces': None
                        }
                    ]
                }
            ]
        })

        # test logging subsets of possible features -- no plots
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
            ),
            supported_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.DataSet,
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
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_A1',
                            'dataSets': None
                        }
                    ]
                },
                {
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'report_B1',
                            'dataSets': None
                        }
                    ]
                }
            ]
        })

        # test logging subsets of possible features -- no outputs
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
            ),
            supported_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.DataSet,
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
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_A2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': None
                },
                {
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': [
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B1',
                            'algorithm': None,
                            'simulatorDetails': None
                        },
                        {
                            'status': 'QUEUED',
                            'exception': None,
                            'skipReason': None,
                            'output': None,
                            'duration': None,
                            'id': 'task_B2',
                            'algorithm': None,
                            'simulatorDetails': None
                        }
                    ],
                    'outputs': None
                }
            ]
        })

        # test logging subsets of possible features -- no tasks or outputs
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
                sed_spec.SedDocument,
            ),
            supported_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.DataSet,
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
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_a.sedml',
                    'tasks': None,
                    'outputs': None
                },
                {
                    'status': 'QUEUED',
                    'exception': None,
                    'skipReason': None,
                    'output': None,
                    'duration': None,
                    'location': 'experiment_b.sedml',
                    'tasks': None,
                    'outputs': None
                }
            ]
        })

        # test logging subsets of possible features -- no SED documents
        status = utils.init_combine_archive_log(
            archive, self.dirname,
            logged_features=(
            ),
            supported_features=(
                sed_spec.SedDocument,
                sed_spec.Task,
                sed_spec.Report,
                sed_spec.DataSet,
            ),
        )

        self.assertEqual(status.to_json(), {
            'status': 'QUEUED',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': None
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
        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c,
                                               relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c,
                                                   relay=True) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertTrue(captured_outter.get_text().startswith('here i am'))

        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.python,
                                               relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False,
                                                   level=data_model.StandardOutputErrorCapturerLevel.python,
                                                   relay=True) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertTrue(captured_outter.get_text().startswith('here i am'))

        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c,
                                               relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.c,
                                                   relay=False) as captured_inner:
                print('here ', end='')
                sys.stdout.flush()
                print('i am', end='', file=sys.stderr)
                sys.stderr.flush()
                self.assertTrue(captured_inner.get_text().startswith('here i am'))
            self.assertEqual(captured_outter.get_text(), '')

        with utils.StandardOutputErrorCapturer(disabled=False, level=data_model.StandardOutputErrorCapturerLevel.python,
                                               relay=False) as captured_outter:
            with utils.StandardOutputErrorCapturer(disabled=False,
                                                   level=data_model.StandardOutputErrorCapturerLevel.python,
                                                   relay=False) as captured_inner:
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
