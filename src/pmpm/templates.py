from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple

CONDA_CHANNELS: Tuple[str, ...] = (
    "conda-forge",
    "nodefaults",
)
CONDA_DEPENDENCIES: Tuple[str, ...] = (
    "ipykernel",
    "numpy",
    "scipy",
    "matplotlib",
    "ephem",
    "h5py",
    "healpy",
    "numba",
    "toml",
    "cython",
    "mypy",
    "pylint",
    "pydocstyle",
    "flake8",
    "bandit",
    "pytest",
    "plotly",
    "nbformat",
    "astropy",
    "configobj",
    "mpi4py",
    "pysm3",
    "libsharp",
    "mpich-mpicc",
    "mpich-mpicxx",
    "mpich-mpifort",
    "fftw",
    "libaatm",
    "cfitsio",
    "suitesparse",
    "automake",
    "libtool",
    "lapack",
    "compilers",
    "quaternionarray",
    "make",
    "wurlitzer",
    "sphinx",
    "sphinx_rtd_theme",
)
DEPENDENCIES: Tuple[str, ...] = (
    "libmadam",
    "toast",
)
