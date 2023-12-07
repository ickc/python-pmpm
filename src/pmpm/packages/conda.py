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
    install_ipykernel: bool = True
    package_name: ClassVar[str] = "conda"

    @property
    def src_dir(self) -> Path:
        return self.env.conda_prefix / "bin"

    def _install_conda(self) -> None:
        logger.info("Creating conda environment")
        cmd = [
            str(self.env.mamba_bin),
            "env",
            "create",
            "--file",
            str(self.env.conda_environment_path),
            "--prefix",
            str(self.env.conda_prefix),
        ]
        run(
            cmd,
            env=self.env.environ_with_conda_path,
        )

    def _install_ipykernel(self) -> None:
        logger.info("Registering ipykernel")
        cmd = [
            "python",
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            self.env.name,
            "--display-name",
            self.env.name,
        ]
        self.run_conda_activated(
            cmd,
            env=self.env.environ_with_conda_path,
        )

    def install_env(self) -> None:
        self._install_conda()
        if self.install_ipykernel:
            self._install_ipykernel()

    def update_env(self) -> None:
        logger.info("Updating conda environment")
        cmd = [
            str(self.env.mamba_bin),
            "env",
            "update",
            "--file",
            str(self.env.conda_environment_path),
            "--prefix",
            str(self.env.conda_prefix),
        ]
        run(
            cmd,
            env=self.env.environ_with_conda_path,
        )
