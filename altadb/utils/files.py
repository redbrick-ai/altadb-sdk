"""Handler for file upload/download."""

import os
import gzip
from typing import Any, Callable, Dict, List, Optional, Tuple, Set

import asyncio
import aiohttp

import pydicom
import pydicom.dataset
import pydicom.encaps
import pydicom.tag
import pydicom.uid

from yarl import URL
from tenacity import Retrying, RetryError
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_random_exponential
from natsort import natsorted, ns

from altadb.common.constants import (
    DEFAULT_URL,
    MAX_CONCURRENCY,
    MAX_FILE_BATCH_SIZE,
    MAX_FILE_UPLOADS,
    MAX_RETRY_ATTEMPTS,
)
from altadb.utils.async_utils import gather_with_concurrency
from altadb.utils.logging import log_error, logger
from altadb.config import config


IMAGE_FILE_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "bmp": "image/bmp",
    "dcm": "application/dicom",
}

VIDEO_FILE_TYPES = {
    "mp4": "video/mp4",
    "avi": "video/x-msvideo",
    "dcm": "application/dicom",
}

DICOM_FILE_TYPES = {
    "": "application/dicom",
    "dcm": "application/dicom",
    "ima": "application/dicom",
    "dicom": "application/dicom",
}

JSON_FILE_TYPES = {"json": "application/json"}

NIFTI_FILE_TYPES = {"nii": "application/octet-stream"}

NRRD_FILE_TYPES = {"nrrd": "application/octet-stream"}

FILE_TYPES = {
    **IMAGE_FILE_TYPES,
    **VIDEO_FILE_TYPES,
    **DICOM_FILE_TYPES,
    **JSON_FILE_TYPES,
    **NIFTI_FILE_TYPES,
    **NRRD_FILE_TYPES,
}

ALL_FILE_TYPES = {"*": "*/*"}


def get_file_type(file_path: str) -> Tuple[str, str]:
    """
    Return file type.

    Return
    ------------
    [file_ext, file_type]
        file_ext: png, jpeg, jpg etc.
        file_type: this is the MIME file type e.g. image/png
    """
    file_path, file_ext = os.path.splitext(file_path.lower())
    if file_ext == ".gz":
        file_path, file_ext = os.path.splitext(file_path)
    file_ext = file_ext.lstrip(".")

    if file_ext not in FILE_TYPES:
        raise ValueError(
            f"Unsupported file type {file_ext}! Only {','.join(FILE_TYPES.keys())} are supported"
        )
    return file_ext, FILE_TYPES[file_ext]


def find_files_recursive(
    root: str, file_types: Set[str], multiple: bool = False
) -> List[List[str]]:
    """Find files recursively in a directory, that belong to a list of allowed file types."""
    if not os.path.isdir(root):
        return []

    items = []
    list_items = []
    discard_list_items = False

    for item in os.listdir(root):
        if item.startswith("."):
            continue
        path = os.path.join(root, item)
        if os.path.isdir(path):
            items.extend(find_files_recursive(path, file_types, multiple))
            discard_list_items = True
        elif os.path.isfile(path) and (  # pylint: disable=too-many-boolean-expressions
            "*" in file_types
            or (
                item.rsplit(".", 1)[-1].lower() in file_types
                or (
                    "." in item
                    and item.rsplit(".", 1)[-1].lower() == "gz"
                    and item.rsplit(".", 2)[-2].lower() in file_types
                )
            )
        ):
            if multiple:
                if not discard_list_items:
                    list_items.append(path)
            else:
                items.append([path])
        else:
            discard_list_items = True

    if (
        not discard_list_items
        and len({item.rsplit(".", 1)[-1].lower() for item in list_items}) == 1
    ):
        items.append(list(natsorted(list_items, alg=ns.IGNORECASE)))  # type: ignore

    return items


def uniquify_path(path: str) -> str:
    """Provide unique path with number index."""
    filename, extension = os.path.splitext(path)
    if extension == ".gz":
        filename, extension = os.path.splitext(filename)
        extension += ".gz"

    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


def is_gzipped_data(data: bytes) -> bool:
    """Check if data is gzipped."""
    return data[:2] == b"\x1f\x8b"


def is_dicom_file(file_name: str) -> bool:
    """Check if data is dicom."""
    with open(file_name, "rb") as fp_:
        data = fp_.read()

    if is_gzipped_data(data):
        data = gzip.decompress(data)

    return data[128:132] == b"\x44\x49\x43\x4d"


