from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING
from logging import getLogger

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional, Dict

    from ..core import InstallEnvironment

logger = getLogger('pmpm')


@dataclass
class GenericPackage:
    env: InstallEnvironment
    update: Optional[bool] = None
    package_name: ClassVar[str] = ''

    def __post_init__(self):
        # use some heuristics to determine if we need to update or not
        if self.update is None:
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

    def run(self):
        raise NotImplementedError

    @property
    def is_installed(self) -> bool:
        path = self.src_dir
        is_dir = path.is_dir()
        if is_dir:
            logger.info('Found %s, assuming %s has already been installed.', path, self.package_name)
        else:
            logger.info('%s not found, assuming %s not already installed.', path, self.package_name)
        return is_dir

    @property
    def platform(self) -> str:
        return self.env.platform

    @property
    def sub_platform(self) -> str:
        return self.env.sub_platform

    @property
    def activate_cmd(self) -> str:
        return self.env.activate_cmd
