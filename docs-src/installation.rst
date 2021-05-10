Installation instructions
=========================

Requirements
---------------------------------------

* Python >= 3.7
* pip


Optional requirements
---------------------------------------

* Docker: required to execute containerized simulation tools


Installing the latest release from PyPI
---------------------------------------

After installing `Python <https://www.python.org/downloads/>`_ (>= 3.7) and `pip <https://pip.pypa.io/>`_, run the following command to install BioSimulators utils:

.. code-block:: text

    pip install biosimulators-utils


Installing the latest revision from GitHub
-------------------------------------------

After installing `Python <https://www.python.org/downloads/>`_ (>= 3.7) and `pip <https://pip.pypa.io/>`_, run the following command to install BioSimulators utils:

.. code-block:: text

    pip install git+https://github.com/biosimulators/Biosimulators_utils#egg=biosimulators_utils


Installing the optional features
--------------------------------

To use BioSimulators utils to validate models encoded in NeuroML, install BioSimulators utils with the ``neuroml`` option:

.. code-block:: text

    pip install biosimulators-utils[neuroml]

To use BioSimulators utils to validate models encoded in SBML, install BioSimulators utils with the ``sbml`` option:

.. code-block:: text

    pip install biosimulators-utils[sbml]

To use BioSimulators utils to execute containerized simulation tools, install BioSimulators utils with the ``containers`` option:

.. code-block:: text

    pip install biosimulators-utils[containers]


To use BioSimulators utils to log the standard output and error produced by simulation tools, install BioSimulators utils with the ``logging`` option:

.. code-block:: text

    pip install biosimulators-utils[logging]
