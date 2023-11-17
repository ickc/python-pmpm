from __future__ import annotations

import subprocess
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path
    from typing import List, Optional, Union

    from ..core import InstallEnvironment

logger = getLogger("pmpm")


def combine_commands(*args: Union[str, List[str]]) -> str:
    """Combine multiple commands into a single line of string for subprocess.

    :param args: can be in string or list of string that subprocess.run accepts.
    """
    return " && ".join(cmd if type(cmd) is str else subprocess.list2cmdline(cmd) for cmd in args)


@dataclass
class GenericPackage:
    env: InstallEnvironment
    update: Optional[bool] = None
    fast_update: bool = False
    package_name: ClassVar[str] = ""
    # see doc for march: https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html
    # for example, native or x86-64-v3
    arch: str = "x86-64-v3"
    # for example, native or generic
    tune: str = "generic"

    def __post_init__(self):
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

    def download(self):
        raise NotImplementedError

    def install_env(self):
        raise NotImplementedError

    def update_env(self):
        raise NotImplementedError

    def update_env_fast(self):
        logger.warning("%s has not implemented fast update, using normal update...", self.package_name)
        return self.update_env()

    @staticmethod
    def run_simple(
        command: List[str],
        **kwargs,
    ):
        """Run single command without shell.

        :param kwargs: passes to subprocess.run"""
        cmd_str = subprocess.list2cmdline(command)
        logger.info("Running %s", cmd_str)
        subprocess.run(
            command,
            check=True,
            **kwargs,
        )

    def run(
        self,
        *commands: Union[str, List[str]],
        **kwargs,
    ):
        """Run commands through bash.

        :param kwargs: passes to subprocess.run
        """
        cmd_str = combine_commands(*commands)
        logger.info("Running %s", cmd_str)
        subprocess.run(
            cmd_str,
            check=True,
            shell=True,
            executable=self.bash_bin,
            **kwargs,
        )

    def run_conda_activated(
        self,
        *commands: Union[str, List[str]],
        **kwargs,
    ):
        """Run commands through bash with conda activated.

        :param kwargs: passes to subprocess.run
        """
        logger.info("Running the following command with conda activated:")
        self.run(self.activate_cmd_str, *commands, **kwargs)

    def run_all(self):
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

    @property
    def activate_cmd(self) -> List[str]:
        return self.env.activate_cmd

    @property
    def activate_cmd_str(self) -> str:
        return self.env.activate_cmd_str

    @property
    def bash_bin(self) -> str:
        return self.env.bash_bin
