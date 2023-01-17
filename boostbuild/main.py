"""Main module."""
import sys
import importlib
from pathlib import Path
import argparse
import os
import re
import signal
from typing import List

from colorama import init, Fore

from boostbuild.validation import validate_boost_file


def init_parser() -> argparse.ArgumentParser:
    """Initialize argument parser.

    returns:
        - ArgumentParser with configured arguments.
    """
    parser = argparse.ArgumentParser(
        prog="Boost",
        description="Boost is a simple build system that aims to create an interface \
            for shell command substitution across different operative systems.",
    )
    parser.add_argument("target", type=str, help="Boost target", nargs="?", default="")
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Boost file path",
        default=Path(DEFAULT_BOOST_FILE),
    )
    return parser


def call_command(cmd: str, args: List[str], capture_output=False) -> dict:
    """Execute given command.

    Given command is dyanmically imported from cmd module.
    If module is not found, we will be opnening a shell an executing the command
    directly.

    params:
        - cmd: command that needs to be executed.
        - args: command arguments.
        - capture_output: capture output of executed command on stdout and stderr.

    returns:
        - dict containing executed command output on output key or error on error key.
    """
    try:
        command = importlib.import_module(f"boostbuild.cmd.{cmd}")
    except ModuleNotFoundError:
        # In case the command does not exist on Boost ecosystem, call unkown command.
        # unkown command does also need to know required command, this is why we are
        # adding cmd to args at 0 index.
        command = importlib.import_module("boostbuild.cmd.unkown")
        args.insert(0, cmd)

    # validate if command has implement a generic execution
    if hasattr(command, "generic_exec"):
        return command.generic_exec(args, capture_output)

    # command has different behaviour for windows/posix
    os_to_function = {"nt": "win_exec", "posix": "posix_exec"}
    try:
        call = os_to_function[os.name]
        return getattr(command, call)(args, capture_output)
    except KeyError:
        return {"error": "unsuported OS"}


def get_storage(boost_data: dict, variables: List[str]) -> dict:
    """Store commands variables.

    From list of required variables, store on a dictionary each variable key and value.

    params:
        - boost_data: yaml parsed boost file.
        - variables: list of required variables to store.

    returns:
        - dict containing all stored variables for commands use or dict containing error key on case
        there was an error building the storage.
    """
    storage = {}
    for variable in variables:
        value = ""
        clean_var = variable.replace("{", "").replace("}", "")
        if "vars" in boost_data and clean_var in boost_data["vars"]:
            if boost_data["vars"][clean_var].startswith("exec "):
                cmd, *args = (
                    boost_data["vars"][clean_var].replace("exec ", "").split(" ")
                )
                cmd_output = call_command(cmd, args, True)
                if "error" in cmd_output and cmd_output["error"]:
                    return cmd_output
                value = cmd_output["output"]
            else:
                value = boost_data["vars"][clean_var]
        else:
            # variables are already validated that exists on vars section or on
            # OS environment variable so it is safe to get it
            value = os.environ[clean_var]
        storage[variable] = value
    return storage


def handler(_signum, _frame):
    """
    Handle CTRL-C so the exit signal is sent to the process being executed by boost rather that to boost itself
    TODO: can we maybe handle multiple signals to send to boost itself.
    """


def main() -> int:
    """Main function"""
    init(autoreset=True)
    signal.signal(signal.SIGINT, handler)

    parser = init_parser()
    args = parser.parse_args()

    boost_data = validate_boost_file(args.file)
    if "error" in boost_data:
        print(Fore.RED + boost_data["error"])
        return 1

    if not args.target:
        # if not boost target was specified, use first one
        target = next(iter(boost_data["boost"]))
    else:
        target = args.target

    variables = re.findall("{.*?}", boost_data["boost"][target])
    commands = boost_data["boost"][target].strip().split("\n")
    total_commands = len(commands)
    print(Fore.CYAN + f"Boosting {target} - {total_commands} commands")

    storage = get_storage(boost_data, variables)
    if "error" in storage:
        print(Fore.RED + storage["error"])
        return 1

    for i, cmd in enumerate(commands):
        variables = re.findall("{.*?}", cmd)
        clean_cmd = cmd
        for var in variables:
            print_value = "****"
            if "secret" not in var:
                print_value = storage[var]
            # command containing secret vars values
            cmd = cmd.replace(var, storage[var])
            # command containing secret vars replaced values for printing
            clean_cmd = clean_cmd.replace(var, print_value)

        print(Fore.GREEN + f"-> [{i + 1}/{total_commands}] - {clean_cmd}")
        cmd, *args = cmd.split(" ")
        call_command(cmd, args)
    return 0


DEFAULT_BOOST_FILE = "boost.yaml"

if __name__ == "__main__":
    sys.exit(main())
