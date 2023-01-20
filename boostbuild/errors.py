"""Boost errors definitions."""


def build_error_hinting(error, position, message) -> str:
    """Build error hinting

    This functions returns a string with basic error hinting. Ex:
    ```
    variable: exec exec pwd
    ---------------^-------
    multiple exec instructions on a single variable are not allowed
    ```

    params:
        - error: str which contains the error.
        - position: character where the error is located.
        - message: error message which should be printed out with.

    returns:
        - string containing error and hinting, similar to above example.
    """
    error += "\n"
    for i in range(len(error.strip())):
        if i != position:
            error += "-"
            continue
        error += "^"
    error += f"\n{message}"
    return error


FILE_FOLDER_DOESNT_EXIST = "the given file/folder '{}' does not exist"
MISSING_BOOST_SECTION = "the used boost.yaml file does not have a 'boost' section"
MISSING_VARS_SECTION = "the used boost.yaml file does not have a 'vars' section and you are trying to use variables"
EMPTY_BOOST_SECTION = "the used boost.yaml file 'boost' section is empty"
EMPTY_VARS_SECTION = "the used boost.yaml file 'vars' section is empty and you are trying to use variables"
MISSING_TARGET = "the used boost target '{}' is missing on the 'boost' section"
MISSING_VARIABLE = "the variable '{}' is missing on the 'vars' section"
UNSUPORTED_OS = "the command '{}' does not support the current used OS"
