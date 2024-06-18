"""Input url handler."""

from typing import Optional

from InquirerPy.prompts.input import InputPrompt

from altadb.cli.cli_base import CLIInputParams
from altadb.common.constants import DEFAULT_URL


class CLIInputURL(CLIInputParams):
    """Input url handler."""

    def __init__(self, entity: Optional[str]) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Invalid URL"

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip().rstrip("/")

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        url = self.filtrator(entity)
        return url.startswith("http") and " " not in url and url.count("://") == 1

    def get(self) -> str:
        """Get filtered url value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = InputPrompt(
                qmark=">",
                amark=">",
                message="URL:",
                default=DEFAULT_URL,
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
