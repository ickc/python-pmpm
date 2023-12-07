from __future__ import annotations

import os
import subprocess
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)


def prepend_path(environ: dict[str, str], path: str) -> None:
    """Prepend to PATH in environment dictionary in-place."""
    if "PATH" in environ:
        environ["PATH"] = path + os.pathsep + environ["PATH"]
    else:
        environ["PATH"] = path


def append_path(environ: dict[str, str], path: str) -> None:
    """Append to PATH in environment dictionary in-place."""
    if "PATH" in environ:
        environ["PATH"] += os.pathsep + path
    else:
        environ["PATH"] = path


def append_env(dependencies: list[str], package: str) -> None:
    """Append a package to conda environment definition."""
    if package not in dependencies:
        dependencies.append(package)


def check_file(path: Path, msg: str) -> None:
    """Check if a file exists."""
    if path.is_file():
        logger.info(msg, path)
    else:
        raise RuntimeError(f"{path} not found.")


def check_dir(path: Path, msg: str) -> None:
    """Check if a directory exists."""
    if path.is_dir():
        logger.info(msg, path)
    else:
        raise RuntimeError(f"{path} not found.")


def run(
    command: str | list[str],
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


def split_conda_dep_from_pip(
    dep: list[str] | list[str | dict[str, list[str]]],
) -> tuple[list[str], list[str]]:
    """Split conda and pip dependencies."""
    conda_dependencies: list[str] = []
    pip_dependencies: list[str] = []
    for i in dep:
        if isinstance(i, str):
            conda_dependencies.append(i)
        elif isinstance(i, dict) and len(i) == 1 and "pip" in i:
            pip_dependencies = i["pip"]
        else:
            raise RuntimeError(f"Invalid dependency {i}")
    return conda_dependencies, pip_dependencies
