"""Create command controller."""

from argparse import ArgumentParser, Namespace

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

from altadb.cli.cli_base import CLICreateInterface
from altadb.cli.dataset import CLIDataset
from altadb.config import config
from altadb.repo.dataset import DatasetRepo


class CLICreateController(CLICreateInterface):
    """CLI list command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize list sub commands."""
        parser.add_argument("dataset", help="Dataset name")

    def handler(self, args: Namespace) -> None:
        """Handle controller."""
        self.args = args
        self.handle_create()

    def handle_create(self) -> None:
        """Handle create command."""
        cli_dataset = CLIDataset()
        ds_repo = DatasetRepo(client=cli_dataset.context.client)
        if ds_repo.check_if_exists(
            org_id=cli_dataset.creds.org_id, dataset_name=self.args.dataset
        ):
            raise ValueError("Dataset already exists.")
        status = ds_repo.create_dataset(
            org_id=cli_dataset.creds.org_id,
            dataset_name=self.args.dataset,
        )
        console = Console()
        table = Table(box=ROUNDED)
        # Display the dataset keys in left and values in right
        mask_items = [
            "importStatuses",
        ]
        cipher_items = [
            "createdBy",
        ]
        # Add table headers
        table.add_column("Key", style="bold")
        table.add_column("Value")
        for key, value in status.items():
            if key in cipher_items:
                if value.startswith("API:"):
                    _val = str(value)[:10] + "*" * (len(str(value)) - 6)
                    table.add_row(key, _val)
            elif key not in mask_items:
                table.add_row(key, value)
        if config.log_info:
            console.print(table)
            console.print("Dataset created successfully.")
