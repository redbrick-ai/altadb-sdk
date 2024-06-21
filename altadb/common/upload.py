"""Abstract interface to upload."""

from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod


class UploadControllerInterface(ABC):
    """Abstract interface to define methods for Upload."""

    @abstractmethod
    def import_files(
        self,
        org_id: str,
        data_store: str,
        import_name: Optional[str] = None,
        import_id: Optional[str] = None,
        files: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, List[str]]:
        """Import files into a dataset."""

    @abstractmethod
    def process_import(
        self,
        org_id: str,
        data_store: str,
        import_id: str,
        total_files: int,
    ) -> bool:
        """Process import."""
