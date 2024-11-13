"""CLI export command."""

from argparse import ArgumentParser, Namespace
from rich.console import Console

from altadb.cli.dataset import CLIDataset
from altadb.cli.cli_base import CLIExportInterface
from altadb.common.constants import MAX_UPLOAD_CONCURRENCY


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
            default=MAX_UPLOAD_CONCURRENCY,
            help=f"Concurrency value (Default: {MAX_UPLOAD_CONCURRENCY})",
        )
        parser.add_argument(
            "--clear-cache",
            action="store_true",
            help="Clear the cache before exporting",
        )
        parser.add_argument(
            "-p",
            "--page-size",
            type=int,
            default=50,
            help="Page size for the export (Default: 50)",
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        self.cli_dataset = CLIDataset(self.args.dataset)
        self.handle_export()

    def handle_export(self) -> None:
        """Handle empty sub command."""
        path = self.args.path
        ignore_existing = self.args.clear_cache
        page_size = self.args.page_size
        max_concurrency = self.args.concurrency
        if page_size < max_concurrency:
            console = Console()
            console.print(
                "[bold yellow][WARNING] Page size is less than concurrency value. Concurrency value set to page size.",
            )
            max_concurrency = page_size
        self.cli_dataset.export(
            path, ignore_existing, max_concurrency=max_concurrency, page_size=page_size
        )
