# Boost
Boost is a simple build system that aims to create an interface for shell command substitution across different operative systems while keeping a simple interface. Boost tries to centralize build steps on different development environments.

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
