from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from functools import cached_property
from importlib import import_module
from logging import getLogger
from pathlib import Path
from subprocess import list2cmdline
from typing import TYPE_CHECKING, ClassVar, Iterable, List, Optional, Tuple

import defopt
import psutil

from .templates import CONDA_CHANNELS, CONDA_DEPENDENCIES, DEPENDENCIES

if TYPE_CHECKING:
    from typing import Any, Dict, Union

logger = getLogger("pmpm")


def is_intel() -> bool:
    from cpuinfo import get_cpu_info

    _is_intel = get_cpu_info()["vendor_id_raw"] == "GenuineIntel"
    logger.info("Determined if the CPU is Intel: %s", _is_intel)
    return _is_intel


def prepend_path(environ: Dict[str, str], path: str):
    """Prepend to PATH in environment dictionary in-place."""
    if "PATH" in environ:
        environ["PATH"] = path + os.pathsep + environ["PATH"]
    else:
        environ["PATH"] = path


def append_path(environ: Dict[str, str], path: str):
    """Append to PATH in environment dictionary in-place."""
    if "PATH" in environ:
        environ["PATH"] += os.pathsep + path
    else:
        environ["PATH"] = path


def append_env(dependencies: List[str], package: str):
    """Append a package to conda environment definition."""
    if package not in dependencies:
        dependencies.append(package)


def check_file(path: Path, msg: str):
    if path.is_file():
        logger.info(msg, path)
    else:
        raise RuntimeError(f"{path} not found.")


def check_dir(path: Path, msg: str):
    if path.is_dir():
        logger.info(msg, path)
    else:
        raise RuntimeError(f"{path} not found.")


