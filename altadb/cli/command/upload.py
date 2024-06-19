"""CLI upload command."""

import os
import asyncio
from argparse import ArgumentParser, Namespace
from typing import cast

from altadb.cli.dataset import CLIDataset
from altadb.repo.dataset import DatasetRepo
from altadb.cli.cli_base import CLIUploadInterface
from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.files import (
    DICOM_FILE_TYPES,
    find_files_recursive,
    get_file_type,
    upload_files,
)


class CLIUploadController(CLIUploadInterface):
    """CLI upload command controller."""

    org_id: str
    dataset_name: str

    def __init__(self, parser: ArgumentParser) -> None:
        """Intialize upload sub commands."""
        parser.add_argument(
            "dataset",
            help="Dataset name",
        )
        parser.add_argument(
            "path",
            help="The path containing files to upload to the project",
        )
        parser.add_argument(
            "-n",
            "--name",
            dest="name",
            help="Import name",
        )
        parser.add_argument(
            "-c",
            "--concurrency",
            type=int,
            default=10,
            help="Concurrency value (Default: 10)",
        )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        project = CLIDataset(required=False)
        # assert_validation(project, "Not a valid project")
        self.project = cast(CLIDataset, project)
        self.org_id = project.creds.org_id
        self.dataset_name = args.dataset
        self.handle_upload()

    def handle_upload(self) -> None:  # noqa: ignore=C901
        """Handle empty sub command."""
        # pylint: disable=protected-access, too-many-branches, too-many-locals, too-many-statements
        # pylint: disable=too-many-nested-blocks
        from altadb.utils.dataset import generate_import_label

        path = os.path.normpath(self.args.path)
        import_name = self.args.name or generate_import_label()

        files: list[str] = []
        if os.path.isdir(path):
            _files = find_files_recursive(
                path, set(DICOM_FILE_TYPES.keys()), multiple=False
            )
            print(_files)
            files = [_file[0] for _file in _files if _file]

        else:
            files = [path]
        if not path:
            print("No file path provided")
            return
        # Now that we have the files list, let us generate the presigned URLs
        files_list: list[dict[str, str]] = []
        for file in files:
            files_list.append(
                {
                    "filePath": os.path.basename(file),
                    "abs_file_path": file,
                    "fileType": "application/dicom",
                }
            )
        ds_repo = DatasetRepo(client=self.project.context.client)
        import_id: str = (
            (
                (
                    ds_repo.import_files(
                        org_id=self.org_id,
                        data_store=self.dataset_name,
                        import_name=import_name,
                    )
                    or {}
                ).get("importFiles")
                or {}
            ).get("dataStoreImport")
            or {}
        ).get("importId") or ""
        if import_id:
            # Generate presigned URLs
            print(f"Got import id: {import_id}")
            presigned_urls = (
                (
                    ds_repo.import_files(
                        org_id=self.org_id,
                        data_store=self.dataset_name,
                        import_name=import_name,
                        import_id=import_id,
                        files=[
                            {
                                "filePath": file["filePath"],
                                "fileType": file["fileType"],
                            }
                            for file in files_list
                        ],
                    )
                    or {}
                ).get("importFiles")
                or {}
            ).get("urls") or []
            if presigned_urls:
                print("Presigned URLs generated successfully")
                # Upload files to presigned URLs
                upload_status = asyncio.run(
                    upload_files_intermediate_function(
                        files_paths=files_list,
                        presigned_urls=presigned_urls,
                        concurrency=self.args.concurrency,
                    )
                )
                if not upload_status:
                    print("Error uploading files")
                    return
                mutation_status = ds_repo.process_import(
                    org_id=self.org_id,
                    data_store=self.dataset_name,
                    import_id=import_id,
                    total_files=len(files),
                )
                if not mutation_status:
                    print("Error performing mutation")
                    return
                print("Mutation successful")

            else:
                print("Error: Could not generate presigned URLs")
                return
        else:
            print("Error: Could not generate import ID")
            return


async def upload_files_intermediate_function(
    files_paths: list[dict[str, str]],
    presigned_urls: list[str],
    concurrency: int,
) -> bool:
    coros = [
        upload_files(
            [
                (
                    file_path["abs_file_path"],
                    presigned_url,
                    get_file_type(file_path["abs_file_path"])[-1],
                )
                for file_path, presigned_url in zip(files_paths, presigned_urls)
            ],
        )
    ]
    results = await gather_with_concurrency(
        max_concurrency=concurrency,
        tasks=coros,
        progress_bar_name="Uploading files",
        keep_progress_bar=True,
        return_exceptions=False,
    )
    return all(results)
