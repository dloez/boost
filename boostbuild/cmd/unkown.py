"""
unkown command module.
This command allows the execution of a command which is not currently included on Boost
command ecosystem.
"""
import subprocess
from typing import List


def win_exec(command: List[str]) -> dict | bool:
    """Execute given command.

    This command is executed using powershell.

    params:
        - command: list containing command that needs to be executed.

    returns:
        - dict containing output of command on output key or error on error key.
    """
    command.insert(0, "powershell")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output = ""
    for line in iter(process.stdout.readline, b""):
        decoded = line.rstrip().decode(encoding="unicode_escape")
        print(decoded)
        output += decoded

    error = process.stderr.read().decode(encoding="unicode_escape")
    if error:
        return {"error": error}
    return {"output": output}
