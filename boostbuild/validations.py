"""Helper functions to validate boost file format."""
from pathlib import Path
from typing import Union
import string
import yaml

from boostbuild.utils import find_variables_in, get_required_vars_dict
from boostbuild.errors import build_error_hinting
from boostbuild.errors import (
    EMPTY_BOOST_SECTION,
    FILE_FOLDER_DOESNT_EXIST,
    MISSING_BOOST_SECTION,
    MISSING_TARGET,
    MISSING_VARIABLE,
    SELF_VAR_REQUEST,
    BAD_FORMAT_VARS_SECTION,
    BAD_FORMAT_BOOST_SECTION,
    BAD_FORMAT_ATTRIBUTES,
    UNKOWN_KEY,
    UNSUPPORTED_VAR_ATTRIBUTE,
    NOT_ALLOWED_CHARACTERS,
)


# pylint: disable=too-many-return-statements, too-many-locals, too-many-nested-blocks, too-many-branches
def validate_boost_file(boost_file: Path, boost_target: str) -> Union[dict, str]:
    """
    Validate that the boost file is correct.
    This function is mandatory to be executed on all boost executions. Code running before this
    function MUST not access boost file as it could not be well formatted.
    Code running after this function is save to avoid any checking on the returned `boost_data`
    to avoid duplicated validations that could cause not updated validations on the future.
    If there are new validations that need to be verified, implement them on this function or call them
    on this function.

    Arguments:
        - `boost_file`: `Path` where the boost file is located.
        - `boost_target`: `str` containing the boost target that will be executed.

    Returns:
        - `dict` containing parsed boost file yaml.
        - `str` in case of error containing error hinting.
    """
    # validate that Boost file exists
    if not boost_file.exists():
        return FILE_FOLDER_DOESNT_EXIST.format(boost_file)

    # load file
    with open(boost_file, "r", encoding="utf8") as handler:
        boost_data = yaml.load(handler, Loader=yaml.SafeLoader)

    # list of validations functions. ORDER IS IMPORTANT AND MUST BE PRESERVED.
    validations = [
        validate_missing_boost_section,
        validate_empty_boost_section,
        validate_boost_targets_chars,
        validate_boost_section_format
    ]
    for validation in validations:
        error = validation(boost_data, boost_target)
        if error:
            return error

    # missing boost target
    boost_target = validate_boost_target(boost_data, boost_target)
    if boost_target not in boost_data["boost"]:
        return MISSING_TARGET.format(boost_target)

    required_vars = set(find_variables_in(boost_data["boost"][boost_target]))
    # end of validation if there are no variables
    if not required_vars:
        return boost_data

    variables = boost_data["vars"]
    # check format
    if not isinstance(variables, list):
        return BAD_FORMAT_VARS_SECTION

    error = validate_variables(variables, boost_data)
    if error:
        return error

    return boost_data


def validate_variables(variables: list, boost_data: dict) -> str:
    """
    Validate that variables and their attributes are well fomatted.

    Arguments:
        - `variables`: `dict` containing vars boost section.
        - `boost_data`: `dict` with the contents of boost file. Used to check for missing variables.

    Returns:
        - `str` with the error hinting in case of errors, empty otherwise.
    """
    # get required vars by all boost targets
    required_variables: dict[str, tuple[str, str]] = get_required_vars_dict(
        boost_data["boost"]
    )

    checked_vars: list = []
    for var in variables:
        single_key_found = False
        for variable, value in var.items():
            if variable == "attributes":
                # check attributes not containing a string
                if not isinstance(value, str):
                    return BAD_FORMAT_ATTRIBUTES.format(value, variable)

                # check attributes containing not allowed characters
                if any(c not in ATTRIBUTES_WHITELIST for c in value):
                    return NOT_ALLOWED_CHARACTERS.format(
                        "attributes", value, "".join(ATTRIBUTES_WHITELIST)
                    )

                # check for no supported attributes
                attrs = value.split(",")
                for attr in attrs:
                    if attr not in SUPPORTTED_ATTRIBUTES:
                        return UNSUPPORTED_VAR_ATTRIBUTE.format(attr, variable)
                continue

            # only one key-value pair is allowed
            if not single_key_found:
                single_key_found = True

                # check variables names containing not allowed characters
                if any(c not in VARIABLES_TARGETS_WHITELIST for c in variable):
                    return NOT_ALLOWED_CHARACTERS.format(
                        "variable", variable, "".join(VARIABLES_TARGETS_WHITELIST)
                    )

                # remove variable from required variables if it exists
                required_variables.pop(variable, None)

                # check inner missing variables
                required_inner_vars = find_variables_in(value)
                for rvar in required_inner_vars:
                    found_variable = next(
                        (var for boost_var in variables if rvar in boost_var), None
                    )

                    # avoid re-checking inner variables
                    if found_variable in checked_vars:
                        continue
                    checked_vars.append(found_variable)

                    if not found_variable:
                        return build_error_hinting(
                            value,
                            value.index("{" + rvar + "}"),
                            MISSING_VARIABLE.format(rvar, "variable", variable),
                        )

                    for found_var_key, found_var_value in found_variable.items():
                        if found_var_key == rvar:
                            return build_error_hinting(
                                found_var_value,
                                found_var_value.index("{" + rvar + "}"),
                                SELF_VAR_REQUEST.format(rvar),
                            )
                continue
            return UNKOWN_KEY.format(variable)

    for variable, (target, command) in required_variables.items():
        return build_error_hinting(
            command,
            command.index("{" + variable + "}"),
            MISSING_VARIABLE.format(variable, "target", target),
        )

    return ""


