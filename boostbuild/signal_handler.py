"""Utilities to handle process signals like SIGINT"""
import sys
import time
from colorama import Fore


# pylint: disable=too-few-public-methods
class SignalHandler:
    """Define handler for SIGINT"""

    # If two signals were deteted suring this time, stop boost
    ELAPSED_TIME = 1.5

    def __init__(self) -> None:
        self.last_signal: float = 0

    def handler(self, _signum, _frame) -> None:
        """
        Handle CTRL-C so the exit signal is sent to the process being executed by boost rather that to boost itself
        """
        if not self.last_signal:
            self.last_signal = time.time()
            return

        now = time.time()
        if now - self.last_signal <= 1.5:
            print(Fore.RED + "Boost stop signal detected!")
            sys.exit(1)
        self.last_signal = now
