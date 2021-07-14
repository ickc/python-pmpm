from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import ClassVar, TYPE_CHECKING
import subprocess

from . import GenericPackage, combine_commands

logger = getLogger('pmpm')

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = 'conda'

    @property
    def src_dir(self) -> Path:
        return self.env.conda_prefix / 'etc' / 'conda'

    def _install_conda(self):
        logger.info('Creating conda environment')
        cmd = [
            str(self.env.mamba_bin),
            'env', 'create',
            '--file', str(self.env.conda_environment_path),
            '--prefix', str(self.env.conda_prefix),
        ]
        self.run_simple(
            cmd,
            env=self.env.environ_with_conda_path,
        )

    def _install_ipykernel(self):
        logger.info('Registering ipykernel')
        cmd = [
            str(self.env.python_bin),
            '-m', 'ipykernel',
            'install',
            '--user',
            '--name', self.env.name,
            '--display-name', self.env.name,
        ]
        self.run_conda_activated(
            cmd,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir,
        )

    def install_env(self):
        self._install_conda()
        self._install_ipykernel()

    def update_env(self):
        logger.info('Updating conda environment')
        cmd = [
            str(self.env.mamba_bin),
            'env', 'update',
            '--file', str(self.env.conda_environment_path),
            '--prefix', str(self.env.conda_prefix),
        ]
        self.run_simple(
            cmd,
            env=self.env.environ_with_conda_path,
        )