def validate_missing_boost_section(boost_data: dict, _boost_target: str) -> str:
    """
    Validate that the given `boost_data` has a boost section.

    Arguments:
        - `boost_data`: `dict` with the contents of boost file.
        - `boost_target`: `str` with the content of the argument `target`.

    Returns:
        - `str` with `MISSING_BOOST_SECTION` error if there is not boost section on `boost_data`.
            Empty `str` otherwise.
    """
    if "boost" not in boost_data:
        return MISSING_BOOST_SECTION
    return ""


def validate_boost_target(boost_data: dict, boost_target: str) -> str:
    """
    Return the first boost target if the given `boost_target` is empty.

    Arguments:
        - `boost_data`: `dict` with the contents of boost file.
        - `boost_target`: `str` with the content of the argument `target`.

    Returns:
        - `str` with the first boost target if the given `boost_target` is empty. Return the
            given `boost_terget` othwerwise.
    """
    if boost_target:
        return boost_target
    return list(boost_data["boost"].keys())[0]


def validate_file_exists(file: Path) -> str:
    """
    Validate that the given file exists.

    Arguments:
        - `file`: `Path` to the file to check if it exists or not.

    Returns:
        - `str` with `FILE_FOLDER_DOESNT_EXIST` in case it does not exist or empty if it does.
    """
    if not file.exists():
        return FILE_FOLDER_DOESNT_EXIST.format(file)
    return ""


def validate_empty_boost_section(boost_data: dict, _boost_target: str) -> str:
    """
    Validate that boost section is not empty.

    Arguments:
        - `boost_data`: `dict` with the contents of boost file.
        - `boost_target`: `str` with the content of the argument `target`.

    Returns:
        - `str` with `EMPTY_BOOST_SECTION` error if the boost section is empty.
            Empty `str` otherwise.
    """
    if not boost_data["boost"]:
        return EMPTY_BOOST_SECTION
    return ""


def validate_boost_targets_chars(boost_data: dict, _boost_target: str) -> str:
    """
    Validate that boost targets do not have not allowed chars.

    Arguments:
        - `boost_data`: `dict` with the contents of boost file.
        - `boost_target`: `str` with the content of the argument `target`.

    Returns:
        - `str` with `NOT_ALLOWED_CHARACTERS` error if there is not allowed charcters on boost targets.
            Empty `str` otherwise.
    """
    for target, _ in boost_data["boost"].items():
        if any(c not in VARIABLES_TARGETS_WHITELIST for c in target):
            return NOT_ALLOWED_CHARACTERS.format(
                "target", target, "".join(VARIABLES_TARGETS_WHITELIST)
            )
    return ""


def validate_boost_section_format(boost_data: dict, _boost_target: str) -> str:
    """
    Validate that boost section format is correct.

    Arguments:
        - `boost_data`: `dict` with the contents of boost file.
        - `boost_target`: `str` with the content of the argument `target`.

    Returns:
        - `str` with `BAD_FORMAT_BOOST_SECTION` error if the format of the boost section is not correct.
            Empty `str` otherwise.
    """
    if not isinstance(boost_data["boost"], dict):
        return BAD_FORMAT_BOOST_SECTION
    return ""


def validate_missing_boost_target(boost_data: dict, boost_target: str) -> str:
    """
    Validate that given `boost_target` is not missing from `boost_data`.

    Arguments:
        - `boost_data`: `dict` with the contents of boost file.
        - `boost_target`: `str` with the content of the argument `target`.

    Returns:
        - `str` with `MISSING_BOOST_TARGET` error if the boost target is missing on `boost_data`.
            Empty `str` otherwise.
    """
    if boost_target not in boost_data["boost"]:
        return MISSING_TARGET.format(boost_target)
    return ""


# list of supported attributes
SUPPORTTED_ATTRIBUTES = ["secret", "exec"]

# sets of allowed characters
ATTRIBUTES_WHITELIST = list(string.ascii_letters + ",")
VARIABLES_TARGETS_WHITELIST = list(string.ascii_letters + "_-")
