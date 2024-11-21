"""CLI query command controller."""

from argparse import ArgumentParser, Namespace
from functools import partial
from typing import Dict, Iterator, List, cast

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

from altadb.common.constants import EXPORT_PAGE_SIZE
from altadb.config import config
from altadb.cli.dataset import CLIDataset
from altadb.cli.cli_base import CLIQueryInterface
from altadb.utils.pagination import PaginationIterator


class CLIQueryController(CLIQueryInterface):
    """CLI list command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize list sub commands."""
        parser.add_argument("dataset", help="Dataset name")
        parser.add_argument(
            "-c",
            "--concurrency",
            type=int,
            default=EXPORT_PAGE_SIZE,
            help=f"Number of files to fetch in a single call. (Default: {EXPORT_PAGE_SIZE})",
        )
        parser.add_argument(
            "-n",
            "--number",
            type=int,
            default=EXPORT_PAGE_SIZE,
            help=f"Maximum number of files to query. (Default: {EXPORT_PAGE_SIZE})",
        )
        parser.add_argument(
            "-s",
            "--search",
            type=str,
            default=None,
            help="Search Term to filter matching Series, Study or Import data.",
        )
        cli_dataset = CLIDataset("")
        self.cli_dataset = cast(CLIDataset, cli_dataset)

    def handler(self, args: Namespace) -> None:
        """Handle list command."""
        self.args = args
        self.handle_query()

    def get_data_store_series(
        self, *, dataset_name: str, search: str, page_size: int, limit: int
    ) -> Iterator[Dict[str, str]]:
        """Get data store series."""
        my_iter = PaginationIterator(
            partial(
                self.cli_dataset.context.dataset.get_data_store_import_series,
                self.cli_dataset.creds.org_id,
                dataset_name,
                search,
            ),
            concurrency=page_size,
            limit=limit,
        )

        for ds_import_series in my_iter:
            yield ds_import_series

    def handle_query(self) -> None:
        """Handle query command."""
        # pylint: disable=too-many-locals
        cli_dataset = CLIDataset(self.args.dataset)

        if not self.cli_dataset.context.dataset.check_if_exists(
            org_id=cli_dataset.creds.org_id, dataset_name=cli_dataset.dataset.name
        ):
            raise ValueError("Dataset does not exist.")
        entries: List = []
        for ds_import_series in self.get_data_store_series(
            dataset_name=cli_dataset.dataset.name,
            search=self.args.search,
            page_size=self.args.concurrency,
            limit=self.args.number,
        ):
            entries.append(ds_import_series)
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
                if len(entries) < self.args.number:
                    console.print(
                        "[bold yellow]Dataset has no more entries with the search parameters."
                    )
