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


def run(
    *commands: Union[str, List[str]],
    **kwargs,
) -> None:
    """Run commands with side effects between them.

    :param commands: can be in string or list of string that subprocess.run accepts.
    :param kwargs: passes to subprocess.run
    """
    n = len(commands)
    if n == 1:
        command = commands[0]
        cmd_str = subprocess.list2cmdline(command)
        logger.info("Running %s", cmd_str)
        subprocess.run(
            command,
            check=True,
            **kwargs,
        )
    elif n > 1:
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
    else:
        raise ValueError("No commands given.")
