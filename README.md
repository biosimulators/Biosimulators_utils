[![Latest release](https://img.shields.io/github/v/release/biosimulators/Biosimulators_utils)](https://github.com/biosimulators/Biosimulators_utils/releases)
[![PyPI](https://img.shields.io/pypi/v/biosimulators-utils)](https://pypi.org/project/biosimulators-utils/)
[![CI status](https://github.com/biosimulators/Biosimulators_utils/workflows/Continuous%20integration/badge.svg)](https://github.com/biosimulators/Biosimulators_utils/actions?query=workflow%3A%22Continuous+integration%22)
[![Test coverage](https://codecov.io/gh/biosimulators/Biosimulators_utils/branch/dev/graph/badge.svg)](https://codecov.io/gh/biosimulators/Biosimulators_utils)
[![Binder](https://mybinder.org/badge_logo.svg)](https://tutorial.biosimulators.org/)
[![All Contributors](https://img.shields.io/github/all-contributors/biosimulators/Biosimulators_utils/HEAD)](#contributors-)

# BioSimulators utils
Command-line application and high-level utilities for reading, writing, validating, and executing [COMBINE/OMEX format](https://combinearchive.org/) files that contain descriptions of simulations in [Simulation Experiment Description Markup Language](https://sed-ml.org/) (SED-ML) format with models in formats such as the [BioNetGen Language](https://bionetgen.org) (BNGL) and the [Systems Biology Markup Language](http://sbml.org) (SBML).

## Installation

### Requirements
* Python >= 3.7
* pip (latest)

### Optional requirements

* [Docker](https://www.docker.com/): required to execute containerized simulation tools
* [Java](https://www.java.com/): required to parse and validate NeuroML/LEMS files
* [Perl](https://www.perl.org/): required to parse and validate BioNetGen files
* [RBApy](https://sysbioinra.github.io/RBApy/): required to parse and validate RBA files
* [XPP](http://www.math.pitt.edu/~bard/xpp/xpp.html): required to parse and validate XPP files

### Install latest release from PyPI
```
pip install biosimulators-utils
```

### Install latest revision from GitHub
```
pip install git+https://github.com/biosimulators/Biosimulators_utils.git#biosimulators_utils
```

### Installation optional features

To use BioSimulators utils to validate BNGL models, install BioSimulators utils with the `bgnl` option:
```
pip install biosimulators-utils[bgnl]
```

To use BioSimulators utils to validate CellML models, install BioSimulators utils with the `cellml` option:
```
pip install biosimulators-utils[cellml]
```

To use BioSimulators utils to validate LEMS models, install [Java](https://www.java.com/) and then install BioSimulators utils with the `lems` option:
```
pip install biosimulators-utils[lems]
```

To use BioSimulators utils to validate NeuroML models, install BioSimulators utils with the `neuroml` option:
```
pip install biosimulators-utils[neuroml]
```

To use BioSimulators utils to validate SBML models, install BioSimulators utils with the `sbml` option:
```
pip install biosimulators-utils[sbml]
```

To use BioSimulators utils to validate SBML models, install BioSimulators utils with the `smoldyn` option:
```
pip install biosimulators-utils[smoldyn]
```

To use BioSimulators utils to convert Escher metabolic maps to Vega flux data visualizations, install BioSimulators utils with the `escher` option:
```
pip install biosimulators-utils[escher]
```

To use BioSimulators utils to execute containerized simulation tools, install BioSimulators utils with the `containers` option:
```
pip install biosimulators-utils[containers]
```

To use BioSimulators utils to log the standard output and error produced by simulation tools, install BioSimulators utils with the `logging` option:
```
pip install biosimulators-utils[logging]
```

## Dockerfile and Docker image

This package is available in the `ghcr.io/biosimulators/biosimulators` Docker image. This image includes all of the optional dependencies and installation options.

To install and run this image, run the following commands:
```
docker pull ghcr.io/biosimulators/biosimulators
docker run -it --rm ghcr.io/biosimulators/biosimulators
```

This image includes this package, as well as standardized Python APIs for the simulation tools validated by BioSimulators. Because this image aims to incorporate as many simulation tools as possible within a single Python environment, this image may sometimes lag behind the latest version of this package.

The Dockerfile for this image is available [here](https://github.com/biosimulators/Biosimulators/blob/dev/Dockerfile).

## Tutorials

### Command-line interface
A tutorial for the command-line interface is available [here](https://docs.biosimulators.org/Biosimulators_utils/).

### Python API
Interactive tutorials for using BioSimulators-utils and Python APIs for simulation tools to execute simulations are available online from Binder [here](https://tutorial.biosimulators.org/). The Jupyter notebooks for these tutorials are also available [here](https://github.com/biosimulators/Biosimulators_tutorials).

## API documentation
API documentation is available [here](https://docs.biosimulators.org/Biosimulators_utils/).

## License
This package is released under the [MIT license](LICENSE).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York and the [Center for Reproducible Biomedical Modeling](http://reproduciblebiomodels.org) with assistance from the contributors listed [here](CONTRIBUTORS.md).

## Contributing to BioSimulators utils
We enthusiastically welcome contributions to BioSimulators utils! Please see the [guide to contributing](CONTRIBUTING.md) and the [developer's code of conduct](CODE_OF_CONDUCT.md).

## Funding
This work was supported by National Institutes of Health award P41EB023912.

## Questions and comments
Please contact the [BioSimulators Team](mailto:info@biosimulators.org) with any questions or comments.
