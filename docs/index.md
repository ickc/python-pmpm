# Python manual package manager—a package manager written in Python for manually installing a compiled stack

```{toctree}
:maxdepth: 2
:numbered:
:hidden:

api/modules
changelog
```

<!-- [![Documentation Status](https://readthedocs.org/projects/souk-data-centre/badge/?version=latest)](https://souk-data-centre.readthedocs.io/en/latest/?badge=latest&style=plastic)
[![Documentation Status](https://github.com/ickc/python-pmpm/workflows/GitHub%20Pages/badge.svg)](https://ickc.github.io/souk-data-centre)

![GitHub Actions](https://github.com/ickc/python-pmpm/workflows/Python%20package/badge.svg)

[![Supported versions](https://img.shields.io/pypi/pyversions/souk-data-centre.svg)](https://pypi.org/project/souk-data-centre)
[![Supported implementations](https://img.shields.io/pypi/implementation/souk-data-centre.svg)](https://pypi.org/project/souk-data-centre)
[![PyPI Wheel](https://img.shields.io/pypi/wheel/souk-data-centre.svg)](https://pypi.org/project/souk-data-centre)
[![PyPI Package latest release](https://img.shields.io/pypi/v/souk-data-centre.svg)](https://pypi.org/project/souk-data-centre)
[![GitHub Releases](https://img.shields.io/github/tag/ickc/python-pmpm.svg?label=github+release)](https://github.com/ickc/python-pmpm/releases)
[![Development Status](https://img.shields.io/pypi/status/souk-data-centre.svg)](https://pypi.python.org/pypi/souk-data-centre/)
[![Downloads](https://img.shields.io/pypi/dm/souk-data-centre.svg)](https://pypi.python.org/pypi/souk-data-centre/)
![License](https://img.shields.io/pypi/l/souk-data-centre.svg) -->

Python manual package manager is a package manager written in Python for manually installing a compiled stack.

## Installation

```sh
pip install pmpm
```

## Development

```sh
git clone https://github.com/ickc/python-pmpm.git
cd python-pmpm
conda activate
mamba env create -f environment.yml
conda activate pmpm
pip install -e .
```

## Usage

Use one of the example config in this repository:

```sh
pmpm conda_install "$HOME/pmpm-test" --file examples/....yml
```
