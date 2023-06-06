from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple

CONDA_CHANNELS: Tuple[str, ...] = (
    "conda-forge",
    "nodefaults",
)
CONDA_DEPENDENCIES: Tuple[str, ...] = (
    "astropy",
    "automake",
    "bandit",
    "cfitsio",
    "compilers",
    "configobj",
    "cython",
    "ephem",
    "fftw",
    "flake8",
    "h5py",
    "healpy",
    "ipykernel",
    "lapack",
    "libaatm",
    "libsharp",
    "libtool",
    "make",
    "matplotlib",
    "mpi4py",
    "mpich-mpicc",
    "mpich-mpicxx",
    "mpich-mpifort",
    "mypy",
    "nbformat",
    "numba",
    "numpy",
    "plotly",
    "pydocstyle",
    "pylint",
    "pysm3",
    "pytest",
    "quaternionarray",
    "scipy",
    "sphinx",
    "sphinx_rtd_theme",
    "suitesparse",
    "toml",
    "wurlitzer",
)
DEPENDENCIES: Tuple[str, ...] = (
    "libmadam",
    "toast",
)
