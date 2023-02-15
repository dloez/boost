"""Boost errors definitions."""


def build_error_hinting(error, position, message) -> str:
    """Build error hinting

    This functions returns a string with basic error hinting. Ex:
    ```
    variable: exec exec pwd
    ---------------^-------
    multiple exec instructions on a single variable are not allowed
    ```

    Arguments:
        - `error`: `str` which contains the error.
        - `position`: character where the error is located.
        - `message`: error message which should be printed out with.

    Returns:
        - `str` containing error and hinting, similar to above example.
    """
    error += "\n"
    for i in range(len(error.strip())):
        if i != position:
            error += "-"
            continue
        error += "^"
    error += f"\n{message}"
    return error


UNSUPORTED_OS = "the command '{}' does not support the current used OS"

# validated on validations.py
FILE_FOLDER_DOESNT_EXIST = "the given file/folder '{}' does not exist"
MISSING_BOOST_SECTION = "the used boost.yaml file does not have a 'boost' section"
EMPTY_BOOST_SECTION = "the used boost.yaml file 'boost' section is empty"
MISSING_TARGET = "the used boost target '{}' is missing on the 'boost' section"
MISSING_VARIABLE = "the variable '{}' is missing on the 'vars' section and it was required by the '{}' '{}'"
SELF_VAR_REQUEST = "the variable '{}' is requesting itself, which is not allowed"
BAD_FORMAT_BOOST_SECTION = "the 'boost' section is bad formatted. It should contain key-value pairs \
where each key is a boost target and each value is a \\n separated list of commands for that \
specific boost target"
BAD_FORMAT_VARS_SECTION = "the 'vars' section is bad formatted. It should contain a list of objects with \
at least one key-value pair where the key will be used as the variable name and the value will \
will be used as the variabel value"
UNKOWN_KEY = "Unkown key '{}'"
UNSUPPORTED_VAR_ATTRIBUTE = "the attribute '{}' on the var '{}' is not supported"
BAD_FORMAT_ATTRIBUTES = "the attributes '{}' on the variable '{}' are bad formatted, they should be \
a comma-separated list of variable attributes"
NOT_ALLOWED_CHARACTERS = (
    "the '{}' '{}' has not-allowed caharacters, allowed characters: '{}'"
)
