from argparse import ArgumentParser, Namespace
from typing import cast
from altadb.cli.cli_base import CLIQueryInterface
from altadb.cli.dataset import CLIDataset

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

from altadb.config import config


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

    def handler(self, args: Namespace) -> None:
        self.args = args
        project = CLIDataset("")
        self.project = cast(CLIDataset, project)
        self.handle_query()

    def handle_query(self) -> None:
        dataset = self.args.dataset
        number = self.args.number
        cli_dataset = CLIDataset("")

        if not self.project.context.dataset.check_if_exists(
            org_id=cli_dataset.creds.org_id, dataset_name=dataset
        ):
            raise ValueError("Dataset does not exist.")
        status = self.project.context.dataset.get_data_store_imports(
            org_id=cli_dataset.creds.org_id,
            data_store=dataset,
            first=number,
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
        if status:
            keys = list(status[0].keys())
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
            for index, item in enumerate(status):
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
        return None
