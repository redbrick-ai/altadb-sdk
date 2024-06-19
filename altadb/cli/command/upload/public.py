"""CLI upload command."""

import os
import asyncio
from argparse import ArgumentParser, Namespace
from typing import cast

from altadb.cli.dataset import CLIDataset
from altadb.repo.dataset import DatasetRepo
from altadb.cli.cli_base import CLIUploadInterface
from altadb.common.enums import ImportTypes
from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.logging import logger
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
        from .generate_import_label import generate_import_label

        logger.debug("Uploading data to project")
        project = self.project
        concurrency = self.args.concurrency
        org_id = self.org_id
        dataset_name = self.dataset_name
        import_name = self.args.name or generate_import_label()

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
                upload_status = asyncio.run(
                    upload_files_intermediate_function(
                        files_paths=files_list,
                        presigned_urls=presigned_urls,
                        concurrency=concurrency,
                    )
                )
                if not upload_status:
                    print("Error uploading files")
                    return
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
