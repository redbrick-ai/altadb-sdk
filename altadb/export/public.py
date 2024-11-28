"""Decode DICOM images from metadata and URL."""

from functools import partial
import json
import os
from typing import Dict, Iterator, List, Optional

from rich.console import Console

from altadb.common.constants import MAX_CONCURRENCY
from altadb.common.context import AltaDBContext
from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.files import save_dicom_series
from altadb.utils.pagination import PaginationIterator


class Export:
    """Export class."""

    def __init__(self, context: AltaDBContext, org_id: str, dataset: str) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.dataset = dataset

    def get_data_store_series(
        self, *, dataset_name: str, search: Optional[str], page_size: int
    ) -> Iterator[Dict[str, str]]:
        """Get data store series."""
        my_iter = PaginationIterator(
            partial(
                self.context.dataset.get_data_store_import_series,
                self.org_id,
                dataset_name,
                search,
            ),
            limit=page_size,
        )

        for ds_import_series in my_iter:
            yield ds_import_series

    async def export_to_files(
        self,
        dataset_name: str,
        path: str,
        page_size: int = MAX_CONCURRENCY,
        number: Optional[int] = None,
        search: Optional[str] = None,  # pylint: disable=unused-argument
    ) -> None:
        """Export dataset to folder.

        Args
        ----
        dataset_name: str
            Name of the dataset.
        path: str
            Path to the folder where the dataset will be saved.
        page_size: int
            Number of series to export in parallel.
        number: int
            Number of series to export in total.
        search: str
            Search string to filter the series to export.
        """
        try:
            console = Console()
            console.print(
                f"[bold green][\u2713] Saving dataset {dataset_name} to {path}"
            )
            dataset_root = f"{path}/{dataset_name}"
            json_path = f"{dataset_root}/series.json"
            if os.path.exists(json_path):
                console.print(
                    f"[bold yellow][\u26A0] Warning: {json_path} already exists. It will be overwritten."
                )
                os.remove(json_path)

            ds_import_series_list: List[Dict[str, str]] = []
            # Save the files in chunks of page_size
            for ds_import_series in self.get_data_store_series(
                dataset_name=dataset_name,
                search=search,
                page_size=number or MAX_CONCURRENCY,
            ):
                ds_import_series_list.append(ds_import_series)
                if len(ds_import_series_list) >= page_size:
                    await self.save_series_data_chunk(
                        dataset_name,
                        page_size,
                        dataset_root,
                        json_path,
                        ds_import_series_list,
                    )
                    ds_import_series_list = []

            if ds_import_series_list:
                await self.save_series_data_chunk(
                    dataset_name,
                    page_size,
                    dataset_root,
                    json_path,
                    ds_import_series_list,
                )
        except Exception as error:  # pylint: disable=broad-except
            console.print(f"[bold red][\u2717] Error: {error}")

    async def save_series_data_chunk(
        self,
        dataset_name: str,
        max_concurrency: int,
        dataset_root: str,
        json_path: str,
        ds_import_series_list: List[Dict[str, str]],
    ) -> None:
        """Store data for the given series imports.

        Args
        ----
        dataset_name: str
            Name of the dataset.
        max_concurrency: int
            Number of series to export in parallel.
        dataset_root: str
            Path to the dataset root folder.
        json_path: str
            Path to the series.json file.
        ds_import_series_list: List[Dict]
            List of series to export.

        """
        base_url = self.context.client.url.strip()
        if base_url.endswith("/graphql/"):
            base_url = base_url[:-8]
        if base_url.endswith("api/"):
            base_url = base_url.rstrip("api/")
        coros = [
            save_dicom_series(
                ds_import_series["url"],
                os.path.join(dataset_root, ds_import_series["seriesId"]),
                base_url,
                self.context.client.headers,
            )
            for ds_import_series in ds_import_series_list
        ]
        file_paths_list = await gather_with_concurrency(
            max_concurrency,
            coros,
            progress_bar_name=f"Exporting {len(ds_import_series_list)} series",
            keep_progress_bar=True,
        )
        new_series = []
        # Save the series data to the series.json file
        for ds_import, file_paths in zip(ds_import_series_list, file_paths_list):
            new_series.append(
                {
                    "dataset": dataset_name,
                    "seriesId": ds_import["seriesId"],
                    "importId": ds_import["importId"],
                    "createdAt": ds_import["createdAt"],
                    "createdBy": ds_import["createdBy"],
                    "items": file_paths,
                }
            )
        if new_series:
            series = []
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as series_file:
                    series = json.load(series_file)

            with open(json_path, "w+", encoding="utf-8") as series_file:
                json.dump(
                    [
                        *series,
                        *new_series,
                    ],
                    series_file,
                    indent=2,
                )
