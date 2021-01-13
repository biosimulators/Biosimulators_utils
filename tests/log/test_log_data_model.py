from biosimulators_utils.config import get_config
from biosimulators_utils.log import data_model
import os
import shutil
import tempfile
import unittest
import yaml


class ExecStatusDataModel(unittest.TestCase):
    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test(self):
        task_log = data_model.TaskLog(
            status=data_model.Status.FAILED,
            exception=ValueError('Big error'),
            skip_reason=NotImplementedError('Skip rationale'),
            output='Stdout/err',
            duration=10.5,
            algorithm='KISAO_0000019',
        )
        self.assertEqual(task_log.to_dict(), {
            'status': 'FAILED',
            'exception': {
                'type': 'ValueError',
                'message': 'Big error',
            },
            'skipReason': {
                'type': 'NotImplementedError',
                'message': 'Skip rationale',
            },
            'output': 'Stdout/err',
            'duration': 10.5,
            'algorithm': 'KISAO_0000019',
            'simulatorDetails': None,
        })

        task_log = data_model.TaskLog(
            status=data_model.Status.RUNNING)
        self.assertEqual(task_log.to_dict(), {
            'status': 'RUNNING',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'algorithm': None,
            'simulatorDetails': None,
        })

        report_log = data_model.ReportLog(
            status=data_model.Status.RUNNING,
            data_sets={
                'data_set_1': data_model.Status.QUEUED,
                'data_set_2': data_model.Status.SUCCEEDED,
            })
        self.assertEqual(report_log.to_dict(), {
            'status': 'RUNNING',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'dataSets': {
                'data_set_1': 'QUEUED',
                'data_set_2': 'SUCCEEDED',
            }
        })

        plot2d_log = data_model.Plot2DLog(
            status=data_model.Status.RUNNING,
            curves={
                'curve_1': data_model.Status.QUEUED,
                'curve_2': data_model.Status.SUCCEEDED,
            })
        self.assertEqual(plot2d_log.to_dict(), {
            'status': 'RUNNING',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'curves': {
                'curve_1': 'QUEUED',
                'curve_2': 'SUCCEEDED',
            }
        })

        plot3d_log = data_model.Plot3DLog(
            status=data_model.Status.RUNNING,
            surfaces={
                'surface_1': data_model.Status.QUEUED,
                'surface_2': data_model.Status.SUCCEEDED,
            })
        self.assertEqual(plot3d_log.to_dict(), {
            'status': 'RUNNING',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'surfaces': {
                'surface_1': 'QUEUED',
                'surface_2': 'SUCCEEDED',
            }
        })

        doc_log = data_model.SedDocumentLog(
            status=data_model.Status.RUNNING,
            tasks={
                'task_1': task_log,
            },
            outputs={
                'report_1': report_log,
                'plot_1': plot2d_log,
                'plot_2': plot3d_log,
            },
        )
        self.assertEqual(doc_log.to_dict(), {
            'status': 'RUNNING',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'tasks': {
                'task_1': task_log.to_dict(),
            },
            'outputs': {
                'report_1': report_log.to_dict(),
                'plot_1': plot2d_log.to_dict(),
                'plot_2': plot3d_log.to_dict(),
            },
        })

        archive_log = data_model.CombineArchiveLog(
            status=data_model.Status.RUNNING,
            sed_documents={
                'doc_1': doc_log,
            },
        )
        self.assertEqual(archive_log.to_dict(), {
            'status': 'RUNNING',
            'exception': None,
            'skipReason': None,
            'output': None,
            'duration': None,
            'sedDocuments': {
                'doc_1': doc_log.to_dict(),
            },
        })

        doc_log.parent = archive_log
        task_log.parent = doc_log
        report_log.parent = doc_log
        plot2d_log.parent = doc_log
        plot3d_log.parent = doc_log

        archive_log.out_dir = os.path.join(self.dirname, 'log')

        archive_log.export()
        doc_log.export()
        task_log.export()
        report_log.export()
        plot2d_log.export()
        plot3d_log.export()
        with open(os.path.join(archive_log.out_dir, get_config().LOG_PATH), 'r') as file:
            self.assertEqual(yaml.load(file), archive_log.to_dict())
