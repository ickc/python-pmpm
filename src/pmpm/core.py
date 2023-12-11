"""pmpm core classes.

It should implements the command line of the package manager,
as well as its main logic.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from functools import cached_property
from importlib import import_module
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import defopt
import psutil
import yaml
from custom_inherit import DocInheritMeta

from .packages.conda import Package as CondaPackage
from .util import append_env, append_path, check_dir, check_file, prepend_path, split_conda_dep_from_pip

if TYPE_CHECKING:
    PMPM_DICT_SPEC = dict[
        str,
        list[str] | str | bool | None,
    ]
    PMPM_YAML_SPEC = dict[
        str,
        str | list[str] | list[str | dict[str, list[str]]] | PMPM_DICT_SPEC,
    ]

logger = getLogger("pmpm")


@dataclass
class InstallEnvironment(metaclass=DocInheritMeta(style="google_with_merge")):  # type: ignore[misc]
    """A Generic install environment.

    Args:
        prefix: the prefix path of the environment.
        file: the YAML file of the environment definition.
        conda_channels: conda channels for packages to be searched in.
        conda_dependencies: dependencies install via conda.
        pip_dependencies: dependencies install via pip.
        dependencies: dependencies install via pmpm.
        python_version: Python version to be installed.
        conda_prefix_name: the subdirectory within `prefix` for conda.
        compile_prefix_name: the subdirectory within `prefix` for compiled packages from `dependencies`.
        download_prefix_name: the subdirectory within `prefix` for downloaded source codes from `dependencies`.
        conda: executable name for conda solver, can be mamba, conda.
        sub_platform: such as ubuntu, arch, macports, homebrew, etc.
        skip_test: skip test if specified.
        skip_conda: skip installing/updating conda.
        fast_update: assume minimal change to source of compiled package and perform fast update.
        install_ipykernel: install this environment as an ipykernel.
        update: if updating all packages. If neither --update nor --no-update is provided, determine automatically.
        arch: -march for compilation, for example, native or x86-64-v3
        tune: -mtune for compilation, for example, native or generic
    """

    prefix: Path
    file: Path | None = None
    conda_channels: list[str] = field(default_factory=list)
    conda_dependencies: list[str] = field(default_factory=list)
    pip_dependencies: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    python_version: str = "3.10"
    conda_prefix_name: str = "conda"
    compile_prefix_name: str = "compile"
    download_prefix_name: str = "git"
    conda: str = "mamba"
    sub_platform: str = ""
    skip_test: bool = False
    skip_conda: bool = False
    fast_update: bool = False
    install_ipykernel: bool = True
    update: bool | None = None
    # see doc for march: https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html
    # for example, native or x86-64-v3
    arch: str = "x86-64-v3"
    # for example, native or generic
    tune: str = "generic"
    conda_environment_filename: ClassVar[str] = "environment.yml"
    supported_systems: ClassVar[tuple[str, ...]] = ("Linux", "Darwin")
    system: ClassVar[str] = platform.system()
    cpu_count: ClassVar[int] = psutil.cpu_count(logical=False)

    def __post_init__(self) -> None:
        if self.file is not None:
            logger.info("Reading environment definition from %s and overriding cli options", self.file)
            with self.file.open() as f:
                data = yaml.safe_load(f)
            if "channels" in data:
                self.conda_channels = data["channels"]
            if "dependencies" in data:
                self.conda_dependencies, pip_dependencies = split_conda_dep_from_pip(data["dependencies"])
                if pip_dependencies:
                    self.pip_dependencies = pip_dependencies
            if "prefix" in data:
                self.prefix = Path(data["prefix"])
            if "_pmpm" in data:
                pmpm = data["_pmpm"]
                if "dependencies" in pmpm:
                    self.dependencies = pmpm["dependencies"]
                if "python_version" in pmpm:
                    self.python_version = str(pmpm["python_version"])
                if "conda_prefix_name" in pmpm:
                    self.conda_prefix_name = pmpm["conda_prefix_name"]
                if "compile_prefix_name" in pmpm:
                    self.compile_prefix_name = pmpm["compile_prefix_name"]
                if "download_prefix_name" in pmpm:
                    self.download_prefix_name = pmpm["download_prefix_name"]
                if "conda" in pmpm:
                    self.conda = pmpm["conda"]
                if "sub_platform" in pmpm:
                    self.sub_platform = pmpm["sub_platform"]
                if "skip_test" in pmpm:
                    self.skip_test = pmpm["skip_test"]
                if "skip_conda" in pmpm:
                    self.skip_conda = pmpm["skip_conda"]
                if "fast_update" in pmpm:
                    self.fast_update = pmpm["fast_update"]
                if "update" in pmpm:
                    self.update = pmpm["update"]
                if "arch" in pmpm:
                    self.arch = pmpm["arch"]
                if "tune" in pmpm:
                    self.tune = pmpm["tune"]
        if self.system not in self.supported_systems:
            raise OSError(f"OS {self.system} not supported.")

        append_env(self.conda_dependencies, f"python={self.python_version}")

    @property
    def name(self) -> str:
        """Return the name of the environment."""
        return self.prefix.name

    @cached_property
    def dependencies_versioned(self) -> dict[str, str | None]:
        """Return a dictionary of dependencies with version."""
        res: dict[str, str | None] = {}
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
    def to_dict(
        self,
    ) -> PMPM_YAML_SPEC:
        """Return a dictionary representation of the environment."""
        conda_dependencies: list[str] | list[str | dict[str, list[str]]] = (
            self.conda_dependencies + [{"pip": self.pip_dependencies}]
            if self.pip_dependencies
            else self.conda_dependencies
        )
        return {
            "name": self.name,
            "channels": self.conda_channels,
            "dependencies": conda_dependencies,
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
                "update": self.update,
                "arch": self.arch,
                "tune": self.tune,
            },
        }

    def write_dict(self) -> None:
        """Write the environment definition to a YAML file."""
        logger.info("Writing environment definition to %s", self.conda_environment_path)
        conda_environment_path = self.conda_environment_path
        conda_environment_path.parent.mkdir(parents=True, exist_ok=True)
        with conda_environment_path.open("w") as f:
            yaml.safe_dump(
                self.to_dict,
                f,
                default_flow_style=False,
            )

    @classmethod
    def from_dict(cls, data: PMPM_YAML_SPEC) -> InstallEnvironment:
        """Construct an environment from a dictionary."""
        pmpm: dict[str, PMPM_DICT_SPEC] = data["_pmpm"]  # type: ignore[assignment]
        conda_dependencies, pip_dependencies = split_conda_dep_from_pip(data["dependencies"])  # type: ignore[arg-type]
        return cls(
            Path(data["prefix"]),  # type: ignore[arg-type]
            conda_channels=data["channels"],  # type: ignore[arg-type]
            conda_dependencies=conda_dependencies,
            pip_dependencies=pip_dependencies,
            dependencies=pmpm["dependencies"],  # type: ignore[arg-type]
            python_version=str(pmpm["python_version"]),
            conda_prefix_name=pmpm["conda_prefix_name"],  # type: ignore[arg-type]
            compile_prefix_name=pmpm["compile_prefix_name"],  # type: ignore[arg-type]
            download_prefix_name=pmpm["download_prefix_name"],  # type: ignore[arg-type]
            conda=pmpm["conda"],  # type: ignore[arg-type]
            sub_platform=pmpm["sub_platform"],  # type: ignore[arg-type]
            skip_test=pmpm["skip_test"],  # type: ignore[arg-type]
            skip_conda=pmpm["skip_conda"],  # type: ignore[arg-type]
            fast_update=pmpm["fast_update"],  # type: ignore[arg-type]
            update=pmpm["update"],  # type: ignore[arg-type]
            arch=pmpm["arch"],  # type: ignore[arg-type]
            tune=pmpm["tune"],  # type: ignore[arg-type]
        )

    @cached_property
    def conda_environment_path(self) -> Path:
        """Path to the YAML file of the environment definition."""
        return self.prefix / self.conda_environment_filename

    @cached_property
    def is_linux(self) -> bool:
        """Return True if the system is Linux."""
        return self.system == "Linux"

    @cached_property
    def is_darwin(self) -> bool:
        """Return True if the system is macOS."""
        return self.system == "Darwin"

    @cached_property
    def conda_bin(self) -> Path:
        """Path to the conda binary."""
        path = Path(self.environ["CONDA_EXE"])
        check_file(path, "binary located at %s")
        return path

    @cached_property
    def conda_root_prefix(self) -> Path:
        """Path to the root prefix of conda."""
        path = Path(self.environ["CONDA_PREFIX"])
        check_dir(path, "conda root prefix located at %s")
        return path

    @cached_property
    def mamba_bin(self) -> Path:
        """Path to the mamba binary."""
        path = self.conda_root_prefix / "bin" / "mamba"
        try:
            check_file(path, "binary located at %s")
            return path
        except RuntimeError:
            logger.warning("%s not found, use conda instead.", self.conda)
            return self.conda_bin

    @cached_property
    def conda_prefix(self) -> Path:
        """Path to the prefix for conda."""
        path = self.prefix / self.conda_prefix_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cached_property
    def compile_prefix(self) -> Path:
        """Path to the prefix for the compiled stack by pmpm."""
        path = self.prefix / self.compile_prefix_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cached_property
    def downoad_prefix(self) -> Path:
        """Path to the prefix for the downloaded source codes by pmpm."""
        path = self.prefix / self.download_prefix_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cached_property
    def environ(self) -> dict[str, str]:
        """Return a dictionary of environment variables."""
        _dict = dict(os.environ)
        # point CONDA_PREFIX to the root prefix
        conda_bin = Path(_dict["CONDA_EXE"])
        _dict["CONDA_PREFIX"] = str(conda_bin.parent.parent)
        return _dict

    @cached_property
    def environ_with_compile_path(self) -> dict[str, str]:
        """Return a dictionary of environment variables with compile prefix prepended to PATH."""
        env = self.environ.copy()
        prepend_path(env, str(self.compile_prefix / "bin"))
        return env

    @cached_property
    def environ_with_conda_path(self) -> dict[str, str]:
        """Return a dictionary of environment variables with conda prefix prepended to PATH."""
        env = self.environ.copy()
        prepend_path(env, str(self.conda_prefix / "bin"))
        return env

    @cached_property
    def environ_with_all_paths(self) -> dict[str, str]:
        """Return a dictionary of environment variables with all prefixes prepended to PATH."""
        env = self.environ_with_compile_path.copy()
        prepend_path(env, str(self.conda_prefix / "bin"))
        return env

    def run_all(self) -> None:
        """Run all steps to install/update the environment."""
        self.write_dict()

        # install conda
        if not self.skip_conda:
            package = CondaPackage(
                self,
                install_ipykernel=self.install_ipykernel,
                update=self.update,
                fast_update=self.fast_update,
            )
            package.run_all()

        for dep, ver in self.dependencies_versioned.items():
            try:
                package_module = import_module(f".packages.{dep}", package="pmpm")
            except ImportError as e:
                raise RuntimeError(f"Package {dep} is not defined in pmpm.packages.{dep}") from e
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
    """Using only the stack provided by conda to compile."""

    conda_prefix_name: str = ""
    compile_prefix_name: str = ""
    environment_variable: ClassVar[tuple[str, ...]] = (
        "CONDA_EXE",  # conda
        "CONDA_PREFIX",  # conda
        "HOME",  # UNIX
        "TERM",  # UNIX
    )
    sanitized_path: ClassVar[tuple[str, ...]] = ("/bin", "/usr/bin")  # needed for conda to find POSIX executables

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.conda_prefix_name != self.compile_prefix_name:
            raise RuntimeError("For conda only environment, conda_prefix_name should equals to compile_prefix_name.")

    # @property
    # def sanitized_path(self) -> list[str]:
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
    def environ(self) -> dict[str, str]:
        os_env = super().environ
        _dict = {key: os_env[key] for key in self.environment_variable if key in os_env}
        for path in self.sanitized_path:
            append_path(_dict, path)
        logger.info("environment constructed as %s", _dict)
        return _dict

    @cached_property
    def environ_with_all_paths(self) -> dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.conda_prefix / "bin"))
        return env

    @property
    def environ_with_compile_path(self) -> dict[str, str]:
        return self.environ_with_all_paths

    @property
    def environ_with_conda_path(self) -> dict[str, str]:
        return self.environ_with_all_paths


def cli() -> None:
    """Command line interface for pmpm."""
    env = defopt.run(
        {
            "system_install": InstallEnvironment,
            "conda_install": CondaOnlyEnvironment,
        },
        strict_kwonly=False,
        show_types=True,
    )
    env.run_all()


if __name__ == "__main__":
    cli()
