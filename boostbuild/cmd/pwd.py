"""
pwd command module.
This command returns the current working directory.
"""
from typing import List
import os


def generic_exec(_args: List[str], capture_output: bool = False) -> dict:
    """Delete given object which can be a file or a directory

    Arguments:
        - `args`: list of given arguments. None of them are used on this command.
        - `capture_output`: determine if the command output should be printed, or captured.

    Returns:
        - `dict` containing output of command on output key or error on error key.
    """
    output = os.getcwd()
    if not capture_output:
        print(output)
    return {"output": os.getcwd()}
