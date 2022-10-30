"""Validation of Boost file."""
from pathlib import Path

import yaml
from yaml.loader import SafeLoader


def validate_boost_file(boost_file_path: Path) -> dict:
    """Validate boost.yaml file.

    This functions parses and validates boost file and, if found, returns found error with
    hints feedback.

    returns:
        - dict containing validated boost file or, if found, validation error on error key.
    """
    if not boost_file_path.exists():
        return {
            "error": "Boost file does not exist, please read https://github.com/dloez/boost/tree/main#using-boost"
        }

    with open(boost_file_path, "r", encoding="utf8") as handler:
        boost_data = yaml.load(handler, Loader=SafeLoader)

    if "boost" not in boost_data:
        return {
            "error": "boost section file does not exist, please read https://github.com/dloez/boost/tree/main#using-boost"
        }

    if "vars" in boost_data:
        error = validate_vars(boost_data["vars"])
        if error:
            return {"error": error}
    return boost_data


def validate_vars(variables: dict) -> str:
    """Validate vars section from boost file.

    params:
        - vars: dict containing vars section of boost file.

    returns:
        - str with error hinting if error found, empty otherwise.
    """
    for _, value in variables.items():
        value = value.strip()  # clean new line at the end of str

        # multi-line variables are not allowed
        if "\n" in value:
            position = value.find("\n")
            error = value.replace("\n", " ")
            return build_error_hinting(
                error, position, "Multi-line variables are not allowed"
            )
        if "exec" in value:
            if "exec" in value.replace("exec", "", 1):
                position = value.find("exec")
                return build_error_hinting(
                    value, position, "Keyword exec not allowed twice on same variable"
                )
    return ""


def build_error_hinting(error, position, message) -> str:
    """Build error hinting

    This functions returns a string with basic error hinting. Ex:
    variable: exec exec pwd
    ---------------^-------
    multiple exec instructions on a single variable are not allowed

    params:
        - error: str which contains the error.
        - position: character where the error is located.
        - message: error message which should be printed out with.

    returns:
        - string containing error and hinting, similar to above example.
    """
    error += "\n"
    for i in range(len(error.strip())):
        if i != position:
            error += "-"
            continue
        error += "^"
    error += f"\n{message}"
    return error
