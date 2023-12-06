from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from functools import cached_property
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

from ..util import run
from . import GenericPackage

logger = getLogger("pmpm")

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Package(GenericPackage):
    package_name: ClassVar[str] = "toast"

    @property
    def src_dir(self) -> Path:
        return self.env.downoad_prefix / self.package_name

    @cached_property
    def build_dir(self) -> Path:
        path = self.src_dir / "build"
        path.mkdir(parents=True, exist_ok=True)
        return path

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
        branch = self.version
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

    def _cmake(self) -> None:
        logger.info("Running CMake")
        prefix = self.env.compile_prefix
        libext = "dylib" if self.env.is_darwin else "so"
        cmd = [
            "cmake",
            "-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON",
            "-DPython3_FIND_VIRTUALENV=ONLY",
            f"-DBLAS_LIBRARIES={prefix}/lib/libblas.{libext}",
            f"-DCMAKE_C_COMPILER={prefix}/bin/mpicc",
            f"-DCMAKE_C_FLAGS=-O3 -fPIC -pthread -march={self.arch} -mtune={self.tune}",
            f"-DCMAKE_CXX_COMPILER={prefix}/bin/mpicxx",
            f"-DCMAKE_CXX_FLAGS=-O3 -fPIC -pthread -march={self.arch} -mtune={self.tune}",
            f"-DCMAKE_INSTALL_PREFIX={prefix}",
            f"-DFFTW_ROOT={prefix}",
            f"-DLAPACK_LIBRARIES={prefix}/lib/liblapack.{libext}",
            f"-DMPI_C_COMPILER={prefix}/bin/mpicc",
            f"-DMPI_CXX_COMPILER={prefix}/bin/mpicxx",
            f"-DPython_EXECUTABLE:FILEPATH={prefix}/bin/python",
            f"-DPYTHON_EXECUTABLE:FILEPATH={prefix}/bin/python",
            f"-DPython3_EXECUTABLE:FILEPATH={prefix}/bin/python",
            f"-DPython3_INCLUDE_DIR={prefix}/include/python{self.env.python_version}",
            f"-DSUITESPARSE_INCLUDE_DIR_HINTS={prefix}/include",
            f"-DSUITESPARSE_LIBRARY_DIR_HINTS={prefix}/lib",
            "..",
        ]
        if self.env.is_darwin:
            cmd.append(f"-DCMAKE_OSX_SYSROOT={self.env.environ['CONDA_BUILD_SYSROOT']}")
        run(
            cmd,
            env=self.env.environ_with_compile_path,
            cwd=self.build_dir,
        )

    def _make(self) -> None:
        logger.info("Running Make")
        cmd = [
            "make",
            f"-j{self.env.cpu_count}",
        ]
        run(
            cmd,
            env=self.env.environ_with_compile_path,
            cwd=self.build_dir,
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
            cwd=self.build_dir,
        )

    def _test(self) -> None:
        logger.info("Running test")
        CIBUILDWHEEL = os.environ.get("CIBUILDWHEEL", None)
        if CIBUILDWHEEL is not None:
            env = self.env.environ_with_all_paths.copy()
            logger.info("Skipping toast timing test by setting CIBUILDWHEEL=%s", CIBUILDWHEEL)
            env["CIBUILDWHEEL"] = CIBUILDWHEEL
        else:
            env = self.env.environ_with_all_paths
        cmd = [
            "python",
            "-c",
            "from toast.tests import run; run()",
        ]
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.run_conda_activated(
                cmd,
                env=env,
                cwd=tmpdirname,
            )

    def install_env(self) -> None:
        logger.info("Installing %s", self.package_name)
        self.download()
        self._cmake()
        self._make()
        self._make_install()
        if not self.env.skip_test:
            self._test()

    def update_env(self) -> None:
        logger.info("Updating %s, any changes in %s will be installed.", self.package_name, self.src_dir)
        self._cmake()
        self._make()
        self._make_install()
        if not self.env.skip_test:
            self._test()

    def update_env_fast(self) -> None:
        logger.info("Fast updating %s, any changes in %s will be installed.", self.package_name, self.src_dir)
        self._make()
        self._make_install()
        if not self.env.skip_test:
            self._test()
