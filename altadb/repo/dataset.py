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

    def get_datasets(self, org_id: str) -> List[Dict]:
        """Get all datasets in organization."""
        query = """
            query sdkDataStores($orgId: UUID!) {
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
        response: Dict[str, List[Dict]] = self.client.execute_query(
            query, {"orgId": org_id}
        )
        return response["dataStores"]

    def check_if_exists(self, org_id: str, dataset_name: str) -> bool:
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
        print(variables)
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
        print(response)
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

    def self_health_check(
        self, org_id: str, self_url: str, self_data: Dict
    ) -> Optional[str]:
        """Send a health check update from the model server."""
        query_string = """
            mutation modelHealthSDK($orgId: UUID!, $modelUrl: String!, $modelData: JSONString!) {
                modelHealth(orgId: $orgId, modelUrl: $modelUrl, modelData: $modelData) {
                    ok
                    message
                }
            }
        """
        query_variables = {
            "orgId": org_id,
            "modelUrl": self_url,
            "modelData": json.dumps(self_data),
        }
        result = self.client.execute_query(query_string, query_variables)
        if not result["modelHealth"]["ok"]:
            return result["modelHealth"]["message"]

        return None
