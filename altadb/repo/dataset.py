"""Handlers to access APIs for getting projects."""

import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from altadb.common.client import AltaDBClient
from altadb.common.dataset import DatasetRepoInterface
from altadb.repo.shards import PROJECT_SHARD, STAGE_SHARD, TAXONOMY_SHARD
from altadb.types.taxonomy import Attribute, ObjectType, Taxonomy


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

    def get_stages(self, org_id: str, project_id: str) -> List[Dict]:
        """Get stages."""
        query = f"""
            query sdkGetStagesSDK($orgId: UUID!, $projectId: UUID!) {{
                stages(orgId: $orgId, projectId: $projectId) {{
                    {STAGE_SHARD}
                }}
            }}
        """
        variables = {"orgId": org_id, "projectId": project_id}
        response: Dict[str, List[Dict]] = self.client.execute_query(query, variables)
        return response["stages"]

    def create_project(
        self,
        org_id: str,
        name: str,
        stages: List[dict],
        td_type: str,
        tax_name: str,
        workspace_id: Optional[str],
        sibling_tasks: Optional[int],
    ) -> Dict:
        """Create a project and return project_id."""
        query = """
            mutation createProjectSimpleSDK(
                $orgId: UUID!
                $name: String!
                $stages: [StageInputSimple!]!
                $tdType: TaskDataType!
                $taxonomyName: String!
                $taxonomyVersion: Int!
                $workspaceId: UUID
                $taskDuplicationCount: Int
            ) {
                createProjectSimple(
                    orgId: $orgId
                    name: $name
                    stages: $stages
                    tdType: $tdType
                    taxonomyName: $taxonomyName
                    taxonomyVersion: $taxonomyVersion
                    workspaceId: $workspaceId
                    taskDuplicationCount: $taskDuplicationCount
                ) {
                    ok
                    errors
                    project {
                        projectId
                    }
                }
            }
        """
        for stage in stages:
            stage["stageConfig"] = json.dumps(
                stage["stageConfig"], separators=(",", ":")
            )
        variables = {
            "orgId": org_id,
            "name": name,
            "stages": stages,
            "tdType": td_type,
            "taxonomyName": tax_name,
            "taxonomyVersion": 1,
            "workspaceId": workspace_id,
            "taskDuplicationCount": sibling_tasks,
        }

        response: Dict[str, Dict] = self.client.execute_query(query, variables)
        return {
            "orgId": org_id,
            "projectId": response["createProjectSimple"]["project"]["projectId"],
        }

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

    def get_projects(self, org_id: str) -> List[Dict]:
        """Get all projects in organization."""
        query = f"""
            query getProjectsSDK($orgId: UUID!) {{
                projects(orgId: $orgId) {{
                    {PROJECT_SHARD}
                }}
            }}
        """
        response: Dict[str, List[Dict]] = self.client.execute_query(
            query, {"orgId": org_id}
        )
        return response["projects"]

    def get_taxonomies(self, org_id: str) -> List[Taxonomy]:
        """Get a list of taxonomies."""
        query = f"""
            query getTaxonomiesSDK($orgId: UUID!) {{
                taxonomies(orgId: $orgId) {{
                    {TAXONOMY_SHARD}
                }}
            }}
        """
        response: Dict[str, List[Taxonomy]] = self.client.execute_query(
            query, {"orgId": org_id}
        )
        return response["taxonomies"]

    def delete_project(self, org_id: str, project_id: str) -> None:
        """Delete Project."""
        query = """
            mutation removeProjectSDK($orgId: UUID!, $projectId: UUID!) {
                removeProject(orgId: $orgId, projectId: $projectId) {
                    ok
                }
            }
        """
        self.client.execute_query(query, {"orgId": org_id, "projectId": project_id})

    def get_labeling_information(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
        first: int,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get org labeling information."""
        query_string = """
        query firstLabelingTimeSDK(
            $orgId: UUID!
            $startDate: DateTime!
            $endDate: DateTime!
            $first: Int
            $after: String
        ) {
            firstLabelingTime(
                orgId: $orgId
                startDate: $startDate
                endDate: $endDate
                first: $first
                after: $after
            ) {
                entries {
                    project {
                        projectId
                    }
                    taskId
                    user {
                        email
                    }
                    timeSpent
                    cycle
                    date
                }
                cursor
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "first": first,
            "after": cursor,
        }
        result = self.client.execute_query(query_string, query_variables)
        tasks_paged = result.get("firstLabelingTime", {}) or {}
        entries: List[Dict] = tasks_paged.get("entries", []) or []  # type: ignore
        return entries, tasks_paged.get("cursor")

    def create_taxonomy(
        self,
        org_id: str,
        name: str,
        study_classify: Optional[List[Attribute]],
        series_classify: Optional[List[Attribute]],
        instance_classify: Optional[List[Attribute]],
        object_types: Optional[List[ObjectType]],
    ) -> bool:
        """Create new taxonomy."""
        query_string = """
        mutation createTaxonomyNewSDK(
            $orgId: UUID!
            $name: String!
            $studyClassify: [NewAttributeInput!]
            $seriesClassify: [NewAttributeInput!]
            $instanceClassify: [NewAttributeInput!]
            $objectTypes: [ObjectTypeInput!]
        ) {
            createTaxonomyNew(
                orgId: $orgId
                name: $name
                studyClassify: $studyClassify
                seriesClassify: $seriesClassify
                instanceClassify: $instanceClassify
                objectTypes: $objectTypes
            ) {
                ok
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "name": name,
            "studyClassify": study_classify,
            "seriesClassify": series_classify,
            "instanceClassify": instance_classify,
            "objectTypes": object_types,
        }
        result = self.client.execute_query(query_string, query_variables)
        return bool(result and result.get("createTaxonomyNew", {}).get("ok"))

    def get_taxonomy(
        self, org_id: str, tax_id: Optional[str], name: Optional[str]
    ) -> Taxonomy:
        """Get a taxonomy."""
        query = f"""
            query getTaxonomySDK($orgId: UUID!, $taxId: UUID, $name: String) {{
                taxonomy(orgId: $orgId, taxId: $taxId, name: $name) {{
                    {TAXONOMY_SHARD}
                }}
            }}
        """
        response: Dict[str, Taxonomy] = self.client.execute_query(
            query, {"orgId": org_id, "taxId": tax_id, "name": name}
        )
        return response["taxonomy"]

    def update_taxonomy(
        self,
        org_id: str,
        tax_id: str,
        study_classify: Optional[List[Attribute]],
        series_classify: Optional[List[Attribute]],
        instance_classify: Optional[List[Attribute]],
        object_types: Optional[List[ObjectType]],
    ) -> bool:
        """Update taxonomy."""
        query_string = """
        mutation updateTaxonomySDK(
            $orgId: UUID!
            $taxId: UUID!
            $studyClassify: [NewAttributeInput!]
            $seriesClassify: [NewAttributeInput!]
            $instanceClassify: [NewAttributeInput!]
            $objectTypes: [ObjectTypeInput!]
        ) {
            updateTaxonomy(
                orgId: $orgId
                taxId: $taxId
                studyClassify: $studyClassify
                seriesClassify: $seriesClassify
                instanceClassify: $instanceClassify
                objectTypes: $objectTypes
            ) {
                ok
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "taxId": tax_id,
            "studyClassify": study_classify,
            "seriesClassify": series_classify,
            "instanceClassify": instance_classify,
            "objectTypes": object_types,
        }
        result = self.client.execute_query(query_string, query_variables)
        return bool(result and result.get("updateTaxonomy", {}).get("ok"))

    def get_label_storage(self, org_id: str, project_id: str) -> Tuple[str, str]:
        """Get label storage method for a project."""
        query_string = """
        query getLabelStorageSDK($orgId: UUID!, $projectId: UUID!) {
            getLabelStorage(orgId: $orgId, projectId: $projectId) {
                storageId
                path
            }
        }
        """
        query_variables = {"orgId": org_id, "projectId": project_id}
        result = self.client.execute_query(query_string, query_variables)
        return (
            result["getLabelStorage"]["storageId"],
            result["getLabelStorage"]["path"],
        )

    def set_label_storage(
        self, org_id: str, project_id: str, storage_id: str, path: str
    ) -> bool:
        """Set label storage method for a project."""
        query_string = """
        mutation updateLabelStorageSDK(
            $orgId: UUID!
            $projectId: UUID!
            $storageId: UUID!
            $path: String!
        ) {
            updateLabelStorage(
                orgId: $orgId
                projectId: $projectId
                storageId: $storageId
                path: $path
            ) {
                ok
            }
        }
        """
        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "storageId": storage_id,
            "path": path,
        }
        result = self.client.execute_query(query_string, query_variables)
        return bool(result and result.get("updateLabelStorage", {}).get("ok"))

    def update_stage(
        self, org_id: str, project_id: str, stage_name: str, stage_config: Dict
    ) -> Tuple[bool, List[Dict]]:
        """Update project stage."""
        query_string = f"""
        mutation updateStageSDK(
            $orgId: UUID!
            $projectId: UUID!
            $stageName: String!
            $config: JSONString
        ) {{
            updateStage(
                orgId: $orgId
                projectId: $projectId
                stageName: $stageName
                config: $config
            ) {{
                ok
                pipeline {{
                    {STAGE_SHARD}
                }}
            }}
        }}
        """

        query_variables = {
            "orgId": org_id,
            "projectId": project_id,
            "stageName": stage_name,
            "config": json.dumps(stage_config),
        }

        response = self.client.execute_query(query_string, query_variables)
        result = (response.get("updateStage", {}) or {}) if response else {}
        return bool(result.get("ok")), (result.get("pipeline", []) or [])

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
