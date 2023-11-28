from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

from . import GenericPackage

logger = getLogger("pmpm")

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = "libmadam"

    @property
    def src_dir(self) -> Path:
        return self.env.downoad_prefix / self.package_name

    def download(self):
        logger.info("Downloading %s", self.package_name)
        cmd = [
            "git",
            "clone",
            f"https://github.com/hpc4cmb/{self.package_name}.git",
        ]
        self.run_simple(
            cmd,
            env=self.env.environ_with_all_paths,
            cwd=self.src_dir.parent,
        )

    def _autogen(self):
        logger.info("Running autogen")
        self.run_conda_activated(
            "./autogen.sh",
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _configure(self):
        env = self.env.environ_with_compile_path.copy()
        env["MPIFC"] = "mpifort"
        env["FC"] = "mpifort"

        inc = self.env.compile_prefix / "include"
        lib = self.env.compile_prefix / "lib"
        temp = f'-O3 -fPIC -pthread -march={self.arch} -mtune={self.tune} -I"{inc}" -L"{lib}"'
        if self.env.is_darwin:
            temp += " -I/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include -L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib"

        env["FCFLAGS"] = temp
        env["CFLAGS"] = temp
        logger.info("Running configure with environment %s", env)

        cmd = [
            "./configure",
            f"--prefix={self.env.compile_prefix}",
        ]

        self.run_conda_activated(
            cmd,
            env=env,
            cwd=self.src_dir,
        )

    def _make(self):
        logger.info("Running make")
        cmd = [
            "make",
            f"-j{self.env.cpu_count}",
        ]
        self.run_simple(
            cmd,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _make_install(self):
        logger.info("Running make install")
        cmd = [
            "make",
            "install",
            f"-j{self.env.cpu_count}",
        ]
        self.run_simple(
            cmd,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _python_install(self):
        logger.info("Running Python install")
        cmd = [
            str(self.env.python_bin),
            "setup.py",
            "install",
        ]
        self.run_conda_activated(
            cmd,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir / "python",
        )

    def _test(self):
        logger.info("Running test")
        cmd = [
            str(self.env.python_bin),
            "setup.py",
            "test",
        ]
        self.run_conda_activated(
            cmd,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir / "python",
        )

    def install_env(self):
        logger.info("Installing %s", self.package_name)
        self.download()
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()

    def update_env(self):
        logger.info("Updating %s, any changes in %s will be installed.", self.package_name, self.src_dir)
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()

    def update_env_fast(self):
        logger.info("Fast updating %s, any changes in %s will be installed.", self.package_name, self.src_dir)
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()
