"""CLI upload command."""

import os
import re
import json
import asyncio
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import List, Dict, Optional, Union, cast

from altadb.cli.input.select import CLIInputSelect
from altadb.cli.dataset import CLIDataset
from altadb.repo.dataset import DatasetRepo
from altadb.cli.cli_base import CLIUploadInterface
from altadb.common.enums import StorageMethod, ImportTypes
from altadb.utils.logging import assert_validation, logger
from altadb.utils.files import find_files_recursive
from altadb.types.task import InputTask

from .upload_file_to_presigned_url import upload_file_to_presigned_url
from .file_upload_mutation import file_upload_mutation


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
            "-c",
            "--concurrency",
            type=int,
            default=2,
            help="Concurrency value (Default: 10)",
        )
        parser.add_argument(
            "--as-frames",
            action="store_true",
            help="Upload video from image frames",
        )
        parser.add_argument(
            "--type",
            "-t",
            nargs="?",
            default=ImportTypes.DICOM3D.value,
            choices=[import_type.value for import_type in ImportTypes],
            help=f"""Import file type
{['`' + import_type.value + '`' for import_type in ImportTypes]}\n
Please refer to [our documentation](https://docs.redbrickai.com/importing-data/direct-data-upload),
to understand the required folder structure and supported file types.
""",
        )
        parser.add_argument(
            "--as-study",
            action="store_true",
            help="Group files by study",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Upload json files with list of task objects",
        )
        parser.add_argument(
            "--segment-map",
            "-m",
            help="Segmentation mapping file path",
        )
        parser.add_argument(
            "--storage",
            "-s",
            default=self.STORAGE_REDBRICK,
            help="Storage method: "
            + f"({self.STORAGE_REDBRICK} [default], {self.STORAGE_PUBLIC}, <storage id>)",
        )
        parser.add_argument(
            "--label-storage",
            help="Label Storage method: (same as items storage `--storage` [default],"
            + f" {self.STORAGE_REDBRICK}, {self.STORAGE_PUBLIC}, <storage id>)",
        )
        parser.add_argument(
            "--ground-truth",
            action="store_true",
            help="""Upload tasks directly to ground truth.""",
        )
        parser.add_argument(
            "--label-validate",
            action="store_true",
            help="""
Validate NIfTI label instances and segmentMap.
By default, the uploaded NIfTI files are not validated during upload,
which can result in invalid files being uploaded.
Using this argument validates the files before upload,
but may increase the upload time.""",
        )
        parser.add_argument(
            "--rt-struct",
            action="store_true",
            help="Upload segmentations from DICOM RT-Struct files.",
        )
        parser.add_argument(
            "--clear-cache", action="store_true", help="Clear local cache"
        )
        # parser.add_argument(
        #     "--concurrency",
        #     "-c",
        #     type=int,
        #     default=10,
        #     help="Concurrency value (Default: 10)",
        # )

    def handler(self, args: Namespace) -> None:
        """Handle upload command."""
        self.args = args
        project = CLIDataset(required=False)
        org_id = project.creds.org_id
        # assert_validation(project, "Not a valid project")
        self.project = cast(CLIDataset, project)
        self.org_id = org_id
        self.dataset_name = args.dataset
        self.handle_upload()

    def handle_upload(self) -> None:  # noqa: ignore=C901
        """Handle empty sub command."""
        # pylint: disable=protected-access, too-many-branches, too-many-locals, too-many-statements
        # pylint: disable=too-many-nested-blocks
        logger.debug("Uploading data to project")
        project = self.project
        concurrency = self.args.concurrency
        org_id = self.org_id
        dataset_name = self.dataset_name

        path = os.path.normpath(self.args.path)
        api_key = self.project.context.client.gql_api_key
        print(
            f"""
            Arguments received:
                dataset: {self.dataset_name}
                path: {path}
                API Key: {api_key}
              """
        )
        from .generate_import_label import generate_import_label
        from .generate_import_id import generate_import_id
        from .generate_presigned_urls import generate_presigned_urls

        def check_dicom_file(extension: list[str], filename: str) -> bool:
            return any(filename.lower().endswith(ext) for ext in extension)

        files: list[str] = []
        if os.path.isdir(path):
            print("Given path is a directory")
            # Recursively get all files in the directory, and find out the dicom files
            dicom_file_extensions = [".dcm", ".dicom", ".dicm", ".dic"]
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    if check_dicom_file(
                        extension=dicom_file_extensions, filename=filename
                    ):
                        files.append(os.path.join(root, filename))

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
        import_name = generate_import_label()
        ds_repo = DatasetRepo(client=self.project.context.client)
        import_id: str = (
            (
                (
                    ds_repo.import_files(
                        org_id=org_id,
                        data_store=dataset_name,
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
                        org_id=org_id,
                        data_store=dataset_name,
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
                upload_status = upload_files_intermediate_function(
                    files_paths=files_list,
                    presigned_urls=presigned_urls,
                    concurrency=concurrency,
                )
                mutation_status = ds_repo.process_import(
                    org_id=org_id,
                    data_store=dataset_name,
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


def upload_files_intermediate_function(
    files_paths: list[dict[str, str]],
    presigned_urls: list[str],
    concurrency: int,
) -> bool:
    results: list[bool] = []
    semaphore = asyncio.Semaphore(concurrency)
    if len(files_paths) != len(presigned_urls):
        print("Number of files and presigned URLs do not match")
        return False
    for i in range(0, len(files_paths), concurrency):
        loop = asyncio.get_event_loop()
        tasks = [
            upload_file_to_presigned_url(
                file_paths=files_paths[i : i + concurrency],
                presigned_urls=presigned_urls[i : i + concurrency],
                semaphore=semaphore,
            )
        ]
        _results = loop.run_until_complete(asyncio.gather(*tasks))
        if not all(_results):
            return False
        else:
            results.extend(_results)
    return True
