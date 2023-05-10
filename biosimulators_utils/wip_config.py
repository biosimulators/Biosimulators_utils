import enum
import os
import json
import platform
from datetime import datetime
from typing import Dict, List, Union
from kisao import AlgorithmSubstitutionPolicy  # noqa: F401
from biosimulators_utils.log.data_model import StandardOutputErrorCapturerLevel
from biosimulators_utils.omex_meta.data_model import OmexMetadataInputFormat, OmexMetadataOutputFormat, \
    OmexMetadataSchema
from biosimulators_utils.report.data_model import ReportFormat  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
import appdirs

__all__ = [
    'Config', 'get_config', 'Colors',
    'get_app_dirs', 'acceptable_report_formats',
    'acceptable_viz_formats'
]


CURRENT_PLATFORM = platform.system()
try:
    assert CURRENT_PLATFORM == "Darwin"
    DEFAULT_STDOUT_LEVEL = StandardOutputErrorCapturerLevel.python
except AssertionError as e:
    DEFAULT_STDOUT_LEVEL = StandardOutputErrorCapturerLevel.c
DEFAULT_OMEX_METADATA_INPUT_FORMAT = OmexMetadataInputFormat.rdfxml
DEFAULT_OMEX_METADATA_OUTPUT_FORMAT = OmexMetadataOutputFormat.rdfxml_abbrev
DEFAULT_OMEX_METADATA_SCHEMA = OmexMetadataSchema.biosimulations
DEFAULT_ALGORITHM_SUBSTITUTION_POLICY = AlgorithmSubstitutionPolicy.SIMILAR_VARIABLES
DEFAULT_H5_REPORTS_PATH = 'reports.h5'
DEFAULT_REPORTS_PATH = 'reports.zip'
DEFAULT_PLOTS_PATH = 'plots.zip'
DEFAULT_LOG_PATH = 'log.yml'
DEFAULT_BIOSIMULATORS_API_ENDPOINT = 'https://api.biosimulators.org/'
DEFAULT_BIOSIMULATIONS_API_ENDPOINT = 'https://api.biosimulations.org/'
DEFAULT_BIOSIMULATIONS_API_AUTH_ENDPOINT = 'https://auth.biosimulations.org/oauth/token'
DEFAULT_BIOSIMULATIONS_API_AUDIENCE = 'api.biosimulations.org'


