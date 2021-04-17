Tutorial for the command-line application
=========================================

Validate a modeling project
---------------------------

The following command can be used to validate a COMBINE/OMEX archive and get a summary of the contents of the archive. Note, BioSimulators utils must be installed with the ``sbml`` option to validate COMBINE/OMEX archives that include models encoded in the SMBL format.

.. code-block:: text

    biosimulators-utils validate /path/to/project.omex


Execute a modeling project with a standardized simulation tool from the BioSimulators registry
----------------------------------------------------------------------------------------------

The following command can be used to use a standardized simulation from the `BioSimulators registry <https://biosimulators.org>`_, such as tellurium, to execute a COMBINE/OMEX archive and save its outputs (reports and plots) to a directory. Please see the BioSimulators registry for a list of the available simulation tools. Note, this requires Docker and the installing BioSimulators utils with the ``containers`` option.

.. code-block:: text

    biosimulators-utils exec -i /path/to/project.omex -o /path/to/save/outputs ghcr.io/biosimulators/tellurium:latest


Additional documentation
------------------------

The command-line program is documented inline. To view the documentation, execute the command-line program the ``--help`` option.

.. code-block:: text

    biosimulators-utils --help
