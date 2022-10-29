"""
Delete command module
This command allows deleteion of files and folders
"""
from pathlib import Path
import shutil
from typing import List


def generic_exec(args: List[str]) -> bool:
    """Delete given object which can be a file or a directory

    params:
        - args: list of given arguments.
            - obj: Object system path that needs to be deleted. Can be a file or
            a folder.

    returns:
        - bool as True if sucess, False otherwise.
    """
    obj = Path(args[0])
    if obj.is_file():
        obj.unlink()
    elif obj.is_dir():
        shutil.rmtree(obj)
    return True
