"""Test boostbuild/utils.py"""
from tests.conftest import (
    BOOST_FILE_TEST,
    write_test_boost_file,
    remove_test_boost_file,
)
from boostbuild.utils import (
    get_required_vars_dict,
    find_variables_in,
    from_yaml_to_dict,
)


def test_from_yaml_to_dict():
    content = {"example": "example value"}
    write_test_boost_file(content)
    assert from_yaml_to_dict(BOOST_FILE_TEST) == content
    remove_test_boost_file()
    assert from_yaml_to_dict(BOOST_FILE_TEST) == {}


def test_find_variables_in():
    test_sets = [
        ("hey im a {example} with other {examples}", ["example", "examples"]),
        ("another one {coming}", ["coming"]),
        ("im the last{one}l", ["one"]),
        ("kidding {}", [""]),
    ]

    for test, result in test_sets:
        assert find_variables_in(test) == result


def test_get_required_vars_dict():
    targets = {
        "example": "im a example requiring {example}",
        "other_example": "im another example {other_example} and {example}",
        "last_example": "{example}\n{example2}",
    }
    output = get_required_vars_dict(targets)
    expected_output = {
        "example": ("example", "im a example requiring {example}"),
        "other_example": (
            "other_example",
            "im another example {other_example} and {example}",
        ),
        "example2": ("last_example", "{example2}"),
    }

    assert isinstance(output, dict)
    assert len(output) == 3
    for key, value in output.items():
        assert isinstance(key, str)
        assert isinstance(value, tuple)
        deleted_item = expected_output.pop(key)
        assert deleted_item == value
    assert len(expected_output) == 0
