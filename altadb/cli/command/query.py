"""CLI query command controller."""

from argparse import ArgumentParser, Namespace
from typing import cast

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

from altadb.config import config
from altadb.cli.dataset import CLIDataset
from altadb.cli.cli_base import CLIQueryInterface


class CLIQueryController(CLIQueryInterface):
    """CLI list command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize list sub commands."""
        parser.add_argument("dataset", help="Dataset name")
        parser.add_argument(
            "-n",
            "--number",
            type=int,
            default=20,
            help="Number of rows to display",
        )
        cli_dataset = CLIDataset("")
        self.cli_dataset = cast(CLIDataset, cli_dataset)

    def handler(self, args: Namespace) -> None:
        """Handle list command."""
        self.args = args
        self.handle_query()

    def handle_query(self) -> None:
        """Handle query command."""
        # pylint: disable=too-many-locals
        dataset = self.args.dataset
        number = self.args.number
        cli_dataset = CLIDataset("")

        if not self.cli_dataset.context.dataset.check_if_exists(
            org_id=cli_dataset.creds.org_id, dataset_name=dataset
        ):
            raise ValueError("Dataset does not exist.")
        entries, end_cursor = (
            self.cli_dataset.context.dataset.get_data_store_import_series(
                org_id=cli_dataset.creds.org_id,
                data_store=dataset,
                first=number,
            )
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
        if entries:
            keys = list(entries[0].keys())
            keys = list(set(keys) - set(mask_items))
            keys = [
                "seriesId",
                "importId",
                "createdBy",
                "numFiles",
            ]
            # Add table headers by adding columns
            table.add_column("Index", style="bold")
            for key in keys:
                table.add_column(key, style="bold")
            for index, item in enumerate(entries):
                row = []
                for key in keys:
                    value = item[key]
                    if key in cipher_items:
                        if value.startswith("API:"):
                            _val = str(value)[:10] + "*" * (len(str(value)) - 6)
                            row.append(_val)
                        else:
                            row.append(value)
                    elif key not in mask_items:
                        row.append(value)
                table.add_row(str(index + 1), *[str(i) for i in row])
            if config.log_info:
                console.print(table)
                console.print("Dataset queried successfully.")
                if len(entries) < number or not end_cursor:
                    console.print("[bold yellow]Dataset has no more entries.")
