from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import ClassVar, TYPE_CHECKING
import subprocess

from . import GenericPackage

logger = getLogger('pmpm')

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Dict


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = 'libmadam'

    @property
    def src_dir(self) -> Path:
        return self.env.downoad_prefix / 'libmadam'

    def download(self):
        try:
            cmd = [
                'git',
                'clone',
                'git@github.com:hpc4cmb/libmadam.git',
            ]
            cmd_str = subprocess.list2cmdline(cmd)
            logger.info(
                'Downloading %s by running %s',
                self.package_name,
                cmd_str,
            )
            subprocess.run(
                cmd,
                check=True,
                env=self.env.environ_with_all_paths,
                cwd=self.src_dir.parent,
            )
        except Exception:
            logger.info('Cannot run %s', cmd_str)
            cmd = [
                'git',
                'clone',
                'https://github.com/hpc4cmb/libmadam.git',
            ]
            cmd_str = subprocess.list2cmdline(cmd)
            logger.info('Trying %s instead.', cmd_str)
            subprocess.run(
                cmd,
                check=True,
                env=self.env.environ_with_all_paths,
                cwd=self.src_dir.parent,
            )

    def _autogen(self):
        cmd_str = './autogen.sh'
        logger.info('Running %s', cmd_str)
        subprocess.run(
            cmd_str,
            check=True,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _configure(self):
        env = self.env.environ_with_compile_path.copy()
        env['MPIFC'] = 'mpifort'
        env['FC'] = 'gfortran'
        env['FCFLAGS'] = "-O3 -fPIC -pthread -march=native -mtune=native"
        env['LDFLAGS'] = str(self.env.compile_prefix / 'lib')
        env['MPICC'] = 'mpicc'
        env['CFLAGS'] = "-O3 -fPIC -pthread -march=native -mtune=native"
        cmd = [
            './configure',
            f'--prefix={self.env.compile_prefix}',
        ]
        logger.info('Running %s', subprocess.list2cmdline(cmd))
        subprocess.run(
            cmd,
            check=True,
            env=env,
            cwd=self.src_dir,
        )

    def _make(self):
        cmd = [
            'make',
            f'-j{self.env.cpu_count}',
        ]
        logger.info('Running %s', subprocess.list2cmdline(cmd))
        subprocess.run(
            cmd,
            check=True,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _make_install(self):
        cmd = [
            'make',
            'install',
            f'-j{self.env.cpu_count}',
        ]
        logger.info('Running %s', subprocess.list2cmdline(cmd))
        subprocess.run(
            cmd,
            check=True,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _python_install(self):
        cmd = [
            'python',
            'install',
            '.',
        ]
        cmd_str = '; '.join([self.activate_cmd, subprocess.list2cmdline(cmd)])
        logger.info('Running %s', subprocess.list2cmdline(cmd))
        subprocess.run(
            cmd_str,
            check=True,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir / 'python',
            shell=True,
        )

    def _test(self):
        cmd = [
            'python',
            'setup.py',
            'test',
        ]
        cmd_str = '; '.join([self.activate_cmd, subprocess.list2cmdline(cmd)])
        logger.info('Running %s', subprocess.list2cmdline(cmd))
        subprocess.run(
            cmd_str,
            check=True,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir / 'python',
            shell=True,
        )

    def install_env(self):
        self.download()
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        self._test()

    def update_env(self):
        logger.info('Updating %s, any changes in %s will be installed.', self.package_name, self.src_dir)
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        self._test()

    def run(self):
        self.update_env() if self.update else self.install_env()
