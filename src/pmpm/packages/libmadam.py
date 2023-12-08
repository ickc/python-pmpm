from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

from ..util import run
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

    def download(self) -> None:
        logger.info("Downloading %s", self.package_name)
        cmd = [
            "git",
            "clone",
            f"https://github.com/hpc4cmb/{self.package_name}.git",
        ]
        run(
            cmd,
            env=self.env.environ_with_all_paths,
            cwd=self.src_dir.parent,
        )
        if (branch := self.version) is not None:
            logger.info("Changing to %s branch...", branch)
            cmd = [
                "git",
                "checkout",
                branch,
            ]
            run(
                cmd,
                env=self.env.environ_with_all_paths,
                cwd=self.src_dir,
            )

    def _autogen(self) -> None:
        logger.info("Running autogen")
        self.run_conda_activated(
            "./autogen.sh",
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _configure(self) -> None:
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

    def _make(self) -> None:
        logger.info("Running make")
        cmd = [
            "make",
            f"-j{self.env.cpu_count}",
        ]
        run(
            cmd,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _make_install(self) -> None:
        logger.info("Running make install")
        cmd = [
            "make",
            "install",
            f"-j{self.env.cpu_count}",
        ]
        run(
            cmd,
            env=self.env.environ_with_compile_path,
            cwd=self.src_dir,
        )

    def _python_install(self) -> None:
        logger.info("Running Python install")
        cmd = [
            "python",
            "setup.py",
            "install",
        ]
        self.run_conda_activated(
            cmd,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir / "python",
        )

    def _test(self) -> None:
        logger.info("Running test")
        cmd = [
            "python",
            "setup.py",
            "test",
        ]
        self.run_conda_activated(
            cmd,
            env=self.env.environ_with_conda_path,
            cwd=self.src_dir / "python",
        )

    def install_env(self) -> None:
        logger.info("Installing %s", self.package_name)
        self.download()
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()

    def update_env(self) -> None:
        logger.info("Updating %s, any changes in %s will be installed.", self.package_name, self.src_dir)
        self._autogen()
        self._configure()
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()

    def update_env_fast(self) -> None:
        logger.info("Fast updating %s, any changes in %s will be installed.", self.package_name, self.src_dir)
        self._make()
        self._make_install()
        self._python_install()
        if not self.env.skip_test:
            self._test()
