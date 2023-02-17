"""
Test boostbuild/validations.py

For the file validations.py the focus is mainly on testing the different
validations that can return errors defined on `boostbuild/errors.py`.
"""
from tests.conftest import (
    BOOST_FILE_TEST,
    remove_test_boost_file,
    write_test_boost_file,
)
from boostbuild.validations import (
    VARIABLES_TARGETS_WHITELIST,
    ATTRIBUTES_WHITELIST,
    validate_file_exists,
    validate_missing_boost_section,
    validate_empty_boost_section,
    validate_boost_targets_chars,
    validate_boost_section_format,
    validate_missing_boost_target,
    validate_attributes_format,
    validate_attributes_chars,
)
from boostbuild.errors import (
    FILE_FOLDER_DOESNT_EXIST,
    MISSING_BOOST_SECTION,
    EMPTY_BOOST_SECTION,
    MISSING_TARGET,
    SELF_VAR_REQUEST,
    BAD_FORMAT_BOOST_SECTION,
    BAD_FORMAT_VARS_SECTION,
    UNKOWN_KEY,
    UNSUPPORTED_VAR_ATTRIBUTE,
    BAD_FORMAT_ATTRIBUTES,
    NOT_ALLOWED_CHARACTERS,
)


def return_validations_data(boost_data, boost_target):
    """Build and return a dictionary required for validations function."""
    return {"boost_data": boost_data, "boost_target": boost_target}


def test_validate_file_exists():
    write_test_boost_file({"sample": "value"})
    assert validate_file_exists(BOOST_FILE_TEST) == ""
    remove_test_boost_file()
    assert validate_file_exists(BOOST_FILE_TEST) == FILE_FOLDER_DOESNT_EXIST.format(
        BOOST_FILE_TEST
    )


def test_validate_boost_section():
    boost_data = {"boost": {"example": "", "example2": ""}}
    assert validate_missing_boost_section(return_validations_data(boost_data, "")) == ""

    boost_data = {}
    assert (
        validate_missing_boost_section(return_validations_data(boost_data, ""))
        == MISSING_BOOST_SECTION
    )


def test_validate_empty_boost_section():
    boost_data = {"boost": {"example": "value"}}
    assert validate_empty_boost_section(return_validations_data(boost_data, "")) == ""

    boost_data = {"boost": ""}
    assert (
        validate_empty_boost_section(return_validations_data(boost_data, ""))
        == EMPTY_BOOST_SECTION
    )


def test_validate_boost_targets_chars():
    boost_data = {"boost": {"example": ""}}
    assert validate_boost_targets_chars(return_validations_data(boost_data, "")) == ""

    boost_data = {"boost": {"example-": ""}}
    assert validate_boost_targets_chars(return_validations_data(boost_data, "")) == ""

    boost_data = {"boost": {"example_": ""}}
    assert validate_boost_targets_chars(return_validations_data(boost_data, "")) == ""

    boost_data = {"boost": {"example:": ""}}
    assert validate_boost_targets_chars(
        return_validations_data(boost_data, "")
    ) == NOT_ALLOWED_CHARACTERS.format(
        "target", "example:", "".join(VARIABLES_TARGETS_WHITELIST)
    )

    boost_data = {"boost": {"example%": "", "example2": ""}}
    assert validate_boost_targets_chars(
        return_validations_data(boost_data, "")
    ) == NOT_ALLOWED_CHARACTERS.format(
        "target", "example%", "".join(VARIABLES_TARGETS_WHITELIST)
    )


def test_validate_boost_section_format():
    boost_data = {"boost": {"example": ""}}
    assert validate_boost_section_format(return_validations_data(boost_data, "")) == ""

    boost_data = {"boost": {}}
    assert validate_boost_section_format(return_validations_data(boost_data, "")) == ""

    boost_data = {"boost": ""}
    assert (
        validate_boost_section_format(return_validations_data(boost_data, ""))
        == BAD_FORMAT_BOOST_SECTION
    )


def test_validate_missing_boost_target():
    boost_data = {"boost": {"example": "", "example2": ""}}

    assert (
        validate_missing_boost_target(return_validations_data(boost_data, "example"))
        == ""
    )
    assert (
        validate_missing_boost_target(return_validations_data(boost_data, "example2"))
        == ""
    )
    assert validate_missing_boost_target(
        return_validations_data(boost_data, "asd")
    ) == MISSING_TARGET.format("asd")


def test_validate_attributes_format():
    attributes = ""
    assert validate_attributes_format(attributes) == ""

    attributes = ["example", "example2"]
    assert validate_attributes_format(attributes) == BAD_FORMAT_ATTRIBUTES.format(
        attributes, "attributes"
    )

    attributes = None
    assert validate_attributes_format(attributes) == BAD_FORMAT_ATTRIBUTES.format(
        attributes, "attributes"
    )


def test_validate_attributes_chars():
    attributes = ""
    assert validate_attributes_chars(attributes) == ""

    attributes = "asdasd"
    assert validate_attributes_chars(attributes) == ""

    attributes = "asd,asd"
    assert validate_attributes_chars(attributes) == ""

    attributes = "123"
    assert validate_attributes_chars(attributes) == NOT_ALLOWED_CHARACTERS.format(
        "attributes", attributes, "".join(ATTRIBUTES_WHITELIST)
    )

    attributes = "asd_asd"
    assert validate_attributes_chars(attributes) == NOT_ALLOWED_CHARACTERS.format(
        "attributes", attributes, "".join(ATTRIBUTES_WHITELIST)
    )
