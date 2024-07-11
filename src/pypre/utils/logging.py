from __future__ import annotations

import logging
import sys
from copy import copy
from typing import Callable, ClassVar, Literal

import click


# Adapted from:
# https://github.com/encode/uvicorn/blob/6dcb6a6b9456c08d502373285e0c2bfd73d9c19e/uvicorn/logging.py
class ColourizedFormatter(logging.Formatter):
    """
    A custom log formatter class that:

    * Outputs the LOG_LEVEL with an appropriate color.
    * If a log call includes an `extras={"color_message": ...}` it will be used
      for formatting the output, instead of the plain text message.
    """

    level_name_colors: ClassVar[dict[int, Callable[[str], str]]] = {
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="bright_red"),
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool | None = None,
    ) -> None:
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
            recordcopy.__dict__["levelname"] = levelname
        return super().formatMessage(recordcopy)
