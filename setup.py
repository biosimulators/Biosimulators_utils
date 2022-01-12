import re
import setuptools
import subprocess
import sys
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "pkg_utils"],
        check=True, capture_output=True)
    match = re.search(r'\nVersion: (.*?)\n', result.stdout.decode(), re.DOTALL)
    assert match and tuple(match.group(1).split('.')) >= ('0', '0', '5')
except (subprocess.CalledProcessError, AssertionError):
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "pkg_utils"],
        check=True)
import os
import pkg_utils

name = 'biosimulators_utils'
dirname = os.path.dirname(__file__)
package_data = {
    name: [
        os.path.join('utils', 'identifiers_org.json'),
        os.path.join('model_lang', 'cellml', '*.rng'),
        os.path.join('viz', 'vega', '**', '*.json'),
    ],
}

# get package metadata
md = pkg_utils.get_package_metadata(dirname, name, package_data_filename_patterns=package_data)
with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as file:
    long_description = file.read()

# install package
setuptools.setup(
    name=name,
    version=md.version,
    description=(
        "Command-line program and library for reading, writing, validating "
        "and executing modeling projects (COMBINE/OMEX archives with SED-ML files)."
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/biosimulators/Biosimulators_utils",
    download_url='https://github.com/biosimulators/Biosimulators_utils',
    author='Center for Reproducible Biomedical Modeling',
    author_email="info@biosimulators.org",
    license="MIT",
    keywords='systems biology modeling simulation',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    package_data=md.package_data,
    install_requires=md.install_requires,
    extras_require=md.extras_require,
    tests_require=md.tests_require,
    dependency_links=md.dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    entry_points={
        'console_scripts': [
            'biosimulators-utils = biosimulators_utils.__main__:main',
        ],
    },
)
