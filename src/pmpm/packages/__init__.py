from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

from custom_inherit import DocInheritMeta

from ..util import run

if TYPE_CHECKING:
    from pathlib import Path

    from ..core import InstallEnvironment

logger = getLogger("pmpm")


@dataclass
class GenericPackage(metaclass=DocInheritMeta(style="google_with_merge")):  # type: ignore[misc]
    """Generic package class.

    Args:
        env: the environment to install the package into.
        update: whether to update the package if it is already installed.
        fast_update: whether to use fast update. If True, it will be used if the package
            supports it, otherwise it will fall back to normal update.
        package_name: the name of the package.
        arch: the arch to compile for.
        tune: the tune to compile for.
        version: the version to install, which should be a valid git tag/branch for git-based packages.
    """

    env: InstallEnvironment
    update: bool | None = None
    fast_update: bool = False
    package_name: ClassVar[str] = ""
    # see doc for march: https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html
    # for example, native or x86-64-v3
    arch: str = "x86-64-v3"
    # for example, native or generic
    tune: str = "generic"
    # must be a valid git tag/branch for git-based packages
    version: str = "master"

    def __post_init__(self) -> None:
        # use some heuristics to determine if we need to update or not
        if self.update is None:
            if self.fast_update:
                self.update = True
            else:
                self.update = self.is_installed
        self.update: bool

    @property
    def src_dir(self) -> Path:
        raise NotImplementedError

    def download(self) -> None:
        raise NotImplementedError

    def install_env(self) -> None:
        raise NotImplementedError

    def update_env(self) -> None:
        raise NotImplementedError

    def update_env_fast(self) -> None:
        logger.warning("%s has not implemented fast update, using normal update...", self.package_name)
        return self.update_env()

    def run_conda_activated(
        self,
        command: str | list[str],
        **kwargs,
    ) -> None:
        """Run commands with conda activated.

        :param kwargs: passes to subprocess.run
        """
        logger.info("Running the following command with conda activated:")
        cmd = [str(self.env.mamba_bin), "run", "--prefix", str(self.env.prefix)]
        if isinstance(command, str):
            cmd.append(command)
        else:
            cmd += list(command)
        run(cmd, **kwargs)

    def run_all(self) -> None:
        if self.update:
            if self.fast_update:
                self.update_env_fast()
            else:
                self.update_env()
        else:
            self.install_env()

    @property
    def is_installed(self) -> bool:
        path = self.src_dir
        is_dir = path.is_dir()
        if is_dir:
            logger.info("Found %s, assuming %s has already been installed.", path, self.package_name)
        else:
            logger.info("%s not found, assuming %s not already installed.", path, self.package_name)
        return is_dir

    @property
    def system(self) -> str:
        return self.env.system

    @property
    def sub_platform(self) -> str:
        return self.env.sub_platform
