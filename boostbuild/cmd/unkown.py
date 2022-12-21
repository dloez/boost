"""
unkown command module.
This command allows the execution of a command which is not currently included on Boost
command ecosystem.
"""
import subprocess
from typing import List


def win_exec(command: List[str]) -> dict:
    """Execute given command.

    This command is executed using powershell.

    params:
        - command: list containing command that needs to be executed.

    returns:
        - dict containing output of command on output key or error on error key.
    """
    result = subprocess.run(
        ["powershell", " ".join(command)], check=False, text=True, capture_output=True
    )
    return {
        "error": result.stderr.rstrip().lstrip(),
        "output": result.stdout.rstrip().lstrip(),
    }


def posix_exec(command: List[str]) -> dict:
    """Execute given command.

    This command is executed using bash.

    params:
        - command: list containing command that needs to be executed.

    returns:
        - dict containing output of command on output key or error on error key.
    """
    result = subprocess.run(
        ["/bin/bash", "-c", " ".join(command)],
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "error": result.stderr.rstrip().lstrip(),
        "output": result.stdout.rstrip().lstrip(),
    }
