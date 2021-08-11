Tutorial for the command-line application
=========================================

Convert an Escher metabolic map to a Vega data visualization
------------------------------------------------------------

The following steps can be used to use an `Escher <https://escher.github.io/>`_ map to visualize the results of a flux balance simulation captured by a SED-ML report in a SED-ML document in a COMBINE/OMEX archive.

#. Define a SED-ML document for the simulation. The document should include a flux balance simulation and a report with a dataset for each predicted flux. The ``label`` of each dataset should be the BiGG id of the corresponding reaction. Save the SED-ML document to a file.
#. Add the SED-ML file and the model(s) involved in the file to a COMBINE archive. Add the SED-ML file and each model file to the manifest of the archive.
#. Use this package to convert an Escher map for the model to the `Vega <https://vega.github.io/vega/>`_ data visualization format. The value of the ``--data-sedml`` argument should be a combination of the location of the SED-ML file in the archive and the id of the report for the predicted fluxes.

    .. code-block:: text

        biosimulators-utils convert escher-to-vega \
            --data-sedml location/of/simulation.sedml/id_of_report \
            path/to/config-of-escher-map.json \
            path/to/save-vega.json

#. Add the Vega file to the COMBINE/OMEX archive and its manifest with the format ``http://purl.org/NET/mediatypes/application/vega+json``.

An example COMBINE/OMEX archive with an Escher map converted to Vega is available `here <https://github.com/biosimulators/Biosimulators_test_suite/tree/deploy/examples/sbml-fbc>`_.


Convert a GINML activity flow diagram to a Vega data visualization
------------------------------------------------------------------

`GINML <http://ginsim.org>`_ activity flow diagrams can similarly be used to visualize the results of logical simulations captured by SED-ML reports in SED-ML documents in COMBINE/OMEX archives.

#. Define a SED-ML document for the simulation. The document should include a logical simulation and a report with a dataset for each predicted species. The ``label`` of each dataset should be the GINsim name of the corresponding species. Save the SED-ML document to a file.
#. Add the SED-ML file and the model(s) involved in the file to a COMBINE archive. Add the SED-ML file and each model file to the manifest of the archive.
#. Use this package to convert a GINML diagram for the model to the `Vega <https://vega.github.io/vega/>`_ data visualization format. The ``--data-sedml`` argument should be set to indicate the predicted species levels should be pulled from the reports of the SED-ML files in the COMBINE/OMEX archive.

    .. code-block:: text

        biosimulators-utils convert ginml-to-vega \
            --data-sedml \
            path/to/config-of-diagram.ginml \
            path/to/save-vega.json

#. Add the Vega file to the COMBINE/OMEX archive and its manifest with the format ``http://purl.org/NET/mediatypes/application/vega+json``.

An example COMBINE/OMEX archive with a GINML diagram converted to Vega is available `here <https://github.com/biosimulators/Biosimulators_test_suite/tree/deploy/examples/sbml-qual>`_.


Convert a SBGN process description map to a Vega data visualization
-------------------------------------------------------------------

The following steps can be used to use a `Systems Biology Graphical Notation <https://sbgn.github.io/>`_ (SBGN) process description map to visualize the results of a dynamic simulation captured by a SED-ML report in a SED-ML document in a COMBINE/OMEX archive.

#. Define a SED-ML document for the simulation. The document should include a dynamic simulation (e.g., ODE, SSA) and a report with a dataset for the predicted dynamics of each glyph. The ``label`` of each dataset should be the SBGN ``label`` of the corresponding glyph. Save the SED-ML document to a file.
#. Add the SED-ML file and the model(s) involved in the file to a COMBINE archive. Add the SED-ML file and each model file to the manifest of the archive.
#. Use this package to convert a SBGN process description map for the model to the `Vega <https://vega.github.io/vega/>`_ data visualization format. The value of the ``--data-sedml`` argument should be a combination of the location of the SED-ML file in the archive and the id of the report for the predicted dynamics of the glyphs.

    .. code-block:: text

        biosimulators-utils convert sbgn-to-vega \
            --data-sedml location/of/simulation.sedml/id_of_report \
            path/to/config-of-sbgn-map.sbgn \
            path/to/save-vega.json

#. Add the Vega file to the COMBINE/OMEX archive and its manifest with the format ``http://purl.org/NET/mediatypes/application/vega+json``.

Example COMBINE/OMEX archives with SBGN maps converted to Vega are available `here <https://github.com/biosimulators/Biosimulators_test_suite/tree/deploy/examples/>`_.


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