async def upload_files(
    files: List[Tuple[str, str, str]],
    progress_bar_name: Optional[str] = "Uploading files",
    keep_progress_bar: bool = True,
    upload_callback: Optional[Callable] = None,
) -> List[bool]:
    """Upload files from local path to url (file path, presigned url, file type)."""

    async def _upload_file(
        session: aiohttp.ClientSession, path: str, url: str, file_type: str
    ) -> bool:
        if not path or not url or not file_type:
            return False

        with open(path, mode="rb") as file_:
            data = file_.read()

        status: int = 0

        headers = {"Content-Type": file_type}
        if not is_gzipped_data(data) and file_type != DICOM_FILE_TYPES[""]:
            headers["Content-Encoding"] = "gzip"
            data = gzip.compress(data)

        try:
            for attempt in Retrying(
                reraise=True,
                stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
                wait=wait_random_exponential(min=5, max=30),
                retry=retry_if_not_exception_type(KeyboardInterrupt),
            ):
                with attempt:
                    request_params: Dict[str, Any] = {
                        "headers": headers,
                        "data": data,
                    }
                    if not config.verify_ssl:
                        request_params["ssl"] = False
                    async with session.put(url, **request_params) as response:
                        status = response.status
        except RetryError as error:
            raise Exception("Unknown problem occurred") from error

        if status == 200:
            if upload_callback:
                upload_callback()
            return True
        raise ConnectionError(f"Error in uploading {path} to AltaDB")

    conn = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [
            _upload_file(session, path, url, file_type)
            for path, url, file_type in files
        ]
        uploaded = await gather_with_concurrency(
            MAX_FILE_UPLOADS,
            coros,
            progress_bar_name,
            keep_progress_bar,
        )

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return uploaded


async def download_files(
    files: List[Tuple[Optional[str], Optional[str]]],
    progress_bar_name: Optional[str] = "Downloading files",
    keep_progress_bar: bool = True,
    overwrite: bool = False,
    zipped: bool = False,
) -> List[Optional[str]]:
    """Download files from url to local path (presigned url, file path)."""

    async def _download_file(
        session: aiohttp.ClientSession, url: Optional[str], path: Optional[str]
    ) -> Optional[str]:
        # pylint: disable=no-member
        if not url or not path:
            logger.debug(f"Downloading empty '{url}' to '{path}'")
            return None

        if not overwrite and os.path.isfile(path):
            return path

        headers: Dict = {}
        data: Optional[bytes] = None

        try:
            for attempt in Retrying(
                reraise=True,
                stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
                wait=wait_random_exponential(min=5, max=30),
                retry=retry_if_not_exception_type(KeyboardInterrupt),
            ):
                with attempt:
                    request_params: Dict[str, Any] = {}
                    if not config.verify_ssl:
                        request_params["ssl"] = False
                    async with session.get(
                        URL(url, encoded=True), **request_params
                    ) as response:
                        if response.status == 200:
                            headers = dict(response.headers)
                            data = await response.read()
        except RetryError as error:
            log_error(error)
            raise Exception("Unknown problem occurred") from error

        if not data:
            logger.debug(f"Received empty data from '{url}'")
            return None

        if not zipped and headers.get("Content-Encoding") == "gzip":
            try:
                data = gzip.decompress(data)
            except Exception:  # pylint: disable=broad-except
                pass
        if zipped and not is_gzipped_data(data):
            data = gzip.compress(data)
        if zipped and not path.endswith(".gz"):
            path += ".gz"
        if not overwrite:
            path = uniquify_path(path)
        with open(path, "wb") as file_:
            file_.write(data)
        return path

    dirs: Set[str] = set()
    for _, path in files:
        if not path:
            continue
        parent = os.path.dirname(path)
        if parent in dirs:
            continue
        if not os.path.isdir(parent):
            logger.debug(f"Creating parent dir for {path}")
            os.makedirs(parent, exist_ok=True)
        dirs.add(parent)

    conn = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [_download_file(session, url, path) for url, path in files]
        paths = await gather_with_concurrency(
            MAX_FILE_BATCH_SIZE,
            coros,
            progress_bar_name,
            keep_progress_bar,
            True,
        )
        await session.close()

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return [(path if isinstance(path, str) else None) for path in paths]


