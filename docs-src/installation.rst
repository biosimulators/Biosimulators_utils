Installation instructions
=========================

Requirements
---------------------------------------

* Python >= 3.7
* pip


Optional requirements
---------------------------------------

* `Docker <https://www.docker.com/>`_: required to execute containerized simulation tools
* `Java <https://www.java.com/>`_: required to parse and validate NeuroML/LEMS files
* `Perl <https://www.perl.org/>`_: required to parse and validate BioNetGen files
* `RBApy <https://sysbioinra.github.io/RBApy/>`_: required to parse and validate RBA files
* `XPP <http://www.math.pitt.edu/~bard/xpp/xpp.html>`_: required to parse and validate XPP files


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

To use BioSimulators utils to validate models encoded in BNGL, install BioSimulators utils with the ``bngl`` option:

.. code-block:: text

    pip install biosimulators-utils[bngl]

To use BioSimulators utils to validate models encoded in CellML, install BioSimulators utils with the ``cellml`` option:

.. code-block:: text

    pip install biosimulators-utils[cellml]

To use BioSimulators utils to validate models encoded in LEMS, install `Java <https://www.java.com/>`_ and then install BioSimulators utils with the ``lems`` option:

.. code-block:: text

    pip install biosimulators-utils[lems]

To use BioSimulators utils to validate models encoded in NeuroML, install BioSimulators utils with the ``neuroml`` option:

.. code-block:: text

    pip install biosimulators-utils[neuroml]

To use BioSimulators utils to validate models encoded in SBML, install BioSimulators utils with the ``sbml`` option:

.. code-block:: text

    pip install biosimulators-utils[sbml]

To use BioSimulators utils to validate models encoded in Smoldyn, install BioSimulators utils with the ``smoldyn`` option:

.. code-block:: text

    pip install biosimulators-utils[smoldyn]

To use BioSimulators utils to convert Escher metabolic maps to Vega flux data visualizations, install BioSimulators utils with the ``escher`` option:

.. code-block:: text

    pip install biosimulators-utils[escher]

To use BioSimulators utils to execute containerized simulation tools, install BioSimulators utils with the ``containers`` option:

.. code-block:: text

    pip install biosimulators-utils[containers]


To use BioSimulators utils to log the standard output and error produced by simulation tools, install BioSimulators utils with the ``logging`` option:

.. code-block:: text

    pip install biosimulators-utils[logging]


Dockerfile and Docker image
---------------------------

This package is available in the ``ghcr.io/biosimulators/biosimulators`` Docker image. This image includes all of the optional dependencies and installation options.

To install and run this image, run the following commands::

    docker pull ghcr.io/biosimulators/biosimulators
    docker run -it --rm ghcr.io/biosimulators/biosimulators


This image includes this package, as well as standardized Python APIs for the simulation tools validated by BioSimulators. Because this image aims to incorporate as many simulation tools as possible within a single Python environment, this image may sometimes lag behind the latest version of this package.

The Dockerfile for this image is available `here <https://github.com/biosimulators/Biosimulators/blob/dev/Dockerfile>`_.
