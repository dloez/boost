"""
pwd command module.
This command returns the current working directory.
"""
from typing import List
import os


def generic_exec(_args: List[str]) -> dict:
    """Delete given object which can be a file or a directory

    params:
        - args: list of given arguments. None of them are used on this command.

    returns:
        - dict containing output of command on output key or error on error key.
    """
    return {"output": os.getcwd()}
