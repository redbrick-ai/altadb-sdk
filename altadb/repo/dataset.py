"""Handlers to access APIs for getting projects."""

import json
from typing import List, Dict, Optional

from altadb.common.client import AltaDBClient
from altadb.common.dataset import DatasetRepoInterface


class DatasetRepo(DatasetRepoInterface):
    """Class to manage interaction with project APIs."""

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
        Get project name and status.

        Raise an exception if project does not exist.
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

        raise Exception("Project does not exist")

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