async def save_dicom_series(
    altadb_meta_content_url: str,
    series_dir: str,
    base_url: str = DEFAULT_URL,
    headers: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Save DICOM files using AltaDB URLs.
    Given an AltaDB URL containing the metadata and image frames.

    Save the DICOM files to the destination directory.
    One DICOM file can contain multiple image frames.

    Args
    ------------
    altadb_meta_content_url: str
        AltaDB URL containing the metadata and image frames.
        This URL can be signed or unsigned.
    base_dir: str
        Destination directory to save the DICOM files.
    base_url: str
        Base URL for the AltaDB API.
    headers: Optional[Dict[str, str]]
        Headers to be used for the HTTP requests.
        If the altaDB_meta_content_url is unsigned, the headers should contain the authorization token.

    Returns
    ------------
    List[str]
        List of the saved DICOM files relative to the dataset root.
    """
    # pylint: disable=too-many-locals
    os.makedirs(series_dir, exist_ok=True)

    async def save_dicom_dataset(
        instance_metadata: Dict,
        instance_frames_metadata: List[Dict],
        presigned_image_urls: List[str],
        destination_file: str,
        aiosession: aiohttp.ClientSession,
    ) -> None:
        """Create and save a DICOM dataset using metadata and image frame URLs.

        Args
        ------------
        instance_metadata: Dict
            Metadata of the instance.
        instance_frames_metadata: List[Dict]
            Metadata of the instance frames.
        presigned_image_urls: List[str]
            Presigned URLs of the image frames.
        destination_file: str
            Destination file to save the DICOM dataset.
        aiosession: aiohttp.ClientSession
            aiohttp ClientSession to be used for the HTTP requests.
        """

        async def get_image_content(
            aiosession: aiohttp.ClientSession, image_url: str
        ) -> bytes:
            """Get image content."""
            async with aiosession.get(image_url) as response:
                return await response.content.read()

        frame_contents = await gather_with_concurrency(
            MAX_FILE_BATCH_SIZE,
            [
                get_image_content(aiosession, image_url=image_frame_url)
                for image_frame_url in presigned_image_urls
            ],
        )

        ds_file = pydicom.Dataset.from_json(instance_metadata)
        ds_file.TransferSyntaxUID = pydicom.uid.UID(
            instance_frames_metadata[0]["metaData"]["00020010"]["Value"][0]
        )

        # Move the file meta information to the dataset file meta
        if not hasattr(ds_file, "file_meta"):
            ds_file.file_meta = pydicom.dataset.FileMetaDataset()

        # Iterate through the dataset and copy Group 2 elements
        for elem in ds_file:
            if elem.tag.group == 2:  # Check if the element belongs to Group 2
                ds_file.file_meta.add_new(elem.tag, elem.VR, elem.value)
                del ds_file[elem.tag]  # Remove the element from the dataset

        ds_file.PixelData = pydicom.encaps.encapsulate(frame_contents)

        # PATCH/START: add HTJ2KLosslessRPCL to pydicom
        from pydicom.uid import (  # pylint: disable=import-outside-toplevel
            UID_dictionary,
            AllTransferSyntaxes,
            JPEG2000TransferSyntaxes,
        )

        HTJ2KLosslessRPCL = pydicom.uid.UID(  # pylint: disable=invalid-name
            "1.2.840.10008.1.2.4.202"
        )
        AllTransferSyntaxes.append(HTJ2KLosslessRPCL)
        JPEG2000TransferSyntaxes.append(HTJ2KLosslessRPCL)
        UID_dictionary[HTJ2KLosslessRPCL] = (
            "High-Throughput JPEG 2000 with RPCL Options Image Compression (Lossless Only)",
            "Transfer Syntax",
            "",
            "",
            "HTJ2KLosslessRPCL",
        )
        # PATCH/END: add HTJ2KLosslessRPCL to pydicom

        if ds_file.file_meta.TransferSyntaxUID == HTJ2KLosslessRPCL:
            ds_file.is_little_endian = True
            ds_file.is_implicit_VR = False
        ds_file.save_as(destination_file, write_like_original=False)
        logger.debug(f"Saved DICOM dataset to {destination_file}")

    res: List[str] = []
    if altadb_meta_content_url.startswith("altadb:///"):
        altadb_meta_content_url = "".join([base_url, "/", altadb_meta_content_url[10:]])
    elif altadb_meta_content_url.startswith("altadb://"):
        altadb_meta_content_url = altadb_meta_content_url.replace(
            "altadb://", "https://"
        )

    async with aiohttp.ClientSession() as aiosession:
        async with aiosession.get(altadb_meta_content_url, headers=headers) as response:
            res_json = await response.json()
            frameid_url_map: Dict[str, str] = {
                frame["id"]: frame["path"] for frame in res_json.get("imageFrames", [])
            }

            tasks = []
            for instance in res_json["metaData"]["instances"]:
                frame_ids = [frame["id"] for frame in instance["frames"]]
                image_frames_urls = [
                    frameid_url_map[frame_id] for frame_id in frame_ids
                ]
                file_from_dataset_root = os.path.join(
                    series_dir, f"{instance['frames'][0]['id']}.dcm"
                )
                tasks.append(
                    save_dicom_dataset(
                        instance["metaData"],
                        instance["frames"],
                        image_frames_urls,
                        file_from_dataset_root,
                        aiosession,
                    )
                )
                res.append(file_from_dataset_root)

            await gather_with_concurrency(
                MAX_CONCURRENCY,
                tasks,
                f"Saving series {series_dir.split('/')[-1]}",
                keep_progress_bar=False,
            )

    return res
