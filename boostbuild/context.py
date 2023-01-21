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
    SELF_VAR_REQUEST,
)


class Variable:
    """Represent a boost variable required by a command."""

    def __init__(
        self, name: str, value: str, attributes: str, inner_variables: list
    ) -> None:
        """
        Arguments:
            - name: variable name.
            - value: variable content, it can be a command that needs to be executed to get its value.
            - attributes: variable attributes like `secret`.
        """
        self.name = name
        self.value = value
        self.attributes = attributes
        self.inner_variables = inner_variables

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

        str_variables = re.findall("(?<={)(.*?)(?=})", str_cmd)
        command_variables: dict = {}
        for str_var in str_variables:
            variables = check_inner_variables(
                boost_data, general_variables, command_variables, str_var
            )

            # the storage proceadure on `command_variables` and `general_variables` is already handled inside
            # the `check_inner_variables` process so we just need to handle the errors backtrace
            for variable in variables:
                if isinstance(variable, str):
                    context["error"] = variable
                    return context

        str_cmd = str_cmd.split(" ")
        command = Command(
            command=str_cmd[0], variables=command_variables, args=str_cmd[1:]
        )
        commands.append(command)

    context["vars"] = general_variables
    context["commands"] = commands
    return context


def check_inner_variables(
    boost_data, general_variables, command_variables, variable_key: str
) -> list:
    """
    Recursively create new variables, this means that if the variable `variable_key`
    requests another variable, the function will call itself to load it repeating the process
    if the `variable_key` variable do also require another variable.

    All found variables are stored in `command_variables` and `general_variables`.

    Arguments:
        - `boost_data`: boost yaml file content.
        - `general_variables`: general varibales required by all the boost target commands.
        - `variable_key`: varible that needs to be created.

    Returns:
        - list of `Variable` or `str` where:
            - `Variable`: created variables.
            - `str`: error triggered while processing the creation process.
    """
    outputs = []
    # if variable was already allocated in `general_variables`, return it and skip the process
    # so the same `Variable` object can be shared with all variables with request it.
    if variable_key in general_variables:
        command_variables[variable_key] = general_variables[variable_key]
        outputs.append(general_variables[variable_key])
        return outputs

    # find `variable_key` on boost `vars` section
    found_variable = next(
        (var for var in boost_data["vars"] if variable_key in var), None
    )

    # if the varibale was not found, return the error `MISSING_VARIABLE`
    if not found_variable:
        outputs.append(MISSING_VARIABLE.format(variable_key))
        return outputs

    # if the variable value has more variables inside, call itself with the new found variables
    str_variables = re.findall("(?<={)(.*?)(?=})", found_variable[variable_key])
    for str_variable in str_variables:
        # check if variable is requesting itself, which will end up on an infinite loop
        if str_variable == variable_key:
            outputs.append(SELF_VAR_REQUEST.format(variable_key))
            return outputs

        inner_variables = check_inner_variables(
            boost_data, general_variables, command_variables, str_variable
        )

        # check for errors on inner variables
        for inner_variable in inner_variables:
            if isinstance(inner_variable, str):
                # in case of error, add the current variable so we can generate a traceback
                # of which variable requested a missing one
                inner_variable += f" from {variable_key}"
                outputs.append(inner_variable)
                return outputs
            outputs.append(inner_variable)

    # load found variable attributes and create new variable with inner variables
    attributes = ""
    if "attributes" in found_variable:
        attributes = found_variable["attributes"]
    variable = Variable(
        name=variable_key,
        value=found_variable[variable_key],
        attributes=attributes,
        inner_variables=outputs,
    )
    # register variable on
    #   - `command_variables`: to store command required variables
    #   - `general_variables`: for resuse pourpouses
    command_variables[variable_key] = variable
    general_variables[variable_key] = variable
    outputs.append(variable)
    return outputs
