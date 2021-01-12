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
        'CombineArchiveExecutionStatus'
        'SedDocumentExecutionStatus'

        task_status = data_model.TaskExecutionStatus(
            status=data_model.ExecutionStatus.RUNNING)
        self.assertEqual(task_status.to_dict(), {
            'status': 'RUNNING',
        })

        report_status = data_model.ReportExecutionStatus(
            status=data_model.ExecutionStatus.RUNNING,
            data_sets={
                'data_set_1': data_model.ExecutionStatus.QUEUED,
                'data_set_2': data_model.ExecutionStatus.SUCCEEDED,
            })
        self.assertEqual(report_status.to_dict(), {
            'status': 'RUNNING',
            'dataSets': {
                'data_set_1': 'QUEUED',
                'data_set_2': 'SUCCEEDED',
            }
        })

        plot2d_status = data_model.Plot2DExecutionStatus(
            status=data_model.ExecutionStatus.RUNNING,
            curves={
                'curve_1': data_model.ExecutionStatus.QUEUED,
                'curve_2': data_model.ExecutionStatus.SUCCEEDED,
            })
        self.assertEqual(plot2d_status.to_dict(), {
            'status': 'RUNNING',
            'curves': {
                'curve_1': 'QUEUED',
                'curve_2': 'SUCCEEDED',
            }
        })

        plot3d_status = data_model.Plot3DExecutionStatus(
            status=data_model.ExecutionStatus.RUNNING,
            surfaces={
                'surface_1': data_model.ExecutionStatus.QUEUED,
                'surface_2': data_model.ExecutionStatus.SUCCEEDED,
            })
        self.assertEqual(plot3d_status.to_dict(), {
            'status': 'RUNNING',
            'surfaces': {
                'surface_1': 'QUEUED',
                'surface_2': 'SUCCEEDED',
            }
        })

        doc_status = data_model.SedDocumentExecutionStatus(
            status=data_model.ExecutionStatus.RUNNING,
            tasks={
                'task_1': task_status,
            },
            outputs={
                'report_1': report_status,
                'plot_1': plot2d_status,
                'plot_2': plot3d_status,
            },
        )
        self.assertEqual(doc_status.to_dict(), {
            'status': 'RUNNING',
            'tasks': {
                'task_1': task_status.to_dict(),
            },
            'outputs': {
                'report_1': report_status.to_dict(),
                'plot_1': plot2d_status.to_dict(),
                'plot_2': plot3d_status.to_dict(),
            }
        })

        archive_status = data_model.CombineArchiveExecutionStatus(
            status=data_model.ExecutionStatus.RUNNING,
            sed_documents={
                'doc_1': doc_status,
            },
        )
        self.assertEqual(archive_status.to_dict(), {
            'status': 'RUNNING',
            'sedDocuments': {
                'doc_1': doc_status.to_dict(),
            },
        })

        doc_status.combine_archive_status = archive_status
        task_status.document_status = doc_status
        report_status.document_status = doc_status
        plot2d_status.document_status = doc_status
        plot3d_status.document_status = doc_status

        archive_status.out_dir = self.dirname

        archive_status.export()
        doc_status.export()
        task_status.export()
        report_status.export()
        plot2d_status.export()
        plot3d_status.export()
        with open(os.path.join(self.dirname, get_config().LOG_PATH), 'r') as file:
            self.assertEqual(yaml.load(file), archive_status.to_dict())
