# Python manual package manager—a package manager written in Python for manually installing a compiled stack

```{toctree}
:maxdepth: 2
:numbered:
:hidden:

api/modules
CHANGELOG
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

## Introduction

Python manual package manager is a package manager written in Python for manually installing a compiled stack.
Before you proceed, you should know that for typical usage, `conda` (and its friends `mamba`/`micromamba`) should be enough for the purpose.
`pmpm` built on top of `conda` which also compile some Python packages locally.

Goal:

- Custom compilation of some packages, possibly for optimization such as `-march` and `-mtune` which is beyond what `conda` offers.
- Provide fast re-compile after some small local changes, suitable for development.

Approaches:

- `conda_install`: Both the conda provided stack and the compiled stack from `pmpm` are in the same prefix, this makes activating an environment seamless. It is achieved by cleanly compile an environment using the conda provided stack only, including compilers.
- `system_install`: The conda provided stack and the compiled stack from `pmpm` has a different prefix. This makes the 2 completely separate, where the compiled stack can uses the host compilers. This is useful for example when the vendor provided MPI compilers are needed. This also has more points of failure, as we can't completely control what is in the host environment. `pmpm` only serves as automation for reproducibility. But you probably need to modify how `pmpm` behaves on different host, and you probably need to install packages from the OS package manager.

Alternative approach:

- You can create a conda recipe and use `conda-build` and tweak from there for customization. The only downside probably is the time it takes to re-compile after modifications.

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

## Design

When installing from a YAML file such as those given in the `examples/` directory,
`pmpm` behaves as a superset of conda/mamba with an extra `_pmpm` key in the YAML configuration.
`pmpm` will compile packages available in `pmpm.packages` after the conda environment is created,
as defined in the YAML file.
