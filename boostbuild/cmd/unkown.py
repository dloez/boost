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
    # TODO: better error catching
    result = subprocess.run(["powershell", " ".join(command)], check=False)
    if result.stderr:
        return {"error": result.stderr.decode(encoding="unicode_escape")}
    output = ""
    if result.stdout:
        output = result.stdout.decode(encoding="unicode_escape")
    return {"output": output}


def posix_exec(command: List[str]) -> dict:
    """Execute given command.

    This command is executed using bash.

    params:
        - command: list containing command that needs to be executed.

    returns:
        - dict containing output of command on output key or error on error key.
    """
    # TODO: better error catching
    result = subprocess.run(["/bin/bash", "-c", " ".join(command)], check=False)
    if result.stderr:
        return {"error": result.stderr.decode()}
    output = ""
    if result.stdout:
        output = result.stdout.decode()
    return {"output": output}
