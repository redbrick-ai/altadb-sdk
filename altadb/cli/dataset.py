"""Main CLI project."""

import os
from typing import Optional

from rich.console import Console

from altadb import _populate_context
from altadb.common.constants import MAX_CONCURRENCY
from altadb.config import config
from altadb.common.context import AltaDBContext
from altadb.organization import AltaDBOrganization
from altadb.dataset import AltaDBDataset
from altadb.cli.entity import CLICache, CLIConfiguration, CLICredentials
from altadb.utils.common_utils import config_path


class CLIDataset:
    """CLIDataset class."""

    path: str

    creds: CLICredentials
    conf: CLIConfiguration
    cache: CLICache

    _context: Optional[AltaDBContext] = None
    _org: Optional[AltaDBOrganization] = None
    altadb_dataset: Optional[AltaDBDataset] = None

    def __init__(self, dataset: str = "") -> None:
        """Initialize CLIProject."""
        self._creds_file = os.path.join(config_path(), "credentials")
        self.creds = CLICredentials(self._creds_file)
        self._dataset_name = dataset
        self._dataset: Optional[AltaDBDataset] = None

    @property
    def context(self) -> AltaDBContext:
        """Get AltaDB context."""
        if not self._context:
            self._context = _populate_context(self.creds.context)
        return self._context

    @property
    def org_id(self) -> str:
        """Get org_id of current project."""
        return self.creds.org_id

    @property
    def org(self) -> AltaDBOrganization:
        """Get org object."""
        if not self._org:
            console = Console()
            with console.status("Fetching organization") as status:
                try:
                    self._org = AltaDBOrganization(self.context, self.org_id)
                except Exception as error:
                    status.stop()
                    raise error
            if config.log_info:
                console.print("[bold green]" + str(self._org))
        return self._org

    @property
    def dataset(self) -> AltaDBDataset:
        """Get dataset object."""
        if not self._dataset:
            console = Console()
            with console.status("Fetching project") as status:
                try:
                    self._dataset = AltaDBDataset(
                        self.context, self.org_id, self._dataset_name
                    )
                except Exception as error:
                    status.stop()
                    raise error
            if config.log_info:
                console.print("[bold green]" + str(self._dataset))

        return self._dataset

    def export(
        self,
        path: str,
        page_size: int = MAX_CONCURRENCY,
        number: Optional[int] = None,
        search: Optional[str] = None,
    ) -> None:
        """Export files from dataset."""
        self.dataset.export_to_files(path, page_size, number, search)
