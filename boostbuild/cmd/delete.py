"""
delete command module.
This command allows the deletion of files and folders.
"""
from pathlib import Path
import shutil
from typing import List


def generic_exec(args: List[str], capture_output: bool = False) -> dict:
    """Delete given object which can be a file or a directory

    Arguments:
        - `args`: `list` of system paths that needs to be deleted. Can be a file or a folder.
        - `capture_output`: determine if the command output should be printed, or captured.

    Returns:
       - `dict` containing output of command on output key or error on error key.
    """
    obj = Path(args[0])
    if obj.is_file():
        obj.unlink()
    elif obj.is_dir():
        shutil.rmtree(obj)

    output = "object deleted"
    if not capture_output:
        print(output)
    return {"output": output}
