"""Boost helper functions."""
import re
from pathlib import Path
import yaml


def from_yaml_to_dict(file: Path) -> dict:
    """
    Read and return the content of a yaml file as a dictionary. This function DOES NOT
    raise an exception if the file does not exists.

    Arguments:
        - `file`: `Path` to the yaml file.

    Returns:
        - `dict` with the contents of the file or empty if it does not exists.
    """
    if not file.exists():
        return {}

    with open(file, "r", encoding="utf8") as handler:
        return yaml.load(handler, Loader=yaml.SafeLoader)


def find_variables_in(content: str):
    """
    Search for variables on the given `content` applying a regex pattern.

    Arguments:
        - `content`: `str` where the regex pattern should be applied to.

    Returns:
        - a list of found matches.
    """
    return re.findall("(?<={)(.*?)(?=})", content)


def get_required_vars_dict(targets: dict) -> dict[str, tuple[str, str]]:
    """
    Return a `dict` where each key is a variable found on `targets` and its value its a tuple
    with the target and the line where it was found.

    Arguments:
        - `targets`: `dict` with the contents of the section `boost` on the boost file.

    Returns:
        - `dict` where each key is a variable found on `boost_data` and its value its a tuple
            with the target and the line where it was found.
    """
    variables = {}
    for target, commands in targets.items():
        commands = commands.strip().split("\n")
        for command in commands:
            for var in find_variables_in(command):
                # check if variable was already added so we can show the error
                # on the first variable appearance
                if var in variables:
                    continue
                variables[var] = (target, command)
    return variables


def get_boost_target(boost_data: dict, boost_target: str) -> str:
    """
    Return the first boost target if the given `boost_target` is empty.

    Arguments:
        - `boost_data`: `dict` with the contents on boost file.
        - `boost_target`: `str` with the boost target that is going to be executed.

    Returns:
        - `str` with the first boost target if the given `boost_target` is empty. Return the
            given `boost_terget` othwerwise.
    """
    if boost_target:
        return boost_target
    return list(boost_data["boost"])[0]
