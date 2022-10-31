# Boost
Boost is a simple build system that aims to create an interface for shell command substitution across different operative systems. Boost tries to centralize build steps on different development environments.

Boost adds a simple way to add custom commands with different behaviours for different platforms.

## Commands
A command is a group of functions which determines the behaviour of an action on different environments. A command needs to implement these functions:
- `generic_exec(args: List[str]) -> dict`: function if the code is the same across multiple platforms or
- `win_exec(args: List[str]) -> dict`: for Windows commands.
- `posix_exec(args: List[str]) -> dict`: for Posix commands.

Currently, commands files under cmd package which implement above deffined functions can be automatically used by its file name. For example, `boost.cmd.delete` can be used inside any `boost.yaml` `boost` targets by using the keyword `delete`.

## Using Boost
To use Boost, first, create a `boost.yaml` file in your project directory. This is an example of a simple boost file.

```yaml
vars:
  file: example.txt
  current_dir: exec pwd
boost:
  dev: |
    delete {file}
    asd {current_dir}
```
- `vars`: Define key-value pairs representing variables that needs to be used inside boost targets. If a variable needs to store the output from a command, use `exec` followed by the commands that needs to be captured.
- `boost`: Define key-value pairs named boost targets. Target key will be used to call that specific target. Value contains a list of commands separated by `\n` that will be triggered when calling a specific target.
If a value needs to use a variable, use `$` followed by the variable name that was previously declared on `vars` section.

To call a boost target, run `boost <TARGET>`. If no boost target was specified, boost will use the first defined target.

## Developing boost
Requirements:
  - poetry

Run `poetry install`. Whit the previous command, you can run `poetry run boost` to test boost, boost command does automatically trigger `boostbuild.main:main` function.
