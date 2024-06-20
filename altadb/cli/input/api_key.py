"""Input api_key handler."""

import re
from typing import Optional

from InquirerPy.prompts.input import InputPrompt

from altadb.cli.cli_base import CLIInputParams


class CLIInputAPIAccessKey(CLIInputParams):
    """Input api_key handler."""

    def __init__(self, entity: Optional[str]) -> None:
        """Init handlers."""
        self.entity = entity
        self.error_message = "Invalid API Key"

    def filtrator(self, entity: str) -> str:
        """Filter input entity."""
        return entity.strip()

    def validator(self, entity: str) -> bool:
        """Validate input entity."""
        api_key = self.filtrator(entity)
        return (
            len(api_key) == 40
            and api_key.startswith("API:")
            and re.match(r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$", api_key[4:])
            is not None
        )

    def get(self) -> str:
        """Get filtered api_key value post validation."""
        self.entity = self.from_args()
        if self.entity is None:
            self.entity = InputPrompt(
                qmark=">",
                amark=">",
                message="API Key:",
                transformer=self.filtrator,
                filter=self.filtrator,
                validate=self.validator,
                invalid_message=self.error_message,
            ).execute()
        return self.entity
