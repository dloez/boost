"""Helper functions to validate boost file format."""
from pathlib import Path
from typing import Union
import string
import yaml

from boostbuild.utils import find_variables_in, get_required_vars_dict, get_boost_target
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

    # validations required data, stored in a dictionary for mutation pourpouses
    validations_data = {"boost_data": boost_data, "boost_target": boost_target}

    # list of validations functions. ORDER IS IMPORTANT AND MUST BE PRESERVED.
    validations = [
        validate_missing_boost_section,
        validate_empty_boost_section,
        validate_boost_targets_chars,
        validate_boost_section_format,
        validate_variables,
    ]

    for validation in validations:
        error = validation(validations_data)
        if error:
            return error

    return boost_data


def validate_variables(validations_data: dict) -> str:
    """
    Validate that variables and their attributes are well fomatted.

    Arguments:
        - `variables`: `dict` containing vars boost section.
        - `boost_data`: `dict` with the contents of boost file. Used to check for missing variables.

    Returns:
        - `str` with the error hinting in case of errors, empty otherwise.
    """
    validations_data["boost_target"] = get_boost_target(
        validations_data["boost_data"], validations_data["boost_target"]
    )

    boost_data = validations_data["boost_data"]
    boost_target = validations_data["boost_target"]
    required_vars = set(find_variables_in(boost_data["boost"][boost_target]))
    # end of validation if there are no variables
    if not required_vars:
        return ""

    variables_section = boost_data["vars"]
    # check format
    if not isinstance(variables_section, list):
        return BAD_FORMAT_VARS_SECTION

    # get required vars by all boost targets
    required_variables: dict[str, tuple[str, str]] = get_required_vars_dict(
        boost_data["boost"]
    )

    checked_vars: list = []
    for var in variables_section:
        single_key_found = False
        for variable, value in var.items():
            if variable == "attributes":
                # list of attribute validations functions. ORDER IS IMPORTANT AND MUST BE PRESERVED.
                attribute_validations = [
                    validate_attributes_format,
                    validate_attributes_chars,
                    validate_supported_attributes,
                ]

                for validation in attribute_validations:
                    error = validation(value)
                    if error:
                        return error
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
                        (var for boost_var in variables_section if rvar in boost_var),
                        None,
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


def validate_missing_boost_section(validations_data: dict) -> str:
    """
    Validate that the given `boost_data` has a boost section.

    Arguments:
        - `validations_data`: dictionary with keys for `boost_data` and `boost_target` to perform any validations.

    Returns:
        - `str` with `MISSING_BOOST_SECTION` error if there is not boost section on `boost_data`.
            Empty `str` otherwise.
    """
    if "boost" not in validations_data["boost_data"]:
        return MISSING_BOOST_SECTION
    return ""


def validate_empty_boost_section(validations_data: dict) -> str:
    """
    Validate that boost section is not empty.

    Arguments:
        - `validations_data`: dictionary with keys for `boost_data` and `boost_target` to perform any validations.

    Returns:
        - `str` with `EMPTY_BOOST_SECTION` error if the boost section is empty.
            Empty `str` otherwise.
    """
    if not validations_data["boost_data"]["boost"]:
        return EMPTY_BOOST_SECTION
    return ""


def validate_boost_targets_chars(validations_data: dict) -> str:
    """
    Validate that boost targets do not have not allowed chars.

    Arguments:
        - `validations_data`: dictionary with keys for `boost_data` and `boost_target` to perform any validations.

    Returns:
        - `str` with `NOT_ALLOWED_CHARACTERS` error if there is not allowed charcters on boost targets.
            Empty `str` otherwise.
    """
    for target, _ in validations_data["boost_data"]["boost"].items():
        if any(c not in VARIABLES_TARGETS_WHITELIST for c in target):
            return NOT_ALLOWED_CHARACTERS.format(
                "target", target, "".join(VARIABLES_TARGETS_WHITELIST)
            )
    return ""


def validate_boost_section_format(validations_data: dict) -> str:
    """
    Validate that boost section format is correct.

    Arguments:
        - `validations_data`: dictionary with keys for `boost_data` and `boost_target` to perform any validations.

    Returns:
        - `str` with `BAD_FORMAT_BOOST_SECTION` error if the format of the boost section is not correct.
            Empty `str` otherwise.
    """
    if not isinstance(validations_data["boost_data"]["boost"], dict):
        return BAD_FORMAT_BOOST_SECTION
    return ""


def validate_missing_boost_target(validations_data: dict) -> str:
    """
    Validate that given `boost_target` is not missing from `boost_data`.

    Arguments:
        - `validations_data`: dictionary with keys for `boost_data` and `boost_target` to perform any validations.

    Returns:
        - `str` with `MISSING_BOOST_TARGET` error if the boost target is missing on `boost_data`.
            Empty `str` otherwise.
    """
    if validations_data["boost_target"] not in validations_data["boost_data"]["boost"]:
        return MISSING_TARGET.format(validations_data["boost_target"])
    return ""


def validate_attributes_format(attributes: str) -> str:
    """
    Validate the format of the attributes inside a variable.

    Arguments:
        - `attributes`: `str` with the attributes that needs to be validated.

    Returns:
        - `str` with `BAD_FORMAT_ATTRIBUTES` error if the attributes are bad formatted.
            Empty `str` otherwise.
    """
    if not isinstance(attributes, str):
        return BAD_FORMAT_ATTRIBUTES.format(attributes, "attributes")
    return ""


def validate_attributes_chars(attributes: str) -> str:
    """
    Validate that there are only allowed characters in attributes. Allowed characters are listed in
    `ATTRIBUTES_WHITELIST`.

    Arguments:
        - `attributes`: `str` with the attributes that needs to be validated.

    Returns:
        - `str` with `NOT_ALLOWED_CHARACTERS` error if the attributes contains not allowed characters.
            Empty `str` otherwise.
    """
    if any(c not in ATTRIBUTES_WHITELIST for c in attributes):
        return NOT_ALLOWED_CHARACTERS.format(
            "attributes", attributes, "".join(ATTRIBUTES_WHITELIST)
        )
    return ""


def validate_supported_attributes(attributes: str) -> str:
    """
    Validate that attributes only contains supported attributes. Supported attribues are listed in `SUPPORTED_ATTRIBUTES`.

    Arguments:
        - `attributes`: `str` with the attributes that needs to be validated.

    Returns:
        - `str` with `UNSUPORTED_VAR_ATTRIBUTE` error if the attributes contains not supported attributes.
            Empty `str` otherwise.
    """
    attrs = attributes.split(",")
    for attr in attrs:
        if attr not in SUPPORTTED_ATTRIBUTES:
            return UNSUPPORTED_VAR_ATTRIBUTE.format(attr, "attributes")
    return ""


# list of supported attributes
SUPPORTTED_ATTRIBUTES = ["secret", "exec"]

# sets of allowed characters
ATTRIBUTES_WHITELIST = list(string.ascii_letters + ",")
VARIABLES_TARGETS_WHITELIST = list(string.ascii_letters + "_-")
