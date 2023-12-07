"""Generates different variants of YAML environments.

Examples:

- mkl vs. nomkl
- mpich vs. openmpi vs. nompi
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path

import defopt
import yaml
import yamlloader

from .util import split_conda_dep_from_pip

logger = getLogger("pmpm")


def main(
    path: Path,
    *,
    output: Path,
    mkl: bool = False,
) -> None:
    """Generate the environment variants.

    This is not supposed to be general-purposed, but designed only for the examples in this package.

    Args:
        path: Path to the YAML file.
        mkl: Whether to generate the MKL variant.
    """
    with path.open() as f:
        env = yaml.load(f, Loader=yamlloader.ordereddict.CSafeLoader)
    conda_dependencies, pip_dependencies = split_conda_dep_from_pip(env["dependencies"])
    if mkl:
        conda_dependencies += [
            "mkl",
            "libblas=*=*mkl",
            "liblapack=*=*mkl",
        ]
    else:
        conda_dependencies += [
            "nomkl",
            "libblas=*=*openblas",
            "liblapack=*=*openblas",
        ]
    conda_dependencies.sort()
    env["dependencies"] = conda_dependencies + [{"pip": pip_dependencies}] if pip_dependencies else conda_dependencies
    with output.open("w") as f:
        yaml.dump(env, f, Dumper=yamlloader.ordereddict.CSafeDumper)


def cli() -> None:
    """Command line interface for pmpm."""
    defopt.run(
        main,
        show_types=True,
    )


if __name__ == "__main__":
    cli()
