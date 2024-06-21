"""CLI upload command."""

import os
import asyncio
from argparse import ArgumentParser, Namespace

from altadb.cli.dataset import CLIDataset
from altadb.cli.cli_base import CLIUploadInterface
from altadb.common.constants import MAX_UPLOAD_CONCURRENCY


class CLIUploadController(CLIUploadInterface):
    """CLI upload command controller."""

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
            help="The path containing files to upload to the project",
        )
        parser.add_argument(
            "-n",
            "--name",
            help="Import name",
        )
        parser.add_argument(
            "-c",
            "--concurrency",
            type=int,
            default=MAX_UPLOAD_CONCURRENCY,
            help=f"Concurrency value (Default: {MAX_UPLOAD_CONCURRENCY})",
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        self.cli_dataset = CLIDataset(self.args.dataset)
        self.handle_upload()

    def handle_upload(self) -> None:
        """Handle empty sub command."""
        path = os.path.realpath(self.args.path)

        asyncio.run(
            self.cli_dataset.dataset.upload.upload_files(
                self.args.dataset,
                path,
                self.args.name or None,
                self.args.concurrency,
            )
        )
