"""Handlers to access APIs for getting projects."""

import json
from typing import List, Dict, Optional

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
        files: List[Dict[str, str]] = [],
    ) -> Optional[Dict]:
        if not any([import_id, import_name]):
            raise ValueError("Either import_id or import_name must be provided")
        """Import files into a dataset."""
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
        return result

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

    def get_data_store_imports(
        self,
        org_id: str,
        data_store: str,
        first: int = 20,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get data store imports."""
        query_string = """
            query DataStoreImportSeries($orgId: UUID!, $dataStore: String!, $first: Int, $after: String) {
                dataStoreImportSeries(orgId: $orgId, dataStore: $dataStore, first: $first, after: $after) {
                    entries {
                        orgId
                        datastore
                        importId
                        seriesId
                        createdAt
                        createdBy
                        totalSize
                        numFiles
                        patientHeaders
                        studyHeaders
                        seriesHeaders
                        url
                    }
                    cursor
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStore": data_store,
            "first": first,
            "after": cursor,
        }
        result = self.client.execute_query(query_string, query_variables)
        return result["dataStoreImportSeries"]["entries"]
