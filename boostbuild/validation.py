"""Validation of Boost file."""
from pathlib import Path
import re
import os

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

    variables = {}
    if "vars" in boost_data:
        variables = boost_data["vars"]
        error = validate_vars(variables)
        if error:
            return {"error": error}

    error = validate_targets(boost_data["boost"], variables)
    if error:
        return {"error": error}
    return boost_data


def validate_vars(variables: dict) -> str:
    """Validate vars section from boost file.

    params:
        - variables: dict containing vars section of boost file.

    returns:
        - str with error hinting if error found, empty otherwise.
    """
    for _, value in variables.items():
        value = value.strip().replace("\n", " ")  # clean vars before looking for errors
        if "exec" in value:
            if "exec" in value.replace("exec", "", 1):
                position = value.find("exec")
                return build_error_hinting(
                    value, position, "Keyword exec not allowed twice on same variable"
                )
    return ""


def validate_targets(targets: dict, validated_variables: dict) -> str:
    """Validate boost section from boost file.

    params:
        - targets: dict containing boost targets
        - validated_variables: dict containing validated vars which can be consumed.

    returns:
        - str with error hinting if error found, empty otherwise.
    """
    for _, value in targets.items():
        # validate if requested variable exists
        requested_variables = re.findall("{.*?}", value)
        validated_env_variable = set()
        for rvar in requested_variables:
            rvar = rvar.replace("{", "").replace("}", "")
            # if requested variale is not defined on vars, search it on environment variables
            if rvar not in validated_variables and rvar not in validated_env_variable:
                validated_env_variable.add(rvar)
                try:
                    os.environ[rvar]
                except KeyError:
                    position = 0
                    command = ""
                    for command in value.split("\n"):
                        if rvar in command:
                            position = command.find(rvar)
                            break
                    return build_error_hinting(
                        command,
                        position,
                        f"Varible {rvar} was not declated neither on vars section or on OS environment variables",
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
