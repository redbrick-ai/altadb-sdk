"""Decode DICOM images from metadata and URL."""

import asyncio
from functools import partial
import json
import os
from typing import Dict, Iterator, List, Optional, Tuple

import aiohttp
from rich.console import Console

from altadb.common.constants import EXPORT_PAGE_SIZE, MAX_CONCURRENCY
from altadb.common.context import AltaDBContext
from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.files import save_dicom_dataset, save_dicom_dataset2
from altadb.utils.pagination import PaginationIterator


class Export:
    """Export class."""

    def __init__(self, context: AltaDBContext, org_id: str, dataset: str) -> None:
        """Construct Upload object."""
        self.context = context
        self.org_id = org_id
        self.dataset = dataset

    async def construct_images_from_metadata_and_url(
        self,
        aiosession: aiohttp.ClientSession,
        res_json: Dict,
        source_dir: str,
        filename_preifx: str,
    ) -> List[str]:
        """Construct a DICOM image from metadata and URL."""
        # Get the path of each imageFrame
        image_frames_urls_map = {
            image_frame["id"]: image_frame["path"]
            for image_frame in res_json.get("imageFrames", [])
        }

        file_paths: List[str] = []

        # For each `instances` item, create a new file
        for instance in res_json["metaData"]["instances"]:
            # Get the image frame URLs
            frame_ids = [frame["id"] for frame in instance["frames"]]
            image_frames_urls = [
                image_frames_urls_map[frame_id] for frame_id in frame_ids
            ]
            frame_dir = os.path.join(source_dir, filename_preifx)
            os.makedirs(frame_dir, exist_ok=True)
            export_filename = os.path.join(
                filename_preifx, f"{filename_preifx}-{frame_ids[0]}.dcm"
            )
            await save_dicom_dataset(
                instance["metaData"],
                instance["frames"],
                image_frames_urls,
                os.path.join(source_dir, export_filename),
                aiosession,
            )
            file_paths.append(export_filename)

        await asyncio.sleep(0.250)  # give time to close ssl connections
        await aiosession.close()
        return file_paths

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

    async def export_dataset_to_folder(
        self,
        dataset_name: str,
        path: str,
        page_size: int = MAX_CONCURRENCY,
        number: int = EXPORT_PAGE_SIZE,
        search: Optional[str] = None,  # pylint: disable=unused-argument
    ) -> None:
        """Export dataset to folder."""
        # pylint: disable=too-many-locals
        dataset_root = f"{path}/{dataset_name}"
        console = Console()

        console.print(f"[bold green][\u2713] Saving dataset {dataset_name} to {path}")

        json_path = f"{dataset_root}/series.json"

        series: List[Dict] = []

        ds_import_series_list: List[Dict[str, str]] = []
        for ds_import_series in self.get_data_store_series(
            dataset_name=dataset_name, search=search, page_size=number
        ):
            ds_import_series_list.append(ds_import_series)
            if len(ds_import_series_list) >= page_size:
                await self.store_data(
                    dataset_name,
                    page_size,
                    dataset_root,
                    console,
                    json_path,
                    series,
                    ds_import_series_list,
                )
                ds_import_series_list = []

        if ds_import_series_list:
            await self.store_data(
                dataset_name,
                page_size,
                dataset_root,
                console,
                json_path,
                series,
                ds_import_series_list,
            )

    async def store_data(
        self,
        dataset_name,
        max_concurrency,
        dataset_root,
        console,
        json_path,
        series: List[Dict],
        ds_import_series_list,
    ) -> None:
        """Store data for the given series imports."""
        file_paths_list = await gather_with_concurrency(
            max_concurrency,
            [
                self.fetch_and_save_image_data(
                    ds_import_series,
                    f"{dataset_root}/{ds_import_series['seriesId']}",
                    console,
                )
                for ds_import_series in ds_import_series_list
            ],
        )
        for ds_import, file_paths in zip(ds_import_series_list, file_paths_list):
            series.append(
                {
                    "dataset": dataset_name,
                    "seriesId": ds_import["seriesId"],
                    "importId": ds_import["importId"],
                    "createdAt": ds_import["createdAt"],
                    "createdBy": ds_import["createdBy"],
                    "items": file_paths,
                }
            )
        if series:
            with open(json_path, "w+", encoding="utf-8") as series_file:
                json.dump(series, series_file, indent=2)

    async def fetch_and_save_image_data(
        self,
        item: Dict,
        source_dir: str,
        console: Console,
    ) -> Optional[List[str]]:
        """Fetch and save image data."""
        # Check if the folder exists for the given seriesId
        console.print(f"\t[blue] [\u2713] Fetching {item['seriesId']}")
        image_content_url = item["url"]
        return await save_dicom_dataset2(
            image_content_url,
            source_dir,
            self.context.client.base_url,
            self.context.client.headers,
        )
