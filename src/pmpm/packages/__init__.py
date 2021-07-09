from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING
import subprocess
from logging import getLogger

if TYPE_CHECKING:
    from typing import Optional, Dict, List

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

        raise NotImplementedError

    @property
    def environ(self) -> Dict[str, str]:
        """The environment dict that this package needs.

        This can depends on platform, subplatform"""
        raise NotImplementedError

    @property
    def is_installed(self) -> bool:
        raise NotImplementedError

    def install_env(self):
        raise NotImplementedError

    def update_env(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def platform(self) -> str:
        return self.env.platform

    @property
    def sub_platform(self) -> str:
        return self.sub_platform
