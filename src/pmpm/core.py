from __future__ import annotations

import os
import json
from pathlib import Path
import platform
from logging import getLogger
from functools import cached_property
from dataclasses import dataclass, field
from typing import Tuple, TYPE_CHECKING, ClassVar, List, Optional
import subprocess

import defopt
import psutil

from .templates import CONDA_CHANNELS, CONDA_DEPENDENCIES

if TYPE_CHECKING:
    from typing import Dict, Union

logger = getLogger('pmpm')


def is_intel() -> bool:
    from cpuinfo import get_cpu_info

    _is_intel = get_cpu_info()['vendor_id_raw'] == 'GenuineIntel'
    logger.info(f'Determined if the CPU is Intel: {_is_intel}')
    return _is_intel


def prepend_path(environ: Dict[str, str], path: str):
    """Prepend to PATH in environment dictionary in-place."""
    if 'PATH' in environ:
        environ["PATH"] = path + os.pathsep + environ["PATH"]
    else:
        environ["PATH"] = path


def append_env(dependencies: List[str], package: str):
    """Append a package to conda environment definition."""
    if package not in dependencies:
        dependencies.append(package)


@dataclass
class InstallEnvironment:
    """A Generic install environment."""
    prefix: Path
    conda_environment_path: Path = Path('environment.yml')
    conda_channels: List[str] = field(default_factory=lambda: list(CONDA_CHANNELS))
    conda_dependencies: List[str] = field(default_factory=lambda: list(CONDA_DEPENDENCIES))
    dependencies: List[str] = field(default_factory=list)
    python_version: str = '3.8'
    conda_prefix_name: str = 'conda'
    compile_prefix_name: str = 'compile'
    download_prefix_name: str = 'git'
    conda: str = 'mamba'
    nomkl: Optional[bool] = None
    supported_platforms: ClassVar[Tuple[str, ...]] = ('Linux', 'Darwin')
    platform: ClassVar[str] = platform.system()
    cpu_count: ClassVar[int] = psutil.cpu_count(logical=False)

    def __post_init__(self):
        if self.platform not in self.supported_platforms:
            raise OSError(f'OS {self.platform} not supported.')

        if self.nomkl is None:
            try:
                self.nomkl = False if is_intel() else True
            except ImportError:
                raise RuntimeError('Cannot determine if CPU is Intel. Consider running pip/conda/mamba install py-cpuinfo.')
            except Exception as e:
                logger.critical('Cannot determine nomkl automatically. Try specifying nomkl explicitly.')
                raise e
        self.nomkl: bool

        append_env(self.conda_dependencies, f'python={self.python_version}')
        if self.nomkl:
            append_env(self.conda_dependencies, 'nomkl')

    @property
    def conda_environment(self) -> Dict[str, Union[str, List[str]]]:
        return {
            'name': self.prefix.name,
            'channels': self.conda_channels,
            'dependencies': self.conda_dependencies,
        }

    @cached_property
    def is_linux(self) -> bool:
        return self.platform == 'Linux'

    @cached_property
    def is_darwin(self) -> bool:
        return self.platform == 'Darwin'

    @cached_property
    def conda_bin(self) -> Path:
        return Path(self.environ['CONDA_EXE'])

    @cached_property
    def conda_bin_prefix(self) -> Path:
        return self.conda_bin.parent.parent

    @cached_property
    def mamba_bin(self) -> Path:
        return self.conda_bin_prefix / 'bin' / self.conda

    @cached_property
    def activate_bin(self) -> Path:
        return self.conda_bin_prefix / 'bin' / 'activate'

    @cached_property
    def conda_prefix(self):
        return self.prefix / self.conda_prefix_name

    @cached_property
    def compile_prefix(self):
        return self.prefix / self.compile_prefix_name

    @cached_property
    def downoad_prefix(self):
        return self.prefix / self.download_prefix_name

    @property
    def environ(self) -> Dict[str, str]:
        return dict(os.environ)

    @cached_property
    def environ_with_compile_path(self) -> Dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.compile_prefix / 'bin'))
        return env

    @cached_property
    def environ_with_conda_path(self) -> Dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.conda_prefix / 'bin'))
        return env

    @cached_property
    def environ_with_all_paths(self) -> Dict[str, str]:
        env = self.environ_with_compile_path.copy()
        prepend_path(env, str(self.conda_prefix / 'bin'))
        return env

    def install_conda_packages(self):
        conda_environment_path = self.conda_environment_path
        with open(conda_environment_path, 'w') as f:
            json.dump(self.conda_environment, f)

        logger.info(f'Creating conda environment using {conda_environment_path}')

        subprocess.run(
            [
                str(self.mamba_bin),
                'env', 'create',
                '--file', str(conda_environment_path),
                '--prefix', str(self.conda_prefix),
            ],
            check=True,
            env=self.environ,
        )


@dataclass
class CondaOnlyEnvironment(InstallEnvironment):
    """Using only the stack provided by conda to compile."""
    conda_prefix_name: str = ''
    compile_prefix_name: str = ''
    environment_variable: ClassVar[Tuple[str, ...]] = ('CONDA_EXE', 'SCRATCH', 'TERM', 'HOME')

    def __post_init__(self):
        super().__post_init__()

        assert self.conda_prefix_name == self.compile_prefix_name

        append_env(self.conda_dependencies, 'cmake')
        if self.nomkl:
            append_env(self.conda_dependencies, 'libblas')
            append_env(self.conda_dependencies, 'liblapack')
        else:
            append_env(self.conda_dependencies, 'libblas=*=*mkl')
            append_env(self.conda_dependencies, 'liblapack=*=*mkl')

    @cached_property
    def environ(self) -> Dict[str, str]:
        os_env = os.environ
        return {key: os_env[key] for key in self.environment_variable if key in os_env}

    @cached_property
    def environ_with_all_paths(self) -> Dict[str, str]:
        env = self.environ.copy()
        prepend_path(env, str(self.conda_prefix / 'bin'))
        return env

    @property
    def environ_with_compile_path(self) -> Dict[str, str]:
        return self.environ_with_all_paths

    @property
    def environ_with_conda_path(self) -> Dict[str, str]:
        return self.environ_with_all_paths


def cli():
    env = defopt.run(
        [
            InstallEnvironment,
            CondaOnlyEnvironment,
        ],
        strict_kwonly=False,
    )
    env.install_conda_packages()


if __name__ == '__main__':
    cli()
