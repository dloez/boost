"""Main module"""
import sys
import importlib
from pathlib import Path
import argparse

import yaml
from yaml.loader import SafeLoader


def init_parser() -> argparse.ArgumentParser:
    """Initialize argument parser.

    returns:
        - ArgumentParser with configured arguments.
    """
    parser = argparse.ArgumentParser(
        prog="Boost", description="A modern python multiplatform build system"
    )
    parser.add_argument(
        "boost", help="Boost operation", nargs="?", default="", type=str
    )
    return parser


def validate_boost() -> dict | bool:
    """Reads and validates boost.yaml file.

    returns:
        - dict containing parsed and validated yaml.
        - bool as false in case yaml file could not be readen or validated.
    """
    # TODO: improve validation and in case of error during valdiation
    # return useful error codes/messages
    if not BOOST_FILE.exists():
        return False

    with open(BOOST_FILE, "r", encoding="utf8") as handler:
        boost_data = yaml.load(handler, Loader=SafeLoader)
    if "boost" in boost_data:
        return boost_data
    return False


def call_command(cmd: str, args: list) -> bool:
    """Execute given command.

    Given command is dyanmically imported from cmd module.
    If module is not found, we will be opnening a shell an executing the command
    directly.

    params:
        - cmd: command that needs to be executed.
        - args: command arguments.

    returns:
        - bool as True if command was executed succesfully, False otherwise.
    """
    try:
        command = importlib.import_module(f"boost.cmd.{cmd}")
    except ModuleNotFoundError:
        return False
    command.generic_exec(args)
    return True


def main() -> int:
    """Main function"""
    parser = init_parser()
    args = parser.parse_args()

    boost_data = validate_boost()
    if not boost_data:
        return 1

    if not args.boost:
        # if not boost operation was specified, use first one
        boost = next(iter(boost_data["boost"]))
    else:
        boost = args.boost
    commands = boost_data["boost"][boost].split("\n")[:-1]
    for cmd in commands:
        cmd, *args = cmd.split(" ")
        call_command(cmd, args)

    # delete = importlib.import_module("boost.cmd.delete")
    # delete.generic_exec(Path("example1.txt"))
    return 0


BOOST_FILE = Path("boost.yaml")

if __name__ == "__main__":
    sys.exit(main())
