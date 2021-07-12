from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import ClassVar, TYPE_CHECKING
import subprocess

from . import GenericPackage

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
            env=self.env.environ_with_conda_path,
        )

    def _install_ipykernel(self):
        # ipykernel
        cmd = [
            str(self.env.python_bin),
            '-m', 'ipykernel',
            'install',
            '--user',
            '--name', self.env.name,
            '--display-name', self.env.name,
        ]

        cmd_str = '; '.join([self.activate_cmd, subprocess.list2cmdline(cmd)])
        logger.info('Registering ipykernel by running %s', cmd_str)

        subprocess.run(
            cmd_str,
            check=True,
            env=self.env.environ_with_conda_path,
            shell=True,
            cwd=self.src_dir,
        )

    def install_env(self):
        self._install_conda()
        self._install_ipykernel()

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
            env=self.env.environ_with_conda_path,
        )
