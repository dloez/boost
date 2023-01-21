"""
unkown command module.
This command allows the execution of a command which is not currently included on Boost
command ecosystem.
"""
import subprocess
from typing import List


def win_exec(command: List[str], capture_output=False) -> dict:
    """Execute given command.

    This command is executed using powershell.

    Arguments:
        - command: list containing command and its arguments.
        - `capture_output`: determine if the command output should be printed, or captured.

    Returns:
        - `dict` containing output of command on output key or error on error key.
    """
    result = subprocess.run(
        ["powershell", " ".join(command)],
        check=False,
        text=True,
        capture_output=capture_output,
    )
    output = {"code": str(result.returncode)}
    if capture_output:
        output["output"] = result.stdout.rstrip().lstrip()
        output["error"] = result.stderr.rstrip().lstrip()
    return output


def posix_exec(command: List[str], capture_output=False) -> dict:
    """Execute given command.

    This command is executed using powershell.

    Arguments:
        - command: list containing command and its arguments.
        - `capture_output`: determine if the command output should be printed, or captured.

    Returns:
        - `dict` containing output of command on output key or error on error key.
    """
    result = subprocess.run(
        ["/bin/bash", "-c", " ".join(command)],
        check=False,
        text=True,
        capture_output=capture_output,
    )
    output = {"code": str(result.returncode)}
    if capture_output:
        output["output"] = result.stdout.rstrip().lstrip()
        output["error"] = result.stderr.rstrip().lstrip()
    return output
