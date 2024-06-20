"""Public interface to upload module."""

import os
from typing import Any, List, Optional

import tqdm  # type: ignore

from altadb.common.constants import MAX_FILE_BATCH_SIZE
from altadb.common.context import AltaDBContext

from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.logging import logger, log_error
from altadb.utils.files import (
    DICOM_FILE_TYPES,
    find_files_recursive,
    get_file_type,
    upload_files,
)


class Upload:
    """Primary interface for uploading to a dataset."""

    def __init__(self, context: AltaDBContext, org_id: str, dataset: str) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.dataset = dataset

    async def upload_files(
        self,
        dataset: str,
        path: str,
        import_name: Optional[str] = None,
        concurrency: int = 10,
        batch_size: int = MAX_FILE_BATCH_SIZE,
    ) -> None:
        """Upload files."""

        files: list[str] = []
        if os.path.isdir(path):
            _files = find_files_recursive(
                path, set(DICOM_FILE_TYPES.keys()), multiple=False
            )
            files = [_file[0] for _file in _files if _file]

        else:
            files = [path]
        if not path:
            logger.warn("No file path provided")
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
        import_id: str = (
            (
                (
                    self.context.upload.import_files(
                        org_id=self.org_id,
                        data_store=dataset,
                        import_name=import_name,
                    )
                    or {}
                ).get("importFiles")
                or {}
            ).get("dataStoreImport")
            or {}
        ).get("importId") or ""
        if import_id:
            progress_bar = tqdm.tqdm(desc="Uploading all files", total=len(files_list))
            # Upload files to presigned URLs
            coro = gather_with_concurrency(
                concurrency,
                [
                    self.upload_files_intermediate_function(
                        dataset=dataset,
                        import_name=import_name,
                        import_id=import_id,
                        files_paths=files_list[i : i + 2],
                        file_batch_size=batch_size,
                        global_progress_bar=progress_bar,
                    )
                    for i in range(0, len(files_list), 2)
                ],
            )

            upload_status = await coro

            if not upload_status:
                log_error("Error uploading files", True)

            mutation_status = self.context.upload.process_import(
                org_id=self.org_id,
                data_store=dataset,
                import_id=import_id,
                total_files=len(files),
            )
            if not mutation_status:
                log_error("Error uploading files", True)
        else:
            log_error("Error uploading files", True)

    async def upload_files_intermediate_function(
        self,
        dataset: str,
        import_id: str,
        global_progress_bar: tqdm.tqdm,
        import_name: Optional[str] = None,
        files_paths: List[dict[str, str]] = [],
        file_batch_size: int = MAX_FILE_BATCH_SIZE,
    ) -> bool:
        # Generate presigned URLs for concurrency number of files at a time
        presigned_urls = (
            (
                self.context.upload.import_files(
                    org_id=self.org_id,
                    data_store=dataset,
                    import_name=import_name,
                    import_id=import_id,
                    files=[
                        {
                            "filePath": file["filePath"],
                            "fileType": file["fileType"],
                        }
                        for file in files_paths
                    ],
                )
                or {}
            ).get("importFiles")
            or {}
        ).get("urls") or []
        if not presigned_urls:
            return False
        # Upload files to presigned URLs
        results = await upload_files(
            [
                (
                    file_path["abs_file_path"],
                    presigned_url,
                    get_file_type(file_path["abs_file_path"])[-1],
                )
                for file_path, presigned_url in zip(files_paths, presigned_urls)
            ],
            progress_bar_name=f"Batch Progress",
            keep_progress_bar=False,
            file_batch_size=file_batch_size,
            upload_callback=lambda _, __: global_progress_bar.update(1),
        )
        return all(results)
