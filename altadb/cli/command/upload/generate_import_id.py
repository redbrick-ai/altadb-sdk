from typing import Optional
import requests  # type: ignore
import json

URL = "https://preview.altadb.com/api/graphql/"

MUTATION = """
mutation importFiles($orgId: UUID!, $dataStore: String!, $files: [ImportJobFileInput!]!, $importName: String) {
    importFiles(orgId: $orgId, dataStore: $dataStore, files: $files, importName: $importName) {
        dataStoreImport {
            importId
        }
        urls
    }
}
"""


def generate_import_id(
    apikey: str,
    org_id: str,
    dataset_name: str,
    import_name: str,
) -> Optional[str]:
    try:
        print(
            f"""
        Using the following parameters:
        apikey: {apikey}
        org_id: {org_id}
        dataset_name: {dataset_name}
        import_name: {import_name}
              """
        )
        response = requests.post(
            URL,
            headers={
                "Apikey": apikey,
                "Content-Type": "application/json",
            },
            json={
                "query": MUTATION,
                "variables": {
                    "orgId": org_id,
                    "dataStore": dataset_name,
                    "files": [],
                    "importName": import_name,
                },
            },
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"]["importFiles"]["dataStoreImport"]["importId"]
        else:
            print("Error:", response.status_code)
            print(response.text)
    except Exception as e:
        print(e)

    return None


__all__ = [
    "generate_import_id",
]
