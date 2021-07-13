from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import ClassVar, TYPE_CHECKING
import subprocess
import os

from . import GenericPackage, combine_commands

logger = getLogger('pmpm')

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = 'libmadam'

    @property
    def src_dir(self) -> Path:
        return self.env.downoad_prefix / self.package_name

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
        env['FC'] = 'mpifort'
        env['FCFLAGS'] = '-O3 -fPIC -pthread -march=native -mtune=native'
        env['CFLAGS'] = '-O3 -fPIC -pthread -march=native -mtune=native'
        inc = [str(self.env.compile_prefix / 'include')]
        lib = [str(self.env.compile_prefix / 'lib')]
        if self.env.is_darwin:
            inc.append('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include')
            lib.append('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib')
        temp = f' -I{os.pathsep.join(inc)} -L{os.pathsep.join(lib)}'
        env['CFLAGS'] += temp
        env['FCFLAGS'] += temp

        cmd = [
            './configure',
            f'--prefix={self.env.compile_prefix}',
        ]
        cmd_str = combine_commands(self.activate_cmd, cmd)
        logger.info('Running %s', cmd_str)
        subprocess.run(
            cmd_str,
            check=True,
            env=env,
            cwd=self.src_dir,
            shell=True,
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
            str(self.env.python_bin),
            'setup.py',
            'install',
        ]
        cmd_str = combine_commands(self.activate_cmd, cmd)
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
            str(self.env.python_bin),
            'setup.py',
            'test',
        ]
        cmd_str = combine_commands(self.activate_cmd, cmd)
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
        if not self.env.skip_test:
            self._test()

    def update_env(self):
        logger.info('Updating %s, any changes in %s will be installed.', self.package_name, self.src_dir)
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()

    def update_env_fast(self):
        logger.info('Fast updating %s, any changes in %s will be installed.', self.package_name, self.src_dir)
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()
