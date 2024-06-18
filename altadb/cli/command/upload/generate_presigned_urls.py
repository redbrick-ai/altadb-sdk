import traceback
from typing import Optional

import requests  # type: ignore
import json

URL = "https://preview.altadb.com/api/graphql/"
# print(response.text)
MUTATION = """
mutation importFiles($orgId: UUID!, $dataStore: String!, $files: [ImportJobFileInput!]!, $importId: UUID) {
    importFiles(orgId: $orgId, dataStore: $dataStore, files: $files, importId: $importId) {
        dataStoreImport {
            importId
        }
        urls
    }
}
"""


def generate_presigned_urls(
    apikey: str,
    org_id: str,
    dataset_name: str,
    import_id: str,
    files: list[dict[str, str]],
) -> list[str]:
    res: list[str] = []
    try:
        print(
            f"""
        Using the following parameters:
        apikey: {apikey}
        org_id: {org_id}
        dataset_name: {dataset_name}
        import_name: {import_id}
        files: {files}
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
                    "files": [
                        {
                            "filePath": file["filePath"],
                            "fileType": file["fileType"],
                        }
                        for file in files
                    ],
                    "importId": import_id,
                },
            },
        )
        if response.status_code == 200:
            print("Response:", response.text)
            data: dict = response.json()
            if not data.get("data"):
                print("Error:", data)
                return res
            urls = data["data"]["importFiles"]["urls"]
            res.extend(urls)
        else:
            print("Error:", response.status_code)
            print(response.text)
    except Exception as e:
        traceback.print_exc()
        print(e)
    return res
