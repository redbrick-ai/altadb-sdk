"""CLI Base Classes/Interfaces for AltaDB."""

from abc import ABC, abstractmethod
from argparse import Namespace


class AbstractCLI(ABC):
    args: Namespace

    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError


class CLIConfigInterface(AbstractCLI):
    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_config(self) -> None:
        """Handle the CLI config command."""
        raise NotImplementedError


class CLIListInterface(AbstractCLI):
    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_list(self) -> None:
        """Handle the CLI list command."""
        raise NotImplementedError


class CLIQueryInterface(AbstractCLI):
    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_query(self) -> None:
        """Handle the CLI query command."""
        raise NotImplementedError


class CLIUploadInterface(AbstractCLI):
    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_upload(self) -> None:
        """Handle the CLI upload command."""
        raise NotImplementedError


class CLICreateInterface(AbstractCLI):
    @abstractmethod
    def handler(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError

    @abstractmethod
    def handle_create(self) -> None:
        """Handle the CLI create datastore command."""
        raise NotImplementedError


class CLIInterface(ABC):
    """Main interface for the CLI."""

    config: CLIConfigInterface
    upload: CLIUploadInterface
    list: CLIListInterface
    query: CLIQueryInterface
    create: CLICreateInterface

    CONFIG = "config"
    UPLOAD = "upload"
    LIST = "list"
    QUERY = "query"
    CREATE = "create"

    @abstractmethod
    def handle_command(self, args: Namespace) -> None:
        """Handle the CLI command."""
        raise NotImplementedError
