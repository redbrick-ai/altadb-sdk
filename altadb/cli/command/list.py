from argparse import ArgumentParser, Namespace
from typing import Dict, List
from altadb import _populate_context
from altadb.cli.cli_base import CLIListInterface
from altadb.cli.dataset import CLIDataset

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

from altadb.common.context import AltaDBContext
from altadb.config import config
from altadb.dataset import AltaDBDataset


class CLIListController(CLIListInterface):
    """CLI list command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize list sub commands."""
        parser.add_argument(
            "-d",
            "--dataset",
            help="Dataset name",
            default=None,
            required=False,
        )

    def handler(self, args: Namespace) -> None:
        self.args = args
        toplevel = CLIDataset()
        context = toplevel.context
        org_id = toplevel.creds.org_id
        datasets: List[Dict] = context.dataset.get_datasets(org_id=org_id)
        console = Console()
        table = Table(
            title="Datasets",
            box=ROUNDED,
            show_lines=True,
        )
        mask_out = [
            "importStatuses",
            "createdBy",
            "createdAt",
            "updatedAt",
        ]
        datasets_details: List[Dict] = [
            {k: v for k, v in dataset.items() if k not in mask_out}
            for dataset in datasets
        ]
        # Pick the first item to get the header
        table.add_column("Index", justify="center")
        keys: List[str] = list(set(datasets_details[0].keys()) - set(mask_out))
        for key in keys:
            table.add_column(str(key))

        for index, dset in enumerate(datasets_details):
            if isinstance(dset, dict):
                table.add_row(
                    f"[bold]{index + 1}[/bold]",
                    *[str((dset).get(key) or "") for key in keys],
                    style="dim",
                )
        if config.log_info:
            console.print(table)

    def handle_list(self) -> None:
        """Handle list command."""
        pass
