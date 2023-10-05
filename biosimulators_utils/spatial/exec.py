""" Exec methods for executing spatial tasks in SED-ML files in COMBINE/OMEX archives

:Author: Alexander Patrie <apatrie@uchc.edu>
:Date: 2023-09-16
:Copyright: 2023, UConn Health
:License: MIT
"""

# pragma: no cover
# import os
from typing import Optional, Tuple
from biosimulators_utils.log.data_model import CombineArchiveLog
from biosimulators_utils.report.data_model import SedDocumentResults
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.config import Config, get_config


try:
    from smoldyn.biosimulators.combine import exec_sed_doc
except ImportError:
    raise ImportError('The Smoldyn-Python package must be installed to use this feature.')


def exec_combine_archive(archive_filename: str,
                         out_dir: str,
                         config: Optional[Config] = None) -> Tuple[SedDocumentResults, CombineArchiveLog]:
    """Execute the SED tasks defined in a COMBINE/OMEX archive whose contents are spatial/spatiotemporal in nature.
        Library-level wrapper method which imports smoldyn.biosimulators.combine and
        calls `biosimulators_utils.combine.exec_sedml_docs_in_combine_archive`. Also outputs a simularium file.

        Args:
            archive_filename (:obj:`str`): path to the COMBINE/OMEX archive. Must be the zipped archive.
            out_dir (:obj:`str`): path to store the outputs of the archive (unzipped).
            config (:obj:`Config`): BioSimulators Utils common configuration. Here, you may define the `LOG` and `REPORTS`
                `_PATH`.

        Returns:
            :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    config = config or get_config()
    return exec_sedml_docs_in_archive(
        exec_sed_doc,
        archive_filename,
        out_dir,
        apply_xml_model_changes=False,
        config=config
    )


