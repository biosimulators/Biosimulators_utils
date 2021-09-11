""" Tool for managing licenses through environment variables

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-09-1
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import abc
import contextlib
import os


class LicenseManager(contextlib.AbstractContextManager):
    """ Base singleton class for managing setting up licenses for software packages from environment variables """

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(LicenseManager, cls).__new__(cls)
        return cls.__instance

    @property
    @classmethod
    @abc.abstractmethod
    def ENV_VAR_PREFIX(cls):
        """ Get the prefix for environment variables

        Returns:
            :obj:`str`: prefix for environment variables
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def is_package_available(self):
        """ Determine whether the package is installed and available

        Returns:
            :obj:`bool`: whether the package is installed and available
        """
        pass  # pragma: no cover

    def get_keys_from_env_vars(self):
        """ Get the license keys for the software package from environment variables

        Returns:
            :obj:`dict`: environment license variables for a software package
        """
        keys = {}
        for key, val in os.environ.items():
            if key.startswith(self.ENV_VAR_PREFIX + '_') and len(key) > len(self.ENV_VAR_PREFIX) + 1:
                key = key[len(self.ENV_VAR_PREFIX) + 1:]
                keys[key] = val
        return keys

    @abc.abstractmethod
    def start(self):
        """ Initialize the usage of the software package with license keys """
        pass  # pragma: no cover

    @abc.abstractmethod
    def end(self):
        """ Terminate usage of the software package with license keys """
        pass  # pragma: no cover

    def __enter__(self):
        """ Enter a context """
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """ Exit a context

        Args:
            exc_type
            exc_value
            traceback
        """
        self.end()
