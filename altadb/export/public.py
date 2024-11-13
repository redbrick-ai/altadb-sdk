"""Decode DICOM images from metadata and URL."""

import asyncio
import json
import os
from typing import Dict, List, Optional, Tuple

import aiohttp
from rich.console import Console

from altadb.common.constants import EXPORT_PAGE_SIZE, MAX_CONCURRENCY
from altadb.common.context import AltaDBContext
from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.files import create_dicom_dataset, get_image_content


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
        image_frames_urls: Dict[str, str] = {}
        # Get the path of each imageFrame
        for image_frame in res_json.get("imageFrames") or []:
            image_frames_urls[image_frame["id"]] = image_frame["path"]

        file_paths: List[str] = []

        # For each `instances` item, create a new file
        for instance_metadata in res_json["metaData"]["instances"]:
            # Collect all the frame ids from `frames`
            frame_ids: List[str] = [
                frame.get("id") for frame in instance_metadata.get("frames") or []
            ]
            frame_contents = await asyncio.gather(
                *[
                    get_image_content(aiosession, image_url=image_frames_urls[frame_id])
                    for frame_id in frame_ids
                ]
            )
            # Add metadata
            ds_file = create_dicom_dataset(instance_metadata, frame_contents)
            frame_dir = f"{source_dir}/{filename_preifx}"
            if not os.path.exists(frame_dir):
                os.makedirs(frame_dir)
            export_filename = f"{filename_preifx}/{filename_preifx}-{frame_ids[0]}.dcm"
            ds_file.save_as(
                f"{frame_dir}/{filename_preifx}-{frame_ids[0]}.dcm",
                write_like_original=False,
            )
            file_paths.append(export_filename)

        await aiosession.close()
        return file_paths

    async def export_dataset_to_folder(
        self,
        dataset_name: str,
        path: str,
        ignore_existing: bool = False,
        max_concurrency: int = MAX_CONCURRENCY,
        page_size: int = EXPORT_PAGE_SIZE,
    ) -> None:
        """Export dataset to folder."""
        # pylint: disable=too-many-locals
        first_iteration: bool = True
        end_cursor: Optional[str] = None
        dataset_root = f"{path}/{dataset_name}"
        console = Console()

        console.print(f"[bold green][\u2713] Saving dataset {dataset_name} to {path}")

        json_path = f"{dataset_root}/series.json"

        if not ignore_existing:
            series, ds_series_map = self._extract_series_map(json_path, console)
        else:
            series, ds_series_map = [], {}

        if not any([series, ds_series_map]):
            ignore_existing = True

        while first_iteration or (not first_iteration and end_cursor):
            ds_imports, end_cursor = self.context.dataset.get_data_store_imports(
                org_id=self.org_id,
                data_store=dataset_name,
                first=page_size,
                cursor=end_cursor,
            )
            message = f"Fetching {len(ds_imports)} items in this page"
            if end_cursor:
                message += ", more pages to come..."
            else:
                message += ", last page of the dataset."
            console.print(f"[bold green] [\u2713] {message}")
            file_paths_list = await gather_with_concurrency(
                max_concurrency,
                [
                    self.fetch_and_save_image_data(
                        item, dataset_root, console, ignore_existing
                    )
                    for item in ds_imports
                ],
            )
            first_iteration = False
            for ds_import, file_paths in zip(ds_imports, file_paths_list):
                if not file_paths:
                    if (
                        dataset_name in ds_series_map
                        and ds_import["seriesId"] in ds_series_map[dataset_name]
                    ):
                        continue
                    file_paths = (
                        (ds_series_map.get(dataset_name) or {}).get("seriesId") or {}
                    ).get("items") or []
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

    def _extract_series_map(
        self, json_path: str, console: Console
    ) -> Tuple[List[Dict], Dict]:
        """Extract series map."""
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as series_file:
                try:
                    series = json.load(series_file)
                    ds_series_map: Dict = {}
                    for series_item in series:
                        if series_item["dataset"] not in ds_series_map:
                            ds_series_map[series_item["dataset"]] = {}
                        ds_series_map[series_item["dataset"]][
                            series_item["seriesId"]
                        ] = series_item
                    return series, ds_series_map
                except Exception:  # pylint: disable=broad-exception-caught
                    console.print(
                        "[bold red] [!] Error reading series.json. It is either malformed or corrupted."
                    )
                    return [], {}
        return [], {}

    async def fetch_and_save_image_data(
        self,
        item: Dict,
        source_dir: str,
        console: Console,
        ignore_existing: bool = False,
    ) -> Optional[List[str]]:
        """Fetch and save image data."""
        # Check if the folder exists for the given seriesId
        if (not ignore_existing) and os.path.exists(f"{source_dir}/{item['seriesId']}"):
            console.print(
                f"\t[bold yellow] [!] Skipping {item['seriesId']} as it already exists."
            )
            return None
        console.print(f"\t[blue] [\u2713] Fetching {item['seriesId']}")
        image_content_url = item["url"]
        image_content_url = image_content_url.replace("altadb://", "")
        image_content_url = f"{self.context.client.base_url}{image_content_url}"
        async with aiohttp.ClientSession() as aiosession:
            response = await self.context.client.get_file_content_async(
                aiosession, image_content_url
            )
            res_json = json.loads(response)
            if not os.path.exists(source_dir):
                os.makedirs(source_dir)
            return await self.construct_images_from_metadata_and_url(
                aiosession=aiosession,
                res_json=res_json,
                source_dir=source_dir,
                filename_preifx=item["seriesId"],
            )
