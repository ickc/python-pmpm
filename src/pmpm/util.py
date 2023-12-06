from __future__ import annotations

import platform
import subprocess
from logging import getLogger
from shutil import which
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Union

logger = getLogger(__name__)


def run(
    command: Union[str, List[str]],
    **kwargs,
) -> None:
    """Run command while logging what is running.

    :param command: can be in string or list of string that subprocess.run accepts.
    :param kwargs: passes to subprocess.run
    """
    cmd_str = subprocess.list2cmdline(command)
    logger.info("Running %s", cmd_str)
    subprocess.run(
        command,
        check=True,
        **kwargs,
    )
