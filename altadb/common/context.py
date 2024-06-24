"""Container for low-level methods to communicate with API."""

from typing import Optional

from altadb.config import config


class AltaDBContext:
    """Basic context for accessing low level functionality."""

    def __init__(self, api_key: str, secret: str, url: str) -> None:
        """Construct AltaDB client singleton."""
        # pylint: disable=import-outside-toplevel
        from .client import AltaDBClient
        from .upload import UploadControllerInterface
        from .dataset import DatasetRepoInterface

        self.config = config
        self.client = AltaDBClient(api_key=api_key, secret=secret, url=url)

        self.upload: UploadControllerInterface
        self.dataset: DatasetRepoInterface

        self._key_id: Optional[str] = None

    def __str__(self) -> str:
        """Get string representation."""
        return repr(self) + (
            "***" + self.client.api_key[-3:] if self.client.api_key else ""
        )

    @property
    def key_id(self) -> str:
        """Get key id."""
        if not self._key_id:
            key_id: str = self.dataset.get_current_user()["userId"]
            self._key_id = key_id
        return self._key_id
