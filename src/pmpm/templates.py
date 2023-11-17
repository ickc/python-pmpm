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
    "autobahn",
    "automake",
    "bandit",
    "cfitsio",
    "cmake",
    "compilers",
    "configobj",
    "coveralls",
    "cython",
    "deprecation",
    "ephem",
    "fftw=*=mpi*",
    "flake8",
    "flatbuffers",
    "h5py=*=mpi*",
    "healpy",
    "influxdb",
    "ipykernel",
    "lapack",
    "libaatm",
    "libsharp=*=mpi*",
    "libtool",
    "make",
    "matplotlib",
    "mpi4py",
    "mpich-mpicc",
    "mpich-mpicxx",
    "mpich-mpifort",
    "mypy",
    "namaster",
    "nbformat",
    "numba",
    "numpy",
    "pillow",
    "plotly",
    "pshmem",
    "py-ubjson",
    "pyaml",
    "pydocstyle",
    "pyfftw",
    "pylint",
    "pyserial",
    "pysm3",
    "pysmi",
    "pysnmp",
    "pysqlite3",
    "pytest-cov",
    "pytest",
    "python-dateutil",
    "pytz",
    "pyyaml",
    "quaternionarray",
    "scikit-image",
    "scipy",
    "setproctitle",
    "setuptools",
    "skyfield",
    "sphinx_rtd_theme",
    "sphinx",
    "sqlalchemy",
    "suitesparse",
    "toml",
    "tqdm",
    "twisted",
    "typer",
    "ujson",
    "wurlitzer",
)
DEPENDENCIES: Tuple[str, ...] = (
    "libmadam",
    "toast=toast3",
)
