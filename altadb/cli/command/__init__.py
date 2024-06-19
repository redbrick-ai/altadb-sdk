"""CLI commands controllers."""

from altadb.cli.command.config import CLIConfigController
from altadb.cli.command.upload import CLIUploadController
from altadb.cli.command.list import CLIListController


__all__ = [
    "CLIConfigController",
    "CLIUploadController",
    "CLIListController",
]
