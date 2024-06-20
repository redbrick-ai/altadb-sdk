"""Interface for getting basic information about a project."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DatasetRepoInterface(ABC):
    """Abstract interface to Project APIs."""

    @abstractmethod
    def check_if_exists(self, org_id: str, dataset_name: str) -> bool:
        """Check if dataset exists."""

    @abstractmethod
    def create_dataset(self, org_id: str, dataset_name: str) -> Dict:
        """Create a new dataset."""

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
    def get_data_store_imports(
        self,
        org_id: str,
        data_store: str,
        first: int = 20,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get data store imports."""
