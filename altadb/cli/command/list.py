from argparse import ArgumentParser, Namespace
from altadb.cli.cli_base import CLIListInterface
from altadb.cli.dataset import CLIDataset
from altadb.repo.dataset import DatasetRepo

from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED


class CLIListController(CLIListInterface):
    """CLI list command controller."""

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize list sub commands."""
        parser.add_argument("dataset", help="Dataset name")

    def handler(self, args: Namespace) -> None:
        self.args = args
        dataset = args.dataset
        dataset = CLIDataset(required=False)
        context = dataset.context
        org_id = dataset.creds.org_id
        # dataset.initialize_project(
        #     RBOrganization(context, dataset.creds.org_id),
        #     AltaDBDataset(context, org_id, dataset),
        # )
        print("org: ", dataset.creds.org_id)
        print(dataset.context.client.api_key)
        print(dataset.context.client.secret_key)
        print(dataset.context.client.url)
        print(dataset._org)
        datasets = DatasetRepo(client=dataset.context.client).get_datasets(
            org_id=org_id
        )
        print(datasets)
        console = Console()
        table = Table(
            title="Datasets",
            box=ROUNDED,
            show_lines=True,
            show_edge=False,
            expand=True,
        )
        mask_out = [
            "importStatuses",
            "createdBy",
            "createdAt",
            "updatedAt",
        ]
        datasets = [
            {k: v for k, v in dataset.items() if k not in mask_out}
            for dataset in datasets
        ]
        # Pick the first item to get the header
        table.add_column("Index", justify="center")
        for key in datasets[0].keys():
            table.add_column(key)
        for index, dataset in enumerate(datasets):
            table.add_row(
                f"[bold]{index + 1}[/bold]",
                *dataset.values(),
                style="dim",
            )
        console.print(table)

    def handle_list(self) -> None:
        """Handle list command."""
        pass