class Config(object):
    def __init__(self,
                 OMEX_METADATA_INPUT_FORMAT=DEFAULT_OMEX_METADATA_INPUT_FORMAT,
                 OMEX_METADATA_OUTPUT_FORMAT=DEFAULT_OMEX_METADATA_OUTPUT_FORMAT,
                 OMEX_METADATA_SCHEMA=DEFAULT_OMEX_METADATA_SCHEMA,
                 VALIDATE_OMEX_MANIFESTS=True,
                 VALIDATE_SEDML=True,
                 VALIDATE_SEDML_MODELS=True,
                 VALIDATE_IMPORTED_MODEL_FILES=True,
                 VALIDATE_OMEX_METADATA=True,
                 VALIDATE_IMAGES=True,
                 VALIDATE_RESULTS=True,
                 ALGORITHM_SUBSTITUTION_POLICY=DEFAULT_ALGORITHM_SUBSTITUTION_POLICY,
                 COLLECT_COMBINE_ARCHIVE_RESULTS=False,
                 COLLECT_SED_DOCUMENT_RESULTS=False,
                 SAVE_PLOT_DATA=True,
                 REPORT_FORMATS=None,
                 VIZ_FORMATS=None,
                 H5_REPORTS_PATH=DEFAULT_H5_REPORTS_PATH,
                 REPORTS_PATH=DEFAULT_REPORTS_PATH,
                 PLOTS_PATH=DEFAULT_PLOTS_PATH,
                 BUNDLE_OUTPUTS=True,
                 KEEP_INDIVIDUAL_OUTPUTS=True,
                 LOG=True,
                 LOG_PATH=DEFAULT_LOG_PATH,
                 BIOSIMULATORS_API_ENDPOINT=DEFAULT_BIOSIMULATORS_API_ENDPOINT,
                 BIOSIMULATIONS_API_ENDPOINT=DEFAULT_BIOSIMULATIONS_API_ENDPOINT,
                 BIOSIMULATIONS_API_AUTH_ENDPOINT=DEFAULT_BIOSIMULATIONS_API_AUTH_ENDPOINT,
                 BIOSIMULATIONS_API_AUDIENCE=DEFAULT_BIOSIMULATIONS_API_AUDIENCE,
                 VERBOSE=False,
                 DEBUG=False,
                 STDOUT_LEVEL=DEFAULT_STDOUT_LEVEL,
                 **CUSTOM_SETTINGS):

        self.OMEX_METADATA_INPUT_FORMAT = OMEX_METADATA_INPUT_FORMAT
        self.OMEX_METADATA_OUTPUT_FORMAT = OMEX_METADATA_OUTPUT_FORMAT
        self.OMEX_METADATA_SCHEMA = OMEX_METADATA_SCHEMA
        self.VALIDATE_OMEX_MANIFESTS = VALIDATE_OMEX_MANIFESTS
        self.VALIDATE_SEDML = VALIDATE_SEDML
        self.VALIDATE_SEDML_MODELS = VALIDATE_SEDML_MODELS
        self.VALIDATE_IMPORTED_MODEL_FILES = VALIDATE_IMPORTED_MODEL_FILES
        self.VALIDATE_OMEX_METADATA = VALIDATE_OMEX_METADATA
        self.VALIDATE_IMAGES = VALIDATE_IMAGES
        self.VALIDATE_RESULTS = VALIDATE_RESULTS
        self.ALGORITHM_SUBSTITUTION_POLICY = ALGORITHM_SUBSTITUTION_POLICY
        self.COLLECT_COMBINE_ARCHIVE_RESULTS = COLLECT_COMBINE_ARCHIVE_RESULTS
        self.COLLECT_SED_DOCUMENT_RESULTS = COLLECT_SED_DOCUMENT_RESULTS
        self.SAVE_PLOT_DATA = SAVE_PLOT_DATA
        self.REPORT_FORMATS = [ReportFormat.csv] if not REPORT_FORMATS else REPORT_FORMATS
        self.VIZ_FORMATS = [VizFormat.pdf] if not VIZ_FORMATS else VIZ_FORMATS
        self.H5_REPORTS_PATH = H5_REPORTS_PATH
        self.REPORTS_PATH = REPORTS_PATH
        self.PLOTS_PATH = PLOTS_PATH
        self.BUNDLE_OUTPUTS = BUNDLE_OUTPUTS
        self.KEEP_INDIVIDUAL_OUTPUTS = KEEP_INDIVIDUAL_OUTPUTS
        self.LOG = LOG
        self.LOG_PATH = LOG_PATH
        self.BIOSIMULATORS_API_ENDPOINT = BIOSIMULATORS_API_ENDPOINT
        self.BIOSIMULATIONS_API_ENDPOINT = BIOSIMULATIONS_API_ENDPOINT
        self.BIOSIMULATIONS_API_AUTH_ENDPOINT = BIOSIMULATIONS_API_AUTH_ENDPOINT
        self.BIOSIMULATIONS_API_AUDIENCE = BIOSIMULATIONS_API_AUDIENCE
        self.VERBOSE = VERBOSE
        self.DEBUG = DEBUG
        self.STDOUT_LEVEL = STDOUT_LEVEL
        self.CUSTOM_SETTINGS = self.__getcustomsettings(CUSTOM_SETTINGS)
        if "EASY_LOG" in CUSTOM_SETTINGS:
            self.logger = self.easy_log()

    def __getcustomsettings(self, settings: Dict = None):
        for key in settings.keys():
            setattr(self, key, settings[key])
        return self

    def easy_log(self):
        return EasyLog(os.getcwd())


