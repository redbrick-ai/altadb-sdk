from argparse import ArgumentParser, Namespace
from altadb.cli.cli_base import CLIQueryInterface
from altadb.cli.dataset import CLIDataset
from altadb.repo.dataset import DatasetRepo

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED


class CLIQueryController(CLIQueryInterface):
    """CLI list command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize list sub commands."""
        parser.add_argument("dataset", help="Dataset name")

    def handler(self, args: Namespace) -> None:
        print("Query command")

    def handle_query(self) -> None:
        print("Query command")