@dataclass
class InstallEnvironment:
    """A Generic install environment.

    :param prefix: the prefix path of the environment.
    :conda_channels: conda channels for packages to be searched in.
    :param conda_dependencies: dependencies install via conda.
    :param dependencies: dependencies install via pmpm.
    :param python_version: Python version to be installed.
    :param conda_prefix_name: the subdirectory within `prefix` for conda.
    :param compile_prefix_name: the subdirectory within `prefix` for compiled packages from `dependencies`.
    :param download_prefix_name: the subdirectory within `prefix` for downloaded source codes from `dependencies`.
    :param conda: executable name for conda solver, can be mamba, conda.
    :param sub_platform: such as ubuntu, arch, macports, homebrew, etc.
    :param skip_test: skip test if specified.
    :param skip_conda: skip installing/updating conda.
    :param fast_update: assume minimal change to source of compiled package and perform fast update.
    :param nomkl: if nomkl is used in conda packages, nomkl should be True for non-Intel CPUs.
    :param update: if updating all packages.
    :param arch: -march for compilation, for example, native or x86-64-v3
    :param tune: -mtune for compilation, for example, native or generic
    """

    prefix: Path
    conda_channels: List[str] = field(default_factory=lambda: list(CONDA_CHANNELS))
    conda_dependencies: List[str] = field(default_factory=lambda: list(CONDA_DEPENDENCIES))
    dependencies: List[str] = field(default_factory=lambda: list(DEPENDENCIES))
    python_version: str = "3.10"
    conda_prefix_name: str = "conda"
    compile_prefix_name: str = "compile"
    download_prefix_name: str = "git"
    conda: str = "mamba"
    sub_platform: str = ""
    skip_test: bool = False
    skip_conda: bool = False
    fast_update: bool = False
    # TODO: defopt can't pass False here
    nomkl: Optional[bool] = None
    update: Optional[bool] = None
    # see doc for march: https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html
    # for example, native or x86-64-v3
    arch: str = "x86-64-v3"
    # for example, native or generic
    tune: str = "generic"
    conda_environment_filename: ClassVar[str] = "environment.yml"
    supported_systems: ClassVar[Iterable[str]] = ("Linux", "Darwin", "Windows")
    system: ClassVar[str] = platform.system()
    windows_exclude_conda_dependencies: ClassVar[Iterable[str]] = {
        "automake",
        "libaatm",
        "mpich-mpicc",
        "libsharp",
        "healpy",
        "libtool",
        "mpich-mpicxx",
        "mpich-mpifort",
        "suitesparse",
        "pysm3",
        "fftw",
        "cfitsio",
        "lapack",
        "matplotlib",
    }
    windows_exclude_dependencies: ClassVar[Iterable[str]] = ("libmadam",)
    cpu_count: ClassVar[int] = psutil.cpu_count(logical=False)

    def __post_init__(self):
        if self.system not in self.supported_systems:
            raise OSError(f"OS {self.system} not supported.")
        elif self.is_windows:
            if "matplotlib" in self.conda_dependencies:
                self.conda_dependencies.append("matplotlib-base")
            self.conda_dependencies = [
                dep for dep in self.conda_dependencies if dep not in self.windows_exclude_conda_dependencies
            ]
            dependencies = []
            for dep in self.dependencies:
                if dep.split("=")[0] not in self.windows_exclude_dependencies:
                    dependencies.append(dep)
            self.dependencies = dependencies
            logger.warning(
                "Windows support is experimental and may not work. Only the following dependencies are installed: Conda: %s; others: %s",
                self.conda_dependencies,
                self.dependencies,
            )

        if self.nomkl is None:
            try:
                self.nomkl = False if is_intel() else True
            except ImportError:
                raise RuntimeError(
                    "Cannot determine if CPU is Intel. Consider running pip/conda/mamba install py-cpuinfo."
                )
            except Exception as e:
                logger.critical("Cannot determine nomkl automatically. Try specifying nomkl explicitly.")
                raise e
        self.nomkl: bool

        append_env(self.conda_dependencies, f"python={self.python_version}")
        if self.nomkl:
            append_env(self.conda_dependencies, "nomkl")

    @property
    def name(self) -> str:
        return self.prefix.name

    @cached_property
    def dependencies_versioned(self) -> dict[str, Optional[str]]:
        """Return a dictionary of dependencies with version."""
        res = {}
        for dep in self.dependencies:
            temp = dep.split("=")
            if len(temp) == 1:
                res[temp[0]] = None
            elif len(temp) == 2:
                res[temp[0]] = temp[1]
            else:
                raise RuntimeError(f"Invalid dependency {dep}")
        return res

    @property
    def to_dict(self) -> Dict[str, Union[str, List[str], Dict[str, Any]]]:
        return {
            "name": self.name,
            "channels": self.conda_channels,
            "dependencies": self.conda_dependencies,
            "prefix": str(self.prefix),
            "_pmpm": {
                "dependencies": self.dependencies,
                "python_version": self.python_version,
                "conda_prefix_name": self.conda_prefix_name,
                "compile_prefix_name": self.compile_prefix_name,
                "download_prefix_name": self.download_prefix_name,
                "conda": self.conda,
                "sub_platform": self.sub_platform,
                "skip_test": self.skip_test,
                "skip_conda": self.skip_conda,
                "fast_update": self.fast_update,
                "nomkl": self.nomkl,
                "update": self.update,
                "arch": self.arch,
                "tune": self.tune,
            },
        }

    def write_dict(self):
        logger.info("Writing environment definition to %s", self.conda_environment_path)
        conda_environment_path = self.conda_environment_path
        conda_environment_path.parent.mkdir(parents=True, exist_ok=True)
        with conda_environment_path.open("w") as f:
            json.dump(
                self.to_dict,
                f,
                indent=2,
                sort_keys=True,
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, List[str], Dict[str, Any]]]):
        pmpm: Dict[str, Any] = data["_pmpm"]
        return cls(
            Path(pmpm["prefix"]),
            conda_channels=data["channels"],
            conda_dependencies=data["dependencies"],
            dependencies=pmpm["dependencies"],
            python_version=str(pmpm["python_version"]),
            conda_prefix_name=pmpm["conda_prefix_name"],
            compile_prefix_name=pmpm["compile_prefix_name"],
            download_prefix_name=pmpm["download_prefix_name"],
            conda=pmpm["conda"],
            sub_platform=pmpm["sub_platform"],
            skip_test=pmpm["skip_test"],
            skip_conda=pmpm["skip_conda"],
            fast_update=pmpm["fast_update"],
            nomkl=pmpm["nomkl"],
            update=pmpm["update"],
        )

    @classmethod
    def read_dict(cls, input: Path):
        """"""
        with open(input, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @cached_property
    def conda_environment_path(self) -> Path:
        """Path to the JSON file of the environment definition."""
        return self.prefix / self.conda_environment_filename

    @cached_property
    def is_linux(self) -> bool:
        return self.system == "Linux"

    @cached_property
    def is_darwin(self) -> bool:
        return self.system == "Darwin"

    @cached_property
    def is_windows(self) -> bool:
        return self.system == "Windows"

    @cached_property
    def conda_bin(self) -> Path:
        path = Path(self.environ["CONDA_EXE"])
        check_file(path, "binary located at %s")
        return path

    @cached_property
    def conda_root_prefix(self) -> Path:
        path = Path(self.environ["CONDA_PREFIX"])
        check_dir(path, "conda root prefix located at %s")
        return path

    @cached_property
    def mamba_bin(self) -> Path:
        if self.conda == "mamba" and self.is_windows:
            mamba = "mamba.exe"
        else:
            mamba = self.conda
        path = self.conda_root_prefix / "bin" / mamba
        try:
            check_file(path, "binary located at %s")
            return path
        except RuntimeError:
            logger.warning("%s not found, use conda instead.", self.conda)
            return self.conda_bin

    @cached_property
    def activate_bin(self) -> Path:
        if self.is_windows:
            path = Path("activate")
        else:
            path = self.conda_root_prefix / "bin" / "activate"
            check_file(path, "binary located at %s")
        return path

    @cached_property
    def python_bin(self) -> Path:
        return self.conda_prefix / "bin" / "python"

    @cached_property
    def bash_bin(self) -> Path:
        from shutil import which

        bash_str = "bash.exe" if self.is_windows else "bash"
        bash = which(bash_str, path=self.environ_with_all_paths.get("PATH", None))

        if bash is None:
            raise RuntimeError("Cannot locate bash in environment: %s", self.environ_with_all_paths)

        logger.info("Using bash located at %s", bash)
        return Path(bash)

    @cached_property
    def activate_cmd(self) -> List[str]:
        """Return a command to activate the conda environment."""
        cmd = [] if self.is_windows else ["source"]
        cmd += [str(self.activate_bin), str(self.conda_prefix)]
        return cmd

    @cached_property
    def activate_cmd_str(self) -> str:
        """Return a string of command to activate the conda environment."""
        return list2cmdline(self.activate_cmd)

    @cached_property
    def conda_prefix(self):
        path = self.prefix / self.conda_prefix_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cached_property
    def compile_prefix(self):
        path = self.prefix / self.compile_prefix_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cached_property
    def downoad_prefix(self):
        path = self.prefix / self.download_prefix_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cached_property
    def environ(self) -> Dict[str, str]:
        _dict = dict(os.environ)
        # point CONDA_PREFIX to the root prefix
        conda_bin = Path(_dict["CONDA_EXE"])
        _dict["CONDA_PREFIX"] = str(conda_bin.parent.parent)
        return _dict

    @cached_property
    def environ_with_compile_path(self) -> Dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.compile_prefix / "bin"))
        return env

    @cached_property
    def environ_with_conda_path(self) -> Dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.conda_prefix / "bin"))
        return env

    @cached_property
    def environ_with_all_paths(self) -> Dict[str, str]:
        env = self.environ_with_compile_path.copy()
        prepend_path(env, str(self.conda_prefix / "bin"))
        return env

    def run_all(self):
        # TODO: don't write dict if read from file
        self.write_dict()

        # install conda
        if not self.skip_conda:
            from .packages.conda import Package

            package = Package(self, update=self.update, fast_update=self.fast_update)
            package.run_all()

        for dep, ver in self.dependencies_versioned.items():
            try:
                package_module = import_module(f".packages.{dep}", package="pmpm")
            except ImportError:
                raise RuntimeError(f"Package {dep} is not defined in pmpm.packages.{dep}")
            package = package_module.Package(
                self,
                update=self.update,
                fast_update=self.fast_update,
                arch=self.arch,
                tune=self.tune,
                version=ver,
            )
            package.run_all()


