from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import ClassVar, TYPE_CHECKING
import subprocess

from . import GenericPackage

logger = getLogger('pmpm')

if TYPE_CHECKING:
    from typing import Dict


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = 'conda'

    def __post_init__(self):
        # use some heuristics to determine if we need to update or not
        if self.update is None:
            self.update = self.is_installed
        self.update: bool

    @property
    def environ(self) -> Dict[str, str]:
        """The environment dict that this package needs.

        This can depends on platform, subplatform"""
        return self.env.environ_with_conda_path

    @property
    def is_installed(self) -> bool:
        path = self.env.conda_prefix / 'etc' / 'conda'
        is_dir = path.is_dir()
        if is_dir:
            logger.info('Found %s, assuming conda has already been installed.', path)
        else:
            logger.info('%s not found, assuming conda not already installed.', path)
        return is_dir

    def install_env(self):
        # conda
        cmd = [
            str(self.env.mamba_bin),
            'env', 'create',
            '--file', str(self.env.conda_environment_path),
            '--prefix', str(self.env.conda_prefix),
        ]
        logger.info('Creating conda environment by running %s', subprocess.list2cmdline(cmd))

        subprocess.run(
            cmd,
            check=True,
            env=self.environ,
        )

        # ipykernel
        cmd = [
            'python',
            '-m', 'ipykernel',
            'install',
            '--user',
            '--name', self.env.name,
            '--display-name', self.env.name,
        ]

        cmd_str = '; '.join([self.activate_str, subprocess.list2cmdline(cmd)])
        logger.info('Creating conda environment by running %s', cmd_str)

        subprocess.run(
            cmd_str,
            check=True,
            env=self.environ,
            shell=True,
        )

    def update_env(self):
        cmd = [
            str(self.env.mamba_bin),
            'env', 'update',
            '--file', str(self.env.conda_environment_path),
            '--prefix', str(self.env.conda_prefix),
        ]
        logger.info(f'Updating conda environment by running {" ".join(cmd)}')

        subprocess.run(
            cmd,
            check=True,
            env=self.environ,
        )

    def run(self):
        self.update_env() if self.update else self.install_env()
