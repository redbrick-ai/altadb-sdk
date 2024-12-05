"""Handlers to access APIs for getting projects."""

from typing import List, Dict, Optional, Tuple

from altadb.common.client import AltaDBClient
from altadb.common.dataset import DatasetRepoInterface


class DatasetRepo(DatasetRepoInterface):
    """Class to manage interaction with dataset APIs."""

    def __init__(self, client: AltaDBClient) -> None:
        """Construct Dataset."""
        self.client = client

    def check_if_exists(self, org_id: str, dataset_name: str) -> bool:
        """Check if dataset exists."""
        query = """
        query sdkDataStore($orgId: UUID!) {
            dataStores(orgId: $orgId) {
                orgId
                name
                displayName
                createdAt
                createdBy
                status
                updatedAt
                importStatuses
            }
        }
        """
        variables = {"orgId": org_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        return any(
            dataset["displayName"] == dataset_name for dataset in response["dataStores"]
        )

    def create_dataset(self, org_id: str, dataset_name: str) -> Dict:
        """Create a new dataset."""
        query = """
            mutation sdkCreateDatastore($orgId: UUID!, $dataStore: String!, $displayName: String!) {
                createDatastore(orgId: $orgId, dataStore: $dataStore, displayName: $displayName) {
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }
            }
        """
        variables = {
            "orgId": org_id,
            "dataStore": dataset_name,
            "displayName": dataset_name,
        }
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        return response["createDatastore"]

    def get_project(self, org_id: str, project_id: str) -> Dict:
        """
        Get dataset name and status.

        Raise an exception if dataset does not exist.
        """
        query = """
            query sdkDataStore($orgId: UUID!, $name: String!) {
                dataStore(orgId: $orgId, name: $name) {
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }
            }
        """
        variables = {"orgId": org_id, "projectId": project_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        if response.get("project"):
            return response["project"]

        raise Exception("Dataset does not exist")

    def get_org(self, org_id: str) -> Dict:
        """Get organization."""
        query = """
            query sdkOrganization($orgId: UUID!) {
                organization(orgId: $orgId) {
                    orgId
                    name
                    desc
                    role
                    createdAt
                    status
                    idProviders
                }
            }
        """
        response: Dict[str, Dict] = self.client.execute_query(query, {"orgId": org_id})
        return response["organization"]

    def get_current_user(self) -> Dict:
        """Get current user."""
        query_string = """
        query currentUserSDK {
            me {
                userId
            }
        }
        """
        result = self.client.execute_query(query_string, {})
        current_user: Dict = result["me"]
        return current_user

    def get_data_store_imports(self, org_id: str, data_store: str) -> Tuple[Dict, str]:
        """Get data store import."""
        query_string = """
            query dataStoreImports($orgId: UUID!, $dataStore: String!, $first: Int, $after: String, $createdBy: CustomUUID, $createdAfter: DateTime, $createdBefore: DateTime){
                dataStoreImports(orgId: $orgId, dataStore: $dataStore, first: $first, after: $after, createdBy: $createdBy, createdAfter: $createdAfter, createdBefore: $createdBefore){
                    entries{
                        orgId
                        datastore
                        name
                        importId
                        createdAt
                        createdBy
                        status
                        updatedAt
                        taskCount
                        failureLogs
                    }
                    cursor
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStore": data_store,
            "first": 20,
            "after": None,
        }
        result = self.client.execute_query(query_string, query_variables)
        return (
            result["dataStoreImports"]["entries"],
            result["dataStoreImports"]["cursor"],
        )

    def get_data_store_import_series(
        self,
        org_id: str,
        data_store: str,
        search: Optional[str] = None,
        first: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict[str, str]], str]:
        """Get data store imports."""
        query_string = """
            query DataStoreImportSeries($orgId: UUID!, $dataStore: String!, $first: Int, $after: String, $search: String) {
                dataStoreImportSeries(orgId: $orgId, dataStore: $dataStore, first: $first, after: $after, search: $search) {
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
            "search": search,
        }
        result = self.client.execute_query(query_string, query_variables)
        return (
            result["dataStoreImportSeries"]["entries"],
            result["dataStoreImportSeries"]["cursor"],
        )

    def delete_dataset(self, org_id: str, dataset_name: str) -> bool:
        """Delete a dataset."""
        query_string = """
            mutation removeDatastoreSDK($orgId: UUID!, $dataStores: [String!]!) {
                removeDatastore(orgId: $orgId, dataStores: $dataStores) {
                    ok
                    message
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "dataStores": [dataset_name],
        }
        result = self.client.execute_query(query_string, query_variables)
        return result["removeDatastore"]["ok"]