def get_config(report_format: str = None,
               viz_format: str = None,
               acceptable_report_formats: Union[List[str], ReportFormat] = ReportFormat,
               acceptable_viz_formats: Union[List[str], VizFormat] = VizFormat,
               easy_log: bool = False,
               *_default_format_settings) -> Config:
    if not _default_format_settings:  # get
        _default_format_settings = ('csv', 'pdf')  # set

    user_report_format = verify_formats(
        report_format,
        acceptable_report_formats,
        _default_format_settings[0]
    )

    user_viz_format = verify_formats(
        viz_format,
        acceptable_viz_formats,
        _default_format_settings[1]
    )

    print(user_viz_format, user_report_format)

    report_formats = os.environ.get('REPORT_FORMATS', user_report_format).strip()

    if report_formats:
        report_formats = [
            ReportFormat(f.strip().lower()) for f in report_formats.split(',')
        ]
    else:
        report_formats = []

    viz_formats = os.environ.get('VIZ_FORMATS', user_viz_format).strip()
    if viz_formats:
        viz_formats = [
            VizFormat(f.strip().lower()) for f in viz_formats.split(',')
        ]
    else:
        viz_formats = []

    return Config(
        OMEX_METADATA_INPUT_FORMAT=OmexMetadataInputFormat(os.environ.get(
            'OMEX_METADATA_INPUT_FORMAT', DEFAULT_OMEX_METADATA_INPUT_FORMAT)),
        OMEX_METADATA_OUTPUT_FORMAT=OmexMetadataOutputFormat(os.environ.get(
            'OMEX_METADATA_OUTPUT_FORMAT', DEFAULT_OMEX_METADATA_OUTPUT_FORMAT)),
        OMEX_METADATA_SCHEMA=OmexMetadataSchema(os.environ.get(
            'OMEX_METADATA_SCHEMA', DEFAULT_OMEX_METADATA_SCHEMA)),
        VALIDATE_OMEX_MANIFESTS=os.environ.get('VALIDATE_OMEX_MANIFESTS', '1').lower() in ['1', 'true'],
        VALIDATE_SEDML=os.environ.get('VALIDATE_SEDML', '1').lower() in ['1', 'true'],
        VALIDATE_SEDML_MODELS=os.environ.get('VALIDATE_SEDML_MODELS', '1').lower() in ['1', 'true'],
        VALIDATE_IMPORTED_MODEL_FILES=os.environ.get('VALIDATE_IMPORTED_MODEL_FILES', '1').lower() in ['1', 'true'],
        VALIDATE_OMEX_METADATA=os.environ.get('VALIDATE_OMEX_METADATA', '1').lower() in ['1', 'true'],
        VALIDATE_IMAGES=os.environ.get('VALIDATE_IMAGES', '1').lower() in ['1', 'true'],
        VALIDATE_RESULTS=os.environ.get('VALIDATE_RESULTS', '1').lower() in ['1', 'true'],
        ALGORITHM_SUBSTITUTION_POLICY=AlgorithmSubstitutionPolicy(os.environ.get(
            'ALGORITHM_SUBSTITUTION_POLICY', DEFAULT_ALGORITHM_SUBSTITUTION_POLICY)),
        COLLECT_COMBINE_ARCHIVE_RESULTS=os.environ.get('COLLECT_COMBINE_ARCHIVE_RESULTS', '0').lower() in ['1', 'true'],
        COLLECT_SED_DOCUMENT_RESULTS=os.environ.get('COLLECT_SED_DOCUMENT_RESULTS', '0').lower() in ['1', 'true'],
        SAVE_PLOT_DATA=os.environ.get('SAVE_PLOT_DATA', '1').lower() in ['1', 'true'],
        REPORT_FORMATS=report_formats,
        VIZ_FORMATS=viz_formats,
        H5_REPORTS_PATH=os.environ.get('H5_REPORTS_PATH', DEFAULT_H5_REPORTS_PATH),
        REPORTS_PATH=os.environ.get('REPORTS_PATH', DEFAULT_REPORTS_PATH),
        PLOTS_PATH=os.environ.get('PLOTS_PATH', DEFAULT_PLOTS_PATH),
        BUNDLE_OUTPUTS=os.environ.get('BUNDLE_OUTPUTS', '1').lower() in ['1', 'true'],
        KEEP_INDIVIDUAL_OUTPUTS=os.environ.get('KEEP_INDIVIDUAL_OUTPUTS', '1').lower() in ['1', 'true'],
        LOG=os.environ.get('LOG', '1').lower() in ['1', 'true'],
        LOG_PATH=os.environ.get('LOG_PATH', DEFAULT_LOG_PATH),
        BIOSIMULATORS_API_ENDPOINT=os.environ.get('BIOSIMULATORS_API_ENDPOINT', DEFAULT_BIOSIMULATORS_API_ENDPOINT),
        BIOSIMULATIONS_API_ENDPOINT=os.environ.get('BIOSIMULATIONS_API_ENDPOINT', DEFAULT_BIOSIMULATIONS_API_ENDPOINT),
        BIOSIMULATIONS_API_AUTH_ENDPOINT=os.environ.get('BIOSIMULATIONS_API_AUTH_ENDPOINT',
                                                        DEFAULT_BIOSIMULATIONS_API_AUTH_ENDPOINT),
        BIOSIMULATIONS_API_AUDIENCE=os.environ.get('BIOSIMULATIONS_API_AUDIENCE', DEFAULT_BIOSIMULATIONS_API_AUDIENCE),
        VERBOSE=os.environ.get('VERBOSE', '1').lower() in ['1', 'true'],
        DEBUG=os.environ.get('DEBUG', '0').lower() in ['1', 'true'],
        STDOUT_LEVEL=os.environ.get('STDOUT_LEVEL', DEFAULT_STDOUT_LEVEL),
        EASY_LOG=None if not easy_log else easy_log
    )


