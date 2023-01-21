"""
print command module.
This command prints passed object.
"""
from typing import List


def generic_exec(args: List[str], _capture_output: bool = False) -> dict:
    """Print given object

    Arguments:
        - args: `list` of arguments that are printed with a space between them.
        - `capture_output`: determine if the command output should be printed, or captured.
            This argument is not used on this command.

    Returns:
        - `dict` containing output of command on output key or error on error key.
            This command does not return anything, just an empty `dict`.
    """
    print(" ".join(args))
    return {}
