"""CLI Base Classes/Interfaces for AltaDB."""

from abc import ABC, abstractmethod
from typing import Optional
from argparse import Namespace

from altadb.cli.dataset import CLIDataset
from altadb.utils.logging import logger


class AbstractCLI(ABC):
    """Abstract CLI class."""

    args: Namespace

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError


class CLIListInterface(AbstractCLI):
    """CLI List Interface."""

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_list(self) -> None:
        """Handle the CLI list command."""
        raise NotImplementedError


class CLIQueryInterface(AbstractCLI):
    """CLI Query Interface."""

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_query(self) -> None:
        """Handle the CLI query command."""
        raise NotImplementedError


class CLICreateInterface(AbstractCLI):
    """CLI Create Interface."""

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_create(self) -> None:
        """Handle the CLI create datastore command."""
        raise NotImplementedError


class CLIInputParams(ABC):
    """CLI Input params handler."""

    entity: Optional[str]
    error_message: str

    @abstractmethod
    def filtrator(self, entity: str) -> str:
        """Filter input entity."""

    @abstractmethod
    def validator(self, entity: str) -> bool:
        """Validate input entity."""

    @abstractmethod
    def get(self) -> str:
        """Get filtered entity value post validation."""

    def from_args(self) -> Optional[str]:
        """Get value from cli args."""
        if self.entity is None:
            return None

        if self.validator(self.entity):
            return self.filtrator(self.entity)

        logger.warning(self.error_message + " : " + self.entity)
        return None


class CLIConfigInterface(AbstractCLI):
    """CLI config command interface."""

    args: Namespace
    cli_dataset: CLIDataset

    LIST = "list"
    SET = "set"
    ADD = "add"
    REMOVE = "remove"
    CLEAR = "clear"
    VERIFY = "verify"
    EXPORT = "export"

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle config command."""

    @abstractmethod
    def handle_config(self) -> None:
        """Handle empty sub command."""

    @abstractmethod
    def handle_list(self) -> None:
        """Handle list sub command."""

    @abstractmethod
    def handle_set(self) -> None:
        """Handle set sub command."""

    @abstractmethod
    def handle_add(self) -> None:
        """Handle add sub command."""

    @abstractmethod
    def handle_remove(self) -> None:
        """Handle remove sub command."""

    @abstractmethod
    def handle_clear(self) -> None:
        """Handle clear sub command."""

    @abstractmethod
    def handle_verify(self, profile: Optional[str] = None) -> None:
        """Handle verify sub command."""


class CLIUploadInterface(AbstractCLI):
    """CLI upload interface."""

    args: Namespace
    cli_dataset: CLIDataset

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle upload command."""

    @abstractmethod
    def handle_upload(self) -> None:
        """Handle empty sub command."""


class CLIExportInterface(AbstractCLI):
    """CLI export interface."""

    args: Namespace
    cli_dataset: CLIDataset

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle export command."""

    @abstractmethod
    def handle_export(self) -> None:
        """Handle empty sub command."""


class CLIInterface(ABC):
    """Main CLI Interface."""

    config: CLIConfigInterface
    upload: CLIUploadInterface
    list: CLIListInterface
    export: CLIExportInterface

    CONFIG = "config"
    UPLOAD = "upload"
    LIST = "list"
    QUERY = "query"
    CREATE = "create"
    EXPORT = "export"

    @abstractmethod
    def handle_command(self, args: Namespace) -> None:
        """CLI command main handler."""
