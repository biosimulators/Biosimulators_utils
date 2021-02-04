[![Latest release](https://img.shields.io/github/v/release/biosimulators/Biosimulators_utils)](https://github.com/biosimulators/Biosimulators_utils/releases)
[![PyPI](https://img.shields.io/pypi/v/biosimulators-utils)](https://pypi.org/project/biosimulators-utils/)
[![CI status](https://github.com/biosimulators/Biosimulators_utils/workflows/Continuous%20integration/badge.svg)](https://github.com/biosimulators/Biosimulators_utils/actions?query=workflow%3A%22Continuous+integration%22)
[![Test coverage](https://codecov.io/gh/biosimulators/Biosimulators_utils/branch/dev/graph/badge.svg)](https://codecov.io/gh/biosimulators/Biosimulators_utils)


# BioSimulators utils
Utilities for building standardized command-line interfaces for biosimulation tools that support the [Simulation Experiment Description Markup Language](https://sed-ml.org/) (SED-ML) and the [COMBINE/OMEX format](https://combinearchive.org/).

## Contents
* [Installation](#installation)
* [API documentation](#api-documentation)
* [License](#license)
* [Development team](#development-team)
* [Contributing to BioSimulators utils](#contributing-to-biosimulators-utils)
* [Acknowledgements](#acknowledgements)
* [Questions and comments](#questions-and-comments)

## Installation

### Requirements
* Python >= 3.7
* pip

### Optional requirements
* Docker: required to execute containerized simulation tools

### Install latest release from PyPI
```
pip install biosimulators-utils
```

### Install latest revision from GitHub
```
pip install git+https://github.com/biosimulators/Biosimulators_utils.git#biosimulators_utils
```

### Installation optional features

To use BioSimulators utils to execute containerized simulation tools, install BioSimulators utils with the `containers` option:
```
pip install biosimulators-utils[containers]
```

To use BioSimulators utils to log the standard output and error produced by simulation tools, install BioSimulators utils with the `logging` option:
```
pip install biosimulators-utils[logging]
```

## API documentation
API documentation is available [here](https://biosimulators.github.io/Biosimulators_utils/).

## License
This package is released under the [MIT license](LICENSE).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York and the [Center for Reproducible Biomedical Modeling](http://reproduciblebiomodels.org).

## Contributing to BioSimulators utils
We enthusiastically welcome contributions to BioSimulators utils! Please see the [guide to contributing](CONTRIBUTING.md) and the [developer's code of conduct](CODE_OF_CONDUCT.md).

## Acknowledgements
This work was supported by National Institutes of Health award P41EB023912.

## Questions and comments
Please contact the [BioSimulators Team](mailto:info@biosimulators.org) with any questions or comments.
