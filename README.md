## Project archived
This project aimed to be a research project for creating a multi-platform standard command runner with a single yaml file to define commands. During the research of this project, I focused on:
1. Easy to use: The user should be able to download a binary, add it to the path, and just use it. I was intending to use pyoxidizer for this purpose, but it would limit point 2.
2. User customizable: The user could create custom commands in Python. Allowing this feature while providing point 1 seems to be possible but very hacky/slow.
3. Standardized behaviors across multiple OS: The user should be able to write a command, like `rm` and it would be automatically translated into the required command/code depending on the os. This was mainly done by running the command logic using Python code, or by defining different functions that would be called depending on the OS. I like this, I think it would be very useful but the amount of effort to support enough commands to cover different use cases is noticeable, and I do not have the required time to do so.

This is what I found:
- Python is an excellent language but is really bad when you have to distribute an application, I did not realize how bad it is until this project. I think there are better-suited languages for this purpose.
- User simplicity comes at the cost of losing control of the execution. A not well-suited abstraction layer will not cover most of the user cases, not even a decent or usable part of them, and this is what I was starting to feel with the yaml file with custom commands.

With the above information, I came up with 2 solutions. One solution could be to keep the same idea but in a different language that would allow users to simply download a binary, and run the tool; I would really love to build this in the future (at least for the fun!).
The other idea, which is taken in a different direction and inspired by the fantastic go tool [Mage](https://github.com/magefile/mage), would be to have a tool that would allow the user to run functions defined in multiple languages. The user would have the choice to use a language supported by its required platforms which means that the user would rely on a language and its ecosystem for multiplatform support rather than in self-made commands. The tool would need to simplify how the underline language is called. For example, it would need to allow the user to define the `PYTHON_PATH` env variable to define which Python interpreter should run a Python function, or define the shell which should run a bash script. I will try this approach, and, I am currently working on [Arcanist](https://github.com/dloez/arcanist)!

Fantastic tools that I found during this research:
- [Just](https://github.com/casey/just): it is a Make inspired tool for running commands. It relies on Git Bash on Windows but you can control which shell is used for running the commands.
- [Mage](https://github.com/magefile/mage): run go functions within the cli.

# Boost
Boost is a simple command runner that aims to create an interface for shell command substitution across different operative systems while keeping a simple interface. Boost tries to centralize build steps on different development environments.

Boost adds a simple way to add custom commands with different behaviours for different platforms.

Warning: Boost follows semantic versioning and we are currently on 0.Y.Z version which means that the API will probably be modified on early stages and that boost does not have all the validations that we want to implement before the 1.0.0 release.

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
  - file: example.txt
  - current_dir: pwd
    attributes: exec
  - im_a_password: SUPER SECRET PASSWORD
    attributes: secret
boost:
  dev: |
    delete {file}
    echo {current_dir}
```
- `vars`: List of variable objects that a boost target needs to be executed. A variable needs a key that will act as the variable name, and a value for the variable value. Variables can also have an optional key called `attributes` to modify its behavour.
- `boost`: key-value pairs named boost targets. Target key will be used to call that specific target. Key value contains a list of commands separated by `\n` (yaml multi line strings) that will be triggered when calling a specific target.
If a value needs to use a variable, use `{VARIABLE KEY}` where `VARIABLE NAME` is the variable key decalred on the `vars` section. To call a boost target, run `boost <TARGET>`. If no boost target was specified, boost will use the first defined target. If a target only needs to run a single command, it can be written like a one line string on yaml:

  ```yaml
  boost:
    dev: echo I am a single command!!!
  ```

## Variables

Variables are a list of objects. Each object should have a key that will represent the variable name, and a value for its variable value. For example:

```yaml
vars:
  - variable_name: variable_value
```

Only variables required by the target specified will be loaded. So, in the following example, only the variable `foo` and `bar` will be loaded by the execution of `boost dev`:

```yaml
vars:
  foo: '{bar}'
  bar: im a value
  example: im not going to be loaded if the target build is not called :(
boost:
  dev: echo {foo}
  build: |
    echo {example}
    echo {bar}
```

Note that `bar` is loaded because it is required by `foo` which is the one beeing required by the target `dev`.

As you saw in the above example, variables can reference other variables with the same sytax `{VARIABLE}` but it is not allowed to reference themselves.

Variables are loaded when boost is initialized and currently their values cannot be modified. A new variable attribute to change this behaviour will be implemented to allow the re-execution of variables.

### Attributes
Variables can also have an optional key called `attributes`. Attributes modifies variable behaviour. The value of this key is a comma-separated list of attributes.

List of available attributes:
  - `secret`: Avoid a value of a variable to be printed when boost echoes each boost target command. The value will be replaced by `*****`. Note that for the moment this is not applied to the output of commands. Example:
    ```yaml
    vars:
      - password: super secret password
        attributes: secret
    ```
  - `exec`: Handle variable value as a command that needs to be executed to get the actual variable value. Example:
    ```yaml
    vars:
      - current_dir: pwd   # translated to the output of "pwd" when used
        attributes: exec
    ```

## Developing boost
Requirements:
  - poetry

Run `poetry install`. Whit the previous command, you can run `poetry run boost` to test boost or just `boost` if you run `poetry shell`. Boost command does automatically trigger `boostbuild.main:main` function.
More information about Poetry can be found at [their official documentation](https://python-poetry.org/docs/).
