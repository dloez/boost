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
    validate_file_exists,
    validate_missing_boost_section,
    validate_empty_boost_section,
    validate_boost_targets_chars,
    validate_boost_section_format,
    validate_boost_target,
    validate_missing_boost_target,
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


def test_validate_file_exists():
    write_test_boost_file({"sample": "value"})
    assert validate_file_exists(BOOST_FILE_TEST) == ""
    remove_test_boost_file()
    assert validate_file_exists(BOOST_FILE_TEST) == FILE_FOLDER_DOESNT_EXIST.format(
        BOOST_FILE_TEST
    )


def test_validate_boost_section():
    boost_data = {"boost": {"example": "", "example2": ""}}
    assert validate_missing_boost_section(boost_data, "") == ""

    boost_data = {}
    assert validate_missing_boost_section(boost_data, MISSING_BOOST_SECTION)


def test_validate_empty_boost_section():
    boost_data = {"boost": {"example": "value"}}
    assert validate_empty_boost_section(boost_data, "") == ""

    boost_data = {"boost": ""}
    assert validate_empty_boost_section(boost_data, "") == EMPTY_BOOST_SECTION


def test_validate_boost_targets_chars():
    boost_data = {"boost": {"example": ""}}
    assert validate_boost_targets_chars(boost_data, "") == ""

    boost_data = {"boost": {"example-": ""}}
    assert validate_boost_targets_chars(boost_data, "") == ""

    boost_data = {"boost": {"example_": ""}}
    assert validate_boost_targets_chars(boost_data, "") == ""

    boost_data = {"boost": {"example:": ""}}
    assert validate_boost_targets_chars(
        boost_data, ""
    ) == NOT_ALLOWED_CHARACTERS.format(
        "target", "example:", "".join(VARIABLES_TARGETS_WHITELIST)
    )

    boost_data = {"boost": {"example%": "", "example2": ""}}
    assert validate_boost_targets_chars(
        boost_data, ""
    ) == NOT_ALLOWED_CHARACTERS.format(
        "target", "example%", "".join(VARIABLES_TARGETS_WHITELIST)
    )


def test_validate_boost_section_format():
    boost_data = {"boost": {"example": ""}}
    assert validate_boost_section_format(boost_data, "") == ""

    boost_data = {"boost": {}}
    assert validate_boost_section_format(boost_data, "") == ""

    boost_data = {"boost": ""}
    assert validate_boost_section_format(boost_data, "") == BAD_FORMAT_BOOST_SECTION


def test_validate_boost_target():
    boost_data = {"boost": {"example": "", "example2": ""}}

    assert validate_boost_target(boost_data, "example") == "example"
    assert validate_boost_target(boost_data, "") == "example"
    assert validate_boost_target(boost_data, "example2") == "example2"


def test_validate_missing_boost_target():
    boost_data = {"boost": {"example": "", "example2": ""}}

    assert validate_missing_boost_target(boost_data, "example") == ""
    assert validate_missing_boost_target(boost_data, "example2") == ""
    assert validate_missing_boost_target(boost_data, "asd") == MISSING_TARGET.format(
        "asd"
    )