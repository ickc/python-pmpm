from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from logging import getLogger
from typing import ClassVar, TYPE_CHECKING
import subprocess

from . import GenericPackage, combine_commands

logger = getLogger('pmpm')

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = 'toast'

    @property
    def src_dir(self) -> Path:
        return self.env.downoad_prefix / self.package_name

    @cached_property
    def build_dir(self) -> Path:
        path = self.src_dir / 'build'
        path.mkdir(parents=True, exist_ok=True)
        return path

    def download(self):
        try:
            cmd = [
                'git',
                'clone',
                f'git@github.com:hpc4cmb/{self.package_name}.git',
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
                f'https://github.com/hpc4cmb/{self.package_name}.git',
            ]
            cmd_str = subprocess.list2cmdline(cmd)
            logger.info('Trying %s instead.', cmd_str)
            subprocess.run(
                cmd,
                check=True,
                env=self.env.environ_with_all_paths,
                cwd=self.src_dir.parent,
            )

    def _cmake(self):
        prefix = self.env.compile_prefix
        libext = 'dylib' if self.env.is_darwin else 'so'
        cmd = [
            'cmake',
            f'-DCMAKE_INSTALL_PREFIX={prefix}',
            f'-DCMAKE_C_COMPILER={prefix}/bin/mpicc',
            '-DCMAKE_C_FLAGS=-O3 -fPIC -pthread -march=native -mtune=native',
            f'-DCMAKE_CXX_COMPILER={prefix}/bin/mpicxx',
            '-DCMAKE_CXX_FLAGS=-O3 -fPIC -pthread -march=native -mtune=native',
            f'-DMPI_C_COMPILER={prefix}/bin/mpicc',
            f'-DMPI_CXX_COMPILER={prefix}/bin/mpicxx',
            f'-DPYTHON_EXECUTABLE:FILEPATH={prefix}/bin/python',
            f'-DBLAS_LIBRARIES={prefix}/lib/libblas.{libext}',
            f'-DLAPACK_LIBRARIES={prefix}/lib/liblapack.{libext}',
            '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON',
            f'-DFFTW_ROOT={prefix}',
            f'-DSUITESPARSE_INCLUDE_DIR_HINTS={prefix}/include',
            f'-DSUITESPARSE_LIBRARY_DIR_HINTS={prefix}/lib',
            '..',
        ]
        logger.info('In %s, running %s', subprocess.list2cmdline(cmd), self.build_dir)
        subprocess.run(
            cmd,
            check=True,
            env=self.env.environ_with_compile_path,
            cwd=self.build_dir,
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
            cwd=self.build_dir,
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
            cwd=self.build_dir,
        )

    def _test(self):
        cmd = [
            str(self.env.python_bin),
            '-c',
            'from toast.tests import run; run()',
        ]
        cmd_str = combine_commands(self.activate_cmd_str, cmd)
        logger.info('Running %s', subprocess.list2cmdline(cmd))
        subprocess.run(
            cmd_str,
            check=True,
            env=self.env.environ_with_conda_path,
            cwd=self.build_dir,
            shell=True,
        )

    def install_env(self):
        self.download()
        self._cmake()
        self._make()
        self._make_install()
        if not self.env.skip_test:
            self._test()

    def update_env(self):
        logger.info('Updating %s, any changes in %s will be installed.', self.package_name, self.src_dir)
        self._cmake()
        self._make()
        self._make_install()
        if not self.env.skip_test:
            self._test()

    def update_env_fast(self):
        logger.info('Fast updating %s, any changes in %s will be installed.', self.package_name, self.src_dir)
        self._make()
        self._make_install()
        if not self.env.skip_test:
            self._test()
