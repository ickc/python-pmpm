from __future__ import annotations

import platform
import subprocess
from logging import getLogger
from shutil import which
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Union

logger = getLogger(__name__)

bash: str = ""
if platform.system() != "Windows":
    bash = which("bash")
    if bash is None:
        raise RuntimeError("Cannot locate bash.")
    logger.info("Using bash located at %s", bash)


def combine_commands(*args: Union[str, List[str]]) -> str:
    """Combine multiple commands into a single line of string for subprocess.

    :param args: can be in string or list of string that subprocess.run accepts.
    """
    return " && ".join(cmd if isinstance(cmd, str) else subprocess.list2cmdline(cmd) for cmd in args)


def run_commands_with_side_effects(
    *commands: Union[str, List[str]],
    **kwargs,
) -> None:
    cmd_str = combine_commands(*commands)
    logger.info("Running %s", cmd_str)
    if bash:
        subprocess.run(
            cmd_str,
            check=True,
            shell=True,
            text=True,
            executable=bash,
            **kwargs,
        )
    else:
        subprocess.run(
            cmd_str,
            check=True,
            shell=True,
            text=True,
            **kwargs,
        )
