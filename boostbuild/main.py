"""Main module."""
import sys
from pathlib import Path
import argparse
import signal
from colorama import init, Fore

from boostbuild.context import load_context
from boostbuild.signal_handler import SignalHandler


def init_parser() -> argparse.ArgumentParser:
    """Initialize argument parser.

    returns:
        - `ArgumentParser` with configured arguments.
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


def main() -> int:
    """Main function."""
    init(autoreset=True)

    signal_handler = SignalHandler()
    signal.signal(signal.SIGINT, signal_handler.handler)

    parser = init_parser()
    args = parser.parse_args()

    context = load_context(args.file, args.target)
    if "error" in context:
        print(Fore.RED + context["error"])
        return 1

    total_commands = len(context["commands"])
    print(Fore.CYAN + f'Boosting {context["target"]} - {total_commands} commands')
    for i, command in enumerate(context["commands"]):
        print(Fore.GREEN + f"-> [{i + 1}/{total_commands}] - {command}")
        command.call()
    return 0


DEFAULT_BOOST_FILE = "boost.yaml"
MAX_SIGINT_COUNT = 3

if __name__ == "__main__":
    sys.exit(main())
