"""CLI upload command."""

import os
import asyncio
from argparse import ArgumentParser, Namespace
from typing import cast

from altadb.cli.dataset import CLIDataset
from altadb.cli.cli_base import CLIUploadInterface


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
            default=50,
            help="Concurrency value (Default: 50)",
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        project = CLIDataset(required=False)
        self.project = cast(CLIDataset, project)
        self.org_id = project.creds.org_id
        self.dataset_name = args.dataset
        self.handle_upload()

    def handle_upload(self) -> None:
        """Handle empty sub command."""
        path = os.path.realpath(self.args.path)

        asyncio.run(
            self.project.project.upload.upload_files(
                self.dataset_name, path, self.args.name or None, self.args.concurrency
            )
        )
