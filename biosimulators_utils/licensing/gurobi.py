""" Tool for managing Gurobi licenses through environment variables

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-09-1
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import LicenseManager
import functools
import os

try:
    import gurobipy  # noqa: F401
except ModuleNotFoundError:
    gurobipy = None


class GurobiLicenseManager(LicenseManager):
    ENV_VAR_PREFIX = 'GRB'

    def __init__(self):
        if gurobipy is not None:
            self.__gurobipy_Model = gurobipy.Model
        else:
            self.__gurobipy_Model = None

    def get_keys_from_env_vars(self):
        """ Get the license keys for the software package from environment variables

        Returns:
            :obj:`dict`: environment license variables for a software package
        """
        keys = super(GurobiLicenseManager, self).get_keys_from_env_vars()
        license_id = keys.get('LICENSEID', None)
        if license_id is not None:
            keys['LICENSEID'] = int(float(license_id))
        return keys

    def is_package_available(self):
        """ Determine whether the package is installed

        Returns:
            :obj:`bool`: whether the package is installed
        """
        return (
            gurobipy is not None and (
                self.get_keys_from_env_vars()
                or (
                    os.path.isfile(os.path.expanduser(os.path.join('~', 'gurobi.lic')))
                    or os.path.isfile(os.path.join('/opt', 'gurobi', 'gurobi.lic'))
                )
            )
        )

    def start(self):
        """ Initialize usage of the software package with license keys """
        if self.is_package_available():
            keys = self.get_keys_from_env_vars()

            if keys:
                env = gurobipy.Env(params=keys)
                gurobipy.Model = functools.partial(self.__gurobipy_Model, env=env)  # to make OptLang use the Gurobi environment

    def end(self):
        """ Terminate usage of the software package with license keys """
        if self.is_package_available():
            gurobipy.Model = self.__gurobipy_Model
