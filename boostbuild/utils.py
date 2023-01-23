"""Boost helper functions."""
import re


def find_variables_in(content: str):
    """
    Search for variables on the given `content` applying a regex pattern.

    Arguments:
        - `content`: `str` where the regex pattern should be applied to.

    Returns:
        - a list of found matches.
    """
    return re.findall("(?<={)(.*?)(?=})", content)
