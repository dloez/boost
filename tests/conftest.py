"""Define shared hooks, fixtures and helper functions used on all tests."""
from pathlib import Path
import yaml


def write_test_boost_file(content):
    with open(BOOST_FILE_TEST, "w") as handler:
        handler.write(yaml.dump(content))


def remove_test_boost_file():
    if BOOST_FILE_TEST.exists():
        BOOST_FILE_TEST.unlink()


def pytest_sessionfinish(session, exitstatus):
    remove_test_boost_file()


BOOST_FILE_TEST = Path("TEST_BOOST_FILE.yaml")