Colors = enum.Enum('Colors',
                   {
                       'queued': 'cyan',
                       'success': 'blue',
                       'succeeded': 'blue',
                       'running': 'green',
                       'pass': 'green',
                       'passed': 'green',
                       'failure': 'red',
                       'failed': 'red',
                       'skip': 'magenta',
                       'skipped': 'magenta',
                       'warning': 'yellow',
                       'warned': 'yellow',
                   },
                   type=str)


def get_app_dirs():
    """ Get the directories for the application

    Returns:
        :obj:`appdirs.AppDirs`: application directories
    """
    return appdirs.AppDirs("BioSimulatorsUtils", "BioSimulatorsTeam")


def acceptable_viz_formats():
    return get_acceptable_formats(VizFormat)


def acceptable_report_formats():
    return get_acceptable_formats(ReportFormat)


def get_acceptable_formats(acceptable_formats: enum.Enum):
    return [v.value for v in acceptable_formats]


def verify_formats(format_type: str, acceptable_format: enum.Enum, default: str):
    def verify_format(form_type, acceptable_form):
        acceptable_formats = get_acceptable_formats(acceptable_form)
        if form_type not in acceptable_formats:
            print(
                f'''Sorry, you must enter one of the following acceptable formats:
                    {acceptable_formats}. \nSetting to default format: {default}'''
            )
            return False
        else:
            return True

    return default if not verify_format(format_type, acceptable_format) \
        else format_type


class EasyLog:
    def __init__(self, log_dir, fresh: bool = False):
        self.working_file = __file__
        self._make_logdir(log_dir, fresh)
        self.log = {}
        self.index = list(range(len(self.log)))

    def __getsize__(self):
        return len(self.log)

    def __getnow__(self):
        return datetime.now().strftime("%d.%m.%Y..%H.%M.%S")

    def _make_logdir(self, log_dir: str, fresh_log: bool):
        make_dir = lambda: os.os.mkdir(log_dir) if not os.path.exists(log_dir) else None
        if fresh_log:
            filepaths = []
            for root, _, files in os.walk(log_dir):
                filepaths.append(os.path.join(root, f) for f in files)
            for f in filepaths:
                os.remove(f)
            os.rmdir(log_dir)
            make_dir()
        else:
            make_dir()

    def add_msg(self, message, func="none", status="none"):
        size = self.__getsize__()
        entry_number = 1 if size < 1 else size
        now = self.__getnow__()
        verify = lambda v: v != "none"
        func = func.__name__ if verify(func) else func
        status = str(status)
        entry = f"""{now} | NOTES: {message} | CALLED FROM: {self.working_file} 
                          | METHOD CALLED: {func} | STATUS: {status.upper()}"""
        self.log[entry_number] = entry
        return self.log

    def flush(self):
        for n in self.index:
            self.log.pop(n)
        return self.log

    def write(self, log_fp: str = None):
        if not log_fp:
            now = self.__getnow__()
            log_fp = f"log_{now}.json"
        with open(log_fp, "w"):
            json.dump(self.log, log_fp, indent=4)

    def flush_log(self, log_fp: str = None):
        self.write(log_fp)
        self.flush()
        return
