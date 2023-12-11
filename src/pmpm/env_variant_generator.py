"""Generates different variants of YAML environments.

Examples:

- mkl vs. nomkl
- mpich vs. openmpi vs. nompi
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Literal

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
    mpi: Literal["nompi", "mpich", "openmpi"] = "nompi",
    os: Literal["linux", "macos"] = "linux",
) -> None:
    """Generate the environment variants.

    This is not supposed to be general-purposed, but designed only for the examples in this package.

    Args:
        path: Path to the YAML file.
        output: Path to the output YAML file.
        mkl: Whether to generate the MKL variant.
        mpi: MPI implementation to use.
        os: Operating system the environment is for.
    """
    with path.open() as f:
        env = yaml.load(f, Loader=yamlloader.ordereddict.CSafeLoader)
    conda_dependencies, pip_dependencies = split_conda_dep_from_pip(env["dependencies"])
    # mkl
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
    # remove libmadam from known incompatibilities
    if mpi == "nompi" or (os == "macos" and mpi == "openmpi"):
        env["_pmpm"]["dependencies"] = [pkg for pkg in env["_pmpm"]["dependencies"] if pkg != "libmadam"]
    # mpi
    pkgs = ("fftw", "h5py", "libsharp")
    if mpi == "nompi":
        for pkg in pkgs:
            conda_dependencies.append(f"{pkg}=*=nompi_*")
    else:
        for pkg in pkgs:
            conda_dependencies.append(f"{pkg}=*=mpi_{mpi}_*")
        conda_dependencies += [
            mpi,
            "mpi4py",
            f"{mpi}-mpicc",
            f"{mpi}-mpicxx",
            f"{mpi}-mpifort",
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