@dataclass
class CondaOnlyEnvironment(InstallEnvironment):
    """Using only the stack provided by conda to compile.

    :param prefix: the prefix path of the environment.
    :conda_channels: conda channels for packages to be searched in.
    :param conda_dependencies: dependencies install via conda.
    :param dependencies: dependencies install via pmpm.
    :param python_version: Python version to be installed.
    :param conda_prefix_name: the subdirectory within `prefix` for conda.
    :param compile_prefix_name: the subdirectory within `prefix` for compiled packages from `dependencies`.
    :param download_prefix_name: the subdirectory within `prefix` for downloaded source codes from `dependencies`.
    :param conda: executable name for conda solver, can be mamba, conda.
    :param sub_platform: such as ubuntu, arch, macports, homebrew, etc.
    :param skip_test: skip test if specified.
    :param skip_conda: skip installing/updating conda.
    :param fast_update: assume minimal change to source of compiled package and perform fast update.
    :param nomkl: if nomkl is used in conda packages, nomkl should be True for non-Intel CPUs.
    :param update: if updating all packages.
    :param arch: -march for compilation, for example, native or x86-64-v3
    :param tune: -mtune for compilation, for example, native or generic
    """

    conda_prefix_name: str = ""
    compile_prefix_name: str = ""
    environment_variable: ClassVar[Tuple[str, ...]] = (
        "CONDA_PREFIX",
        "CONDA_EXE",
        "SCRATCH",
        "TERM",
        "HOME",
        "SYSTEMROOT",
    )
    sanitized_path: ClassVar[Tuple[str, ...]] = ("/bin", "/usr/bin")  # needed for conda to find POSIX executables

    def __post_init__(self):
        super().__post_init__()

        if self.conda_prefix_name != self.compile_prefix_name:
            raise RuntimeError("For conda only environment, conda_prefix_name should equals to compile_prefix_name.")

        append_env(self.conda_dependencies, "cmake")
        if self.nomkl:
            append_env(self.conda_dependencies, "libblas")
            append_env(self.conda_dependencies, "liblapack")
        else:
            append_env(self.conda_dependencies, "libblas=*=*mkl")
            append_env(self.conda_dependencies, "liblapack=*=*mkl")

    # @property
    # def sanitized_path(self) -> List[str]:
    #     import subprocess

    #     res = subprocess.run(
    #         'echo $PATH',
    #         capture_output=True,
    #         shell=True,
    #         check=True,
    #         env={},
    #     )
    #     paths = res.stdout.decode().strip().split(os.pathsep)
    #     paths = [path for path in paths if path != '.']
    #     logger.info('Obtained sanitized PATH: %s', paths)
    #     return paths

    @cached_property
    def environ(self) -> Dict[str, str]:
        os_env = super().environ
        _dict = {key: os_env[key] for key in self.environment_variable if key in os_env}
        for path in self.sanitized_path:
            append_path(_dict, path)
        logger.info("environment constructed as %s", _dict)
        return _dict

    @cached_property
    def environ_with_all_paths(self) -> Dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.conda_prefix / "bin"))
        return env

    @property
    def environ_with_compile_path(self) -> Dict[str, str]:
        return self.environ_with_all_paths

    @property
    def environ_with_conda_path(self) -> Dict[str, str]:
        return self.environ_with_all_paths


def cli():
    env = defopt.run(
        {
            "system_install": InstallEnvironment,
            "conda_install": CondaOnlyEnvironment,
            "system_install_from_file": InstallEnvironment.read_dict,
            "conda_install_from_file": CondaOnlyEnvironment.read_dict,
        },
        strict_kwonly=False,
        show_types=True,
    )
    env.run_all()


if __name__ == "__main__":
    cli()
