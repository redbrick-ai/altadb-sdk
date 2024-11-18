"""CLI export command."""

from argparse import ArgumentParser, Namespace
from rich.console import Console

from altadb.cli.dataset import CLIDataset
from altadb.cli.cli_base import CLIExportInterface
from altadb.common.constants import MAX_CONCURRENCY


class CLIExportController(CLIExportInterface):
    """CLI export command controller."""

    org_id: str
    dataset_name: str

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize upload sub commands."""
        parser.add_argument(
            "dataset",
            help="Dataset name",
        )
        parser.add_argument(
            "path",
            help="The folder where you want to export the dataset",
        )
        parser.add_argument(
            "-c",
            "--concurrency",
            type=int,
            default=MAX_CONCURRENCY,
            help=f"Number of files to download in parallel per series. (Default: {MAX_CONCURRENCY})",
        )
        parser.add_argument(
            "-n",
            "--number",
            type=int,
            default=MAX_CONCURRENCY,
            help=f"Number of series to export in total. (Default: {MAX_CONCURRENCY})",
        )
        parser.add_argument(
            "-s",
            "--search",
            type=str,
            default=None,
            help="Search Term to filter matching Series, Study or Import data.",
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        self.cli_dataset = CLIDataset(self.args.dataset)
        self.handle_export()

    def handle_export(self) -> None:
        """Handle empty sub command."""
        path = self.args.path
        number = self.args.number
        page_size = self.args.concurrency
        search = self.args.search
        if number < page_size:
            console = Console()
            console.print(
                "[bold yellow][WARNING] Page size is less than concurrency value. Concurrency value set to page size.",
            )
            page_size = number
        self.cli_dataset.export(path, page_size, number, search)
