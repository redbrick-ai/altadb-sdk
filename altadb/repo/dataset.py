"""Handlers to access APIs for getting projects."""

import json
from typing import List, Dict, Optional

from altadb.common.client import AltaDBClient
from altadb.common.dataset import DatasetRepoInterface


class DatasetRepo(DatasetRepoInterface):
    """Class to manage interaction with project APIs."""

    def __init__(self, client: AltaDBClient) -> None:
        """Construct ProjectRepo."""
        self.client = client

    def get_datasets(self, org_id: str) -> List[Dict]:
        """Get all datasets in organization."""
        query = f"""
            query sdkDataStores($orgId: UUID!) {{
                dataStores(orgId: $orgId) {{
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }}
            }}
        """
        response: Dict[str, List[Dict]] = self.client.execute_query(
            query, {"orgId": org_id}
        )
        return response["dataStores"]

    def check_if_exists(self, org_id: str, dataset_name: str) -> bool:
        query = f"""
        query DataStore($orgId: UUID!) {{
            dataStores(orgId: $orgId) {{
                orgId
                name
                displayName
                createdAt
                createdBy
                status
                updatedAt
                importStatuses
            }}
        }}
        """
        variables = {"orgId": org_id}
        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        return any(
            dataset["displayName"] == dataset_name for dataset in response["dataStores"]
        )

    def create_dataset(self, org_id: str, dataset_name: str) -> Dict:
        query = f"""
            mutation sdkCreateDatastore($orgId: UUID!, $dataStore: String!, $displayName: String!) {{
                createDatastore(orgId: $orgId, dataStore: $dataStore, displayName: $displayName) {{
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }}
            }}
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
        query = f"""
            query sdkDataStore($orgId: UUID!, $name: String!) {{
                dataStore(orgId: $orgId, name: $name) {{
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }}
            }}
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
            query Organization($orgId: UUID!) {
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

    def get_members(self, org_id: str, project_id: str) -> List[Dict]:
        """Get members of a project."""
        query_string = """
        query getProjectMembersSDK($orgId: UUID!, $projectId: UUID!) {
            projectMembers(orgId: $orgId, projectId: $projectId) {
                member {
                    user {
                        userId
                        email
                        givenName
                        familyName
                    }
                    role
                    tags
                }
                stageAccess {
                    stageName
                    access
                }
            }
        }
        """
        query_variables = {"orgId": org_id, "projectId": project_id}
        result = self.client.execute_query(query_string, query_variables)
        members: List[Dict] = result["projectMembers"]
        return members

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
