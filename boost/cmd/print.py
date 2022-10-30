"""
print command module.
This command prints passed object.
"""
from typing import List


def generic_exec(args: List[str]) -> dict | bool:
    """Print given object

    params:
        - args: list of given arguments.
            - obj: Object that needs to be printed.

    returns:
       - dict containing output of command on output key or error on error key.
    """
    print(args[0])
    return {}
