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
            "-p",
            "--page-size",
            type=int,
            default=MAX_CONCURRENCY,
            help=f"Number of series to export in parallel (Default: {MAX_CONCURRENCY})",
        )
        parser.add_argument(
            "-s",
            "--series",
            type=str,
            default=None,
            help="Series UUID to export. Exports all series if not provided.",
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        self.cli_dataset = CLIDataset(self.args.dataset)
        self.handle_export()

    def handle_export(self) -> None:
        """Handle empty sub command."""
        path = self.args.path
        page_size = self.args.page_size
        max_concurrency = self.args.concurrency
        series = self.args.series
        if page_size < max_concurrency:
            console = Console()
            console.print(
                "[bold yellow][WARNING] Page size is less than concurrency value. Concurrency value set to page size.",
            )
            max_concurrency = page_size
        self.cli_dataset.export(path, max_concurrency, page_size, series)
