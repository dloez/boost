"""Utilities to generate a context from a Boost file.
"""
import os
import re
import importlib
import yaml
from pathlib import Path

from boostbuild.errors import build_error_hinting
from boostbuild.errors import FILE_FOLDER_DOESNT_EXIST, UNSUPORTED_OS
from boostbuild.errors import (
    MISSING_BOOST_SECTION,
    MISSING_VARS_SECTION,
    MISSING_TARGET,
    MISSING_VARIABLE,
    EMPTY_BOOST_SECTION,
    EMPTY_VARS_SECTION,
)


class Variable:
    """Represent a boost variable required by a command."""

    def __init__(self, name: str, value: str, attributes: str) -> None:
        """
        Arguments:
            - name: variable name.
            - value: variable content, it can be a command that needs to be executed to get its value.
            - attributes: variable attributes like `secret`.
        """
        self.name = name
        self.value = value
        self.attributes = attributes

    def get_value(self, secret: bool = False) -> str:
        """
        Arguments:
            - secret: if a variable has the `secret` attribute, force it to use it. Defaults to `False`.
        """
        if secret and "secret" in self.attributes:
            return "*****"
        return self.value


class Command:
    """Represent a boost target command."""

    def __init__(self, command: str, variables: dict, args: list) -> None:
        """
        Arguments:
            - command: command string.
            - variables: dictionary containing required command `Variable`s.
            - args: command arguments list.
        """
        self.command: str = command
        self.variables: dict = variables
        self.args: list = args

    def call(self, capture_output: bool = False) -> dict:
        """
        Call command.

        Arguments:
            - capture_output: bool as True if the command output needs to be captured, False otherwise.
            Defaults to False.
        """
        try:
            command = importlib.import_module(f"boostbuild.cmd.{self.command}")
        except ModuleNotFoundError:
            # In case the command does not exist on Boost ecosystem, call unkown command.
            # unkown command does also need to know required command, this is why we are
            # adding cmd to args at 0 index.
            command = importlib.import_module("boostbuild.cmd.unkown")
            self.args.insert(0, self.command)

        # get arguments with variables replaced
        args = self.get_arguments()

        # validate if command has implement a generic execution
        if hasattr(command, "generic_exec"):
            return command.generic_exec(args, capture_output)

        # command has different behaviour for windows/posix
        os_to_function = {"nt": "win_exec", "posix": "posix_exec"}
        try:
            call = os_to_function[os.name]
            return getattr(command, call)(args, capture_output)
        except KeyError:
            return {"error": UNSUPORTED_OS.format(command)}

    def get_arguments(self, secret: bool = False) -> list:
        """
        Read command arguments and find all variables, this is done by looking for '{variable}' strings on the
        arguments. Then replace all found variables by their values.

        Arguments:
            - secret: if a variable has the `secret` attribute, force it to use it. Defaults to `False`.

        Returns:
            - list containing command arguments with variables replaces by their values.
        """
        replaced_variables = []
        for arg in self.args:
            value: str = arg

            # check if argument is a variable
            if value.startswith("{") and value.endswith("}"):
                value = self.variables[value[1:-1]].get_value(secret)
            replaced_variables.append(value)
        return replaced_variables

    def __str__(self) -> str:
        return f"{self.command} {' '.join(self.get_arguments(secret=True))}"


def load_context(boost_file: Path, boost_target: str = "") -> dict:
    """
    Generate boost context from the given Boost file.
    Boost context is a dictionary containing all the information required to execute a target like
        - variables
        - commands and arguments

    Arguments:
        - boost_file: `boost.yaml` file.
        - boost_target: boost target that contains the commands that need to be executed.
    """
    context = {}

    # run previous validations to start parsing commands
    # validate that Boost file exists
    if not boost_file.exists():
        context["error"] = FILE_FOLDER_DOESNT_EXIST.format(boost_file)
        return context

    # load file
    with open(boost_file, "r", encoding="utf8") as handler:
        boost_data = yaml.load(handler, Loader=yaml.SafeLoader)

    # check boost section
    if "boost" not in boost_data:
        context["error"] = MISSING_BOOST_SECTION
        return context

    # check empty boost section
    if not boost_data["boost"]:
        context["error"] = EMPTY_BOOST_SECTION
        return context

    # check given boost target
    if not boost_target:
        boost_target = list(boost_data["boost"].keys())[0]
    elif boost_target not in boost_data["boost"]:
        context["error"] = MISSING_TARGET.format(boost_target)
        return context

    context["target"] = boost_target
    str_commands: str = boost_data["boost"][boost_target].strip().split("\n")
    general_variables: dict = {}
    commands: list = []
    for str_cmd in str_commands:
        # now that we know that the boost target commands require variables, check if vars section
        # exists on the boost file.
        if "vars" not in boost_data:
            context["error"] = MISSING_VARS_SECTION
            return context

        if not boost_data["vars"]:
            context["error"] = EMPTY_VARS_SECTION
            return context

        str_variales = re.findall("(?<={)(.*?)(?=})", str_cmd)
        command_variables: dict = {}
        for str_var in str_variales:
            if str_var in general_variables:
                command_variables[str_var] = general_variables[str_var]
                continue

            found_variable = next(
                (var for var in boost_data["vars"] if str_var in var), None
            )
            if not found_variable:
                context["error"] = build_error_hinting(
                    error=str_cmd,
                    position=str_cmd.index("{" + str_var + "}") + 1,
                    message=MISSING_VARIABLE.format(str_var),
                )
                return context

            attributes = ""
            if "attributes" in found_variable:
                attributes = found_variable["attributes"]
            variable = Variable(str_var, found_variable[str_var], attributes)
            general_variables[str_var] = variable
            command_variables[str_var] = variable

        str_cmd = str_cmd.split(" ")
        command = Command(
            command=str_cmd[0], variables=command_variables, args=str_cmd[1:]
        )
        commands.append(command)

    context["vars"] = general_variables
    context["commands"] = commands
    return context
