from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.log import data_model
from biosimulators_utils.log import utils
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
import os
import shutil
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
        model_1 = sedml_data_model.Model(id='model_1', source='./model.xml')
        exp_1.models.append(model_1)
        sim_1 = sedml_data_model.SteadyStateSimulation(id='sim_1')
        exp_1.simulations.append(sim_1)
        task_1 = sedml_data_model.Task(id='task_1', model=model_1, simulation=sim_1)
        task_2 = sedml_data_model.Task(id='task_2', model=model_1, simulation=sim_1)
        exp_1.tasks.append(task_1)
        exp_1.tasks.append(task_2)
        data_gen_1 = sedml_data_model.DataGenerator(id='data_gen_1',
                                                    math='param_1',
                                                    parameters=[sedml_data_model.DataGeneratorParameter(id='param_1', value=1.)])
        data_gen_2 = sedml_data_model.DataGenerator(id='data_gen_2',
                                                    math='param_2',
                                                    parameters=[sedml_data_model.DataGeneratorParameter(id='param_2', value=2.)])
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
        SedmlSimulationWriter().run(exp_1, os.path.join(self.dirname, 'exp_1.sedml'))

        exp_2 = sedml_data_model.SedDocument()
        model_2 = sedml_data_model.Model(id='model_2', source='./model.xml')
        exp_2.models.append(model_2)
        sim_2 = sedml_data_model.SteadyStateSimulation(id='sim_2')
        exp_2.simulations.append(sim_2)
        task_3 = sedml_data_model.Task(id='task_3', model=model_2, simulation=sim_2)
        exp_2.tasks.append(task_3)
        data_gen_3 = sedml_data_model.DataGenerator(id='data_gen_3',
                                                    math='param_3',
                                                    parameters=[sedml_data_model.DataGeneratorParameter(id='param_3', value=1.)])
        data_gen_4 = sedml_data_model.DataGenerator(id='data_gen_4',
                                                    math='param_4',
                                                    parameters=[sedml_data_model.DataGeneratorParameter(id='param_4', value=2.)])
        exp_2.data_generators.append(data_gen_3)
        exp_2.data_generators.append(data_gen_4)
        exp_2.outputs.append(sedml_data_model.Report(id='report_3'))
        exp_2.outputs.append(sedml_data_model.Plot3D(id='plot_5', surfaces=[
            sedml_data_model.Surface(id='surface_1',
                                     x_data_generator=data_gen_3,
                                     y_data_generator=data_gen_3,
                                     z_data_generator=data_gen_4,
                                     x_scale=sedml_data_model.AxisScale.log,
                                     y_scale=sedml_data_model.AxisScale.log,
                                     z_scale=sedml_data_model.AxisScale.log),
        ]))
        exp_2.outputs.append(sedml_data_model.Plot2D(id='plot_4'))
        SedmlSimulationWriter().run(exp_2, os.path.join(self.dirname, 'exp_2.sedml'))

        status = utils.init_combine_archive_log(archive, self.dirname)
        self.assertEqual(status.to_dict(), {
            'status': 'QUEUED',
            'sedDocuments': {
                'exp_1.sedml': {
                    'status': 'QUEUED',
                    'tasks': {
                        'task_1': {'status': 'QUEUED'},
                        'task_2': {'status': 'QUEUED'},
                    },
                    'outputs': {
                        'report_1': {'status': 'QUEUED', 'dataSets': {
                            'data_set_1': 'QUEUED',
                            'data_set_2': 'QUEUED',
                        }},
                        'plot_2': {'status': 'SKIPPED', 'curves': {
                            'curve_1': 'SKIPPED',
                            'curve_2': 'SKIPPED',
                        }},
                    },
                },
                'exp_2.sedml': {
                    'status': 'QUEUED',
                    'tasks': {
                        'task_3': {'status': 'QUEUED'},
                    },
                    'outputs': {
                        'report_3': {'status': 'QUEUED', 'dataSets': {}},
                        'plot_4': {'status': 'SKIPPED', 'curves': {}},
                        'plot_5': {'status': 'SKIPPED', 'surfaces': {
                            'surface_1': 'SKIPPED',
                        }},
                    },
                },
            },
        })
        self.assertEqual(status.sed_documents['exp_1.sedml'].combine_archive_status, status)
        self.assertEqual(status.sed_documents['exp_1.sedml'].tasks['task_1'].document_status, status.sed_documents['exp_1.sedml'])
        self.assertEqual(status.sed_documents['exp_1.sedml'].outputs['report_1'].document_status, status.sed_documents['exp_1.sedml'])

        status = utils.init_combine_archive_log(archive, self.dirname)
        for doc in status.sed_documents.values():
            doc.status = data_model.ExecutionStatus.QUEUED
            for task in doc.tasks.values():
                task.status = data_model.ExecutionStatus.QUEUED
            for output in doc.outputs.values():
                output.status = data_model.ExecutionStatus.QUEUED
                if isinstance(output, data_model.ReportExecutionStatus):
                    els = output.data_sets
                elif isinstance(output, data_model.Plot2DExecutionStatus):
                    els = output.curves
                elif isinstance(output, data_model.Plot3DExecutionStatus):
                    els = output.surfaces
                else:
                    raise ValueError(output.__class__)
                for id in els.keys():
                    els[id] = data_model.ExecutionStatus.QUEUED
        status.finalize()
        self.assertEqual(status.to_dict(), {
            'status': 'SKIPPED',
            'sedDocuments': {
                'exp_1.sedml': {
                    'status': 'SKIPPED',
                    'tasks': {
                        'task_1': {'status': 'SKIPPED'},
                        'task_2': {'status': 'SKIPPED'},
                    },
                    'outputs': {
                        'report_1': {'status': 'SKIPPED', 'dataSets': {
                            'data_set_1': 'SKIPPED',
                            'data_set_2': 'SKIPPED',
                        }},
                        'plot_2': {'status': 'SKIPPED', 'curves': {
                            'curve_1': 'SKIPPED',
                            'curve_2': 'SKIPPED',
                        }},
                    },
                },
                'exp_2.sedml': {
                    'status': 'SKIPPED',
                    'tasks': {
                        'task_3': {'status': 'SKIPPED'},
                    },
                    'outputs': {
                        'report_3': {'status': 'SKIPPED', 'dataSets': {}},
                        'plot_4': {'status': 'SKIPPED', 'curves': {}},
                        'plot_5': {'status': 'SKIPPED', 'surfaces': {
                            'surface_1': 'SKIPPED',
                        }},
                    },
                },
            },
        })

        status = utils.init_combine_archive_log(archive, self.dirname)
        status.status = data_model.ExecutionStatus.RUNNING
        for doc in status.sed_documents.values():
            doc.status = data_model.ExecutionStatus.RUNNING
            for task in doc.tasks.values():
                task.status = data_model.ExecutionStatus.RUNNING
            for output in doc.outputs.values():
                output.status = data_model.ExecutionStatus.RUNNING
                if isinstance(output, data_model.ReportExecutionStatus):
                    els = output.data_sets
                elif isinstance(output, data_model.Plot2DExecutionStatus):
                    els = output.curves
                elif isinstance(output, data_model.Plot3DExecutionStatus):
                    els = output.surfaces
                else:
                    raise ValueError(output.__class__)
                for id in els.keys():
                    els[id] = data_model.ExecutionStatus.RUNNING
        status.finalize()
        self.assertEqual(status.to_dict(), {
            'status': 'FAILED',
            'sedDocuments': {
                'exp_1.sedml': {
                    'status': 'FAILED',
                    'tasks': {
                        'task_1': {'status': 'FAILED'},
                        'task_2': {'status': 'FAILED'},
                    },
                    'outputs': {
                        'report_1': {'status': 'FAILED', 'dataSets': {
                            'data_set_1': 'FAILED',
                            'data_set_2': 'FAILED',
                        }},
                        'plot_2': {'status': 'FAILED', 'curves': {
                            'curve_1': 'FAILED',
                            'curve_2': 'FAILED',
                        }},
                    },
                },
                'exp_2.sedml': {
                    'status': 'FAILED',
                    'tasks': {
                        'task_3': {'status': 'FAILED'},
                    },
                    'outputs': {
                        'report_3': {'status': 'FAILED', 'dataSets': {}},
                        'plot_4': {'status': 'FAILED', 'curves': {}},
                        'plot_5': {'status': 'FAILED', 'surfaces': {
                            'surface_1': 'FAILED',
                        }},
                    },
                },
            },
        })
