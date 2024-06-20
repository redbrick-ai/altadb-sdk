"""Interface for getting basic information about a project."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DatasetRepoInterface(ABC):
    """Abstract interface to Project APIs."""

    @abstractmethod
    def get_project(self, org_id: str, project_id: str) -> Dict:
        """
        Get project name and status.

        Raise an exception if project does not exist.
        """

    @abstractmethod
    def get_org(self, org_id: str) -> Dict:
        """Get organization."""

    @abstractmethod
    def get_current_user(self) -> Dict:
        """Get current user."""

    @abstractmethod
    def self_health_check(
        self, org_id: str, self_url: str, self_data: Dict
    ) -> Optional[str]:
        """Send a health check update from the model server."""
