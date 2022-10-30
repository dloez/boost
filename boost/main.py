"""Main module"""
import sys
import importlib
from pathlib import Path
import argparse
import os
import re
from typing import List

import yaml
from yaml.loader import SafeLoader
from colorama import init, Fore


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


def validate_boost() -> dict:
    """Reads and validates boost.yaml file.

    returns:
        - dict containing parsed and validated yaml.
        - bool as false in case yaml file could not be readen or validated.
    """
    if not BOOST_FILE.exists():
        return {
            "error": "Boost file does not exist, please read https://github.com/dloez/boost/tree/main#using-boost"
        }

    with open(BOOST_FILE, "r", encoding="utf8") as handler:
        boost_data = yaml.load(handler, Loader=SafeLoader)
    if "boost" in boost_data:
        return boost_data
    return {
        "error": "boost section file does not exist, please read https://github.com/dloez/boost/tree/main#using-boost"
    }


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

    # validate if command has implement a generic execution
    if hasattr(command, "generic_exec"):
        return command.generic_exec(args)

    os_to_function = {"nt": "win_exec", "posix": "posix_exec"}
    try:
        call = os_to_function[os.name]
        return getattr(command, call)(args)
    except KeyError:
        print("Unsuported SO")
    return False


def get_storage(boost_data: dict, variables: List[str]) -> dict:
    """Store commands variables.

    From list of required variables, store on a dictionary each variable key and value.

    params:
        - boost_data: yaml parsed boost file.
        - variables: list of required variables to store.

    returns:
        - dict containing all stored variables for commands use.
    """
    storage = {}
    for variable in variables:
        value = ""
        clean_var = variable.replace("{", "").replace("}", "")
        if clean_var in boost_data["vars"]:
            value = boost_data["vars"][clean_var]
        else:
            # TODO: if variable was not declated on boost file, load it from environment vars
            pass
        storage[variable] = value
    return storage


def main() -> int:
    """Main function"""
    init(autoreset=True)

    parser = init_parser()
    args = parser.parse_args()

    boost_data = validate_boost()
    if "error" in boost_data:
        print(Fore.RED + boost_data["error"])
        return 1

    if not args.boost:
        # if not boost operation was specified, use first one
        boost = next(iter(boost_data["boost"]))
    else:
        boost = args.boost
    variables = re.findall("{.*}", boost_data["boost"][boost])
    commands = boost_data["boost"][boost].split("\n")[:-1]

    storage = get_storage(boost_data, variables)
    for cmd in commands:
        variables = re.findall("{.*}", cmd)
        for var in variables:
            cmd = cmd.replace(var, storage[var])
        cmd, *args = cmd.split(" ")
        call_command(cmd, args)
    return 0


BOOST_FILE = Path("boost.yaml")

if __name__ == "__main__":
    sys.exit(main())
