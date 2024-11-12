"""Decode DICOM images from metadata and URL."""

import json
import os
import asyncio
from typing import Dict, List, Optional
import aiohttp

from altadb.common.context import AltaDBContext
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
    ) -> None:
        """Construct a DICOM image from metadata and URL."""
        image_frames_urls: Dict[str, str] = {}
        # Get the path of each imageFrame
        for image_frame in res_json.get("imageFrames") or []:
            image_frames_urls[image_frame["id"]] = image_frame["path"]

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
            ds_file = create_dicom_dataset(
                instance_metadata, frame_contents, len(frame_ids)
            )
            frame_dir = f"{source_dir}/{filename_preifx}"
            if not os.path.exists(frame_dir):
                os.makedirs(frame_dir)

            ds_file.save_as(
                f"{frame_dir}/{filename_preifx}-{frame_ids[0]}.dcm",
                write_like_original=False,
            )
        await aiosession.close()

    async def export_dataset_to_folder(
        self,
        dataset_name: str,
        path: str,
    ) -> None:
        """Export dataset to folder."""
        first_iteration: bool = True
        end_cursor: Optional[str] = None
        while first_iteration or (not first_iteration and end_cursor):
            ds_imports = self.context.dataset.get_data_store_imports(
                org_id=self.org_id, data_store=dataset_name, cursor=end_cursor
            )
            await asyncio.gather(
                *[
                    self.fetch_and_save_image_data(
                        index, item, f"{path}/{dataset_name}"
                    )
                    for index, item in enumerate(ds_imports)
                ]
            )
            first_iteration = False
            end_cursor = ds_imports[-1].get("cursor")

    async def fetch_and_save_image_data(
        self, index: int, item: Dict, source_dir: str
    ) -> None:
        """Fetch and save image data."""
        image_content_url = item["url"]
        series_id = item["seriesId"]
        image_content_url = image_content_url.replace("altadb://", "")
        image_content_url = f"{self.context.client.base_url}{image_content_url}"
        async with aiohttp.ClientSession() as aiosession:
            response = await self.context.client.get_file_content_async(
                aiosession, image_content_url
            )
            res_json = json.loads(response)
            if not os.path.exists(source_dir):
                os.makedirs(source_dir)
            with open(
                f"{source_dir}/item-{index + 1}.json", "w+", encoding="utf-8"
            ) as file:
                json.dump(res_json, file, indent=2)
            filename = series_id
            await self.construct_images_from_metadata_and_url(
                aiosession=aiosession,
                res_json=res_json,
                source_dir=source_dir,
                filename_preifx=filename,
            )
