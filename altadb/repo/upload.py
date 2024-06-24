"""Handlers to access APIs for getting projects."""

from typing import List, Dict, Optional, Tuple

from altadb.common.client import AltaDBClient
from altadb.common.upload import UploadControllerInterface


class UploadRepo(UploadControllerInterface):
    """Class to manage interaction with upload APIs."""

    def __init__(self, client: AltaDBClient) -> None:
        """Construct Upload."""
        self.client = client

    def import_files(
        self,
        org_id: str,
        data_store: str,
        import_name: Optional[str] = None,
        import_id: Optional[str] = None,
        files: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, List[str]]:
        """Import files into a dataset."""
        files = files or []
        if not any([import_id, import_name]):
            raise ValueError("Either import_id or import_name must be provided")
        query_string = """
            mutation importFiles($orgId: UUID!, $dataStore: String!, $files: [ImportJobFileInput!]!, $importName: String, $importId: UUID) {
                importFiles(orgId: $orgId, dataStore: $dataStore, files: $files, importName: $importName, importId: $importId) {
                    dataStoreImport {
                       importId
                    }
                    urls
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStore": data_store,
            "files": files,
            "importName": import_name,
            "importId": import_id,
        }
        result: Dict = self.client.execute_query(query_string, query_variables)
        return (
            result["importFiles"]["dataStoreImport"]["importId"],
            result["importFiles"]["urls"],
        )

    def process_import(
        self,
        org_id: str,
        data_store: str,
        import_id: str,
        total_files: int,
    ) -> bool:
        """Process import."""
        query_string = """
            mutation processImport($orgId: UUID!, $dataStore: String!, $importId: UUID!, $totalFiles: Int) {
                processImport(orgId: $orgId, dataStore: $dataStore, importId: $importId, totalFiles: $totalFiles) {
                    ok
                    message
                }
            }
            """
        query_variables = {
            "orgId": org_id,
            "dataStore": data_store,
            "importId": import_id,
            "totalFiles": total_files,
        }
        result = self.client.execute_query(query_string, query_variables)
        return bool(result["processImport"]["ok"])
