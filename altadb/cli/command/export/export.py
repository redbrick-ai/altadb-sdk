"""CLI export command."""

from argparse import ArgumentParser, Namespace

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
            help="The folder containing files to upload to the project",
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

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        self.cli_dataset = CLIDataset(self.args.dataset)
        self.handle_export()

    def handle_export(self) -> None:
        """Handle empty sub command."""
        path = self.args.path
        ignore_existing = self.args.clear_cache
        self.cli_dataset.export(path, ignore_existing)
