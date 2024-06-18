import requests  # type: ignore
import json

# from altadb.constants import GRAPHQL_SERVER_URL

GRAPHQL_SERVER_URL = "https://preview.altadb.com/api/graphql/"

MUTATION_QUERY = """
    mutation processImport($orgId: UUID!, $dataStore: String!, $importId: UUID!, $totalFiles: Int) {
        processImport(orgId: $orgId, dataStore: $dataStore, importId: $importId, totalFiles: $totalFiles) {
            ok
            message
        }
    }
"""


def file_upload_mutation(
    api_key: str,
    org_id: str,
    data_store: str,
    import_id: str,
    total_files: int,
) -> bool:
    print(
        f"""
    Using the following parameters:
    api_key: {api_key}
    org_id: {org_id}
    data_store: {data_store}
    import_id: {import_id}
    total_files: {total_files}
    """
    )

    response = requests.post(
        GRAPHQL_SERVER_URL,
        headers={
            "Content-Type": "application/json",
            "Apikey": api_key,
            "accept-encoding": "gzip, deflate",
        },
        json={
            "query": MUTATION_QUERY,
            "variables": {
                "orgId": org_id,
                "dataStore": data_store,
                "importId": import_id,
                "totalFiles": total_files,
            },
        },
    )
    return response.status_code == 200


__all__ = [
    "file_upload_mutation",
]
