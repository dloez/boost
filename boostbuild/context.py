"""Utilities to generate a context from a Boost file."""
import os
import importlib
from pathlib import Path

from boostbuild.utils import find_variables_in
from boostbuild.validations import validate_boost_file, validate_boost_target
from boostbuild.errors import UNSUPORTED_OS

# pylint: disable=too-few-public-methods
class Variable:
    """Represent a boost variable required by a command."""

    def __init__(
        self, name: str, value: str, attributes: str, inner_variables: dict
    ) -> None:
        """
        Arguments:
            - `name`: variable name.
            - `value`: variable content, it can be a command that needs to be executed to get its value.
            - `attributes`: variable attributes like `secret`.
            - `inner_variables`:
        """
        self.name = name
        self.value = value
        self.attributes = attributes
        self.inner_variables = inner_variables

    def get_value(self, secret: bool = False) -> str:
        """
        Arguments:
            - `secret`: if a variable has the `secret` attribute, force it to use it. Defaults to `False`.
        """
        if secret and "secret" in self.attributes:
            return "*****"

        if "exec" in self.attributes:
            str_cmd = self.value.split(" ")
            command = Command(str_cmd[0], self.inner_variables, str_cmd[1:])
            output = command.call(capture_output=True)
            return output["output"]

        variable = find_variables_in(self.value)
        if variable:
            return self.inner_variables[variable[0]].get_value(secret)

        return self.value


class Command:
    """Represent a boost target command."""

    def __init__(self, command: str, variables: dict, args: list) -> None:
        """
        Arguments:
            - `command`: command string.
            - `variables`: `dict` containing required command `Variable`s.
            - `args`: command arguments list.
        """
        self.command: str = command
        self.variables: dict = variables
        self.args: list = args

    def call(self, capture_output: bool = False) -> dict:
        """
        Call command.

        Arguments:
            - `capture_output`: `bool` as `True` if the command output needs to be captured, `False` otherwise.
                Defaults to `False`.
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
            - `secret`: if a variable has the `secret` attribute, force it to use it. Defaults to `False`.

        Returns:
            - `list` containing command arguments with variables replaces by their values.
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


def load_context(boost_file: Path, boost_target: str) -> dict:
    """
    Generate boost context from the given Boost file.
    Boost context is a dictionary containing all the information required to execute a target like
        - variables
        - commands and arguments

    Arguments:
        - `boost_file`: 'boost.yaml' file.
        - `boost_target`: boost target that contains the commands that need to be executed.
    """
    context = {}
    output = validate_boost_file(boost_file, boost_target)
    if isinstance(output, str):
        context["error"] = output
        return context

    boost_data: dict = output
    boost_target = validate_boost_target(boost_data, boost_target)
    context["target"] = boost_target
    str_commands: str = boost_data["boost"][boost_target].strip().split("\n")
    general_variables: dict = {}
    commands: list = []
    for str_cmd in str_commands:
        str_variables = find_variables_in(str_cmd)
        command_variables: dict = {}
        for str_var in str_variables:
            create_inner_variables(
                boost_data, general_variables, command_variables, str_var
            )

        str_cmd = str_cmd.split(" ")
        command = Command(
            command=str_cmd[0], variables=command_variables, args=str_cmd[1:]
        )
        commands.append(command)

    context["vars"] = general_variables
    context["commands"] = commands
    return context


def create_inner_variables(
    boost_data: dict,
    general_variables: dict,
    command_variables: dict,
    variable_key: str,
) -> Variable:
    """
    Recursively create new variables, this means that if the variable `variable_key`
    requests another variable, the function will call itself to load it repeating the process
    if the `variable_key` variable do also require another variable.

    All found variables are stored in `command_variables` and `general_variables`.

    Arguments:
        - `boost_data`: boost yaml file content.
        - `general_variables`: general varibales required by all the boost target commands.
        - `command_variables`: `dict` containing variables used by a certain command.
        - `variable_key`: varible that needs to be created.

    Returns:
        - `Variable` created with inner variables checked.
    """
    # if variable was already allocated in `general_variables`, return it and skip the process
    # so the same `Variable` object can be shared with all variables with request it
    if variable_key in general_variables:
        command_variables[variable_key] = general_variables[variable_key]
        return general_variables[variable_key]

    # find `variable_key` on boost `vars` section
    found_variable = next(var for var in boost_data["vars"] if variable_key in var)

    # if the variable value has more variables inside, call itself with the new found variables
    str_variables = find_variables_in(found_variable[variable_key])
    variables: dict = {}
    for str_variable in str_variables:
        inner_variable = create_inner_variables(
            boost_data, general_variables, command_variables, str_variable
        )
        variables[str_variable] = inner_variable

    # load found variable attributes and create new variable with inner variables
    attributes = ""
    if "attributes" in found_variable:
        attributes = found_variable["attributes"]
    variable = Variable(
        name=variable_key,
        value=found_variable[variable_key],
        attributes=attributes,
        inner_variables=variables,
    )
    # register variable on
    #   - `command_variables`: to store command required variables
    #   - `general_variables`: for resuse pourpouses
    command_variables[variable_key] = variable
    general_variables[variable_key] = variable
    return variable
