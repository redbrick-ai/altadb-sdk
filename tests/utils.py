"""Utility functions for the tests."""

from asyncio import run
from dataclasses import dataclass
import os
from time import sleep
from typing import Dict, List

import pydicom
import requests  # type: ignore

import altadb
from tests.contstants import (
    ALTADB_SERIES_FILE_NAME,
    DATA_DIR,
    DATA_ITEMS,
    ExactHeadersComparison,
    MAX_SLEEP_TIME,
    ResourceStatus,
)


@dataclass
class DataSetItem:
    name: str
    local: str
    org_id: str


def get_altadb_datasets(org_id: str) -> List[DataSetItem]:
    return [
        DataSetItem(
            item, os.path.join(os.path.dirname(__file__), DATA_DIR, item), org_id
        )
        for item in os.listdir(os.path.join(os.path.dirname(__file__), DATA_DIR))
        if item in DATA_ITEMS
    ]


def build_sop_metadata_map_remote(
    series_url: str, headers: Dict[str, str]
) -> Dict[str, Dict]:
    """Get the series metadata using the AltaDB series URL.

    Returns
    -------
    dict
        The SOPInstanceUID to metadata map.

    Structure of the metadata:
    {
        "SOPInstanceUID": {
            "8 digit tag value": {
                "Value": ["value"],
                "vr": "vr",
            },
        }
    }
    """
    series_url = series_url.replace("altadb://", "https://preview.altadb.com")
    response = requests.get(
        series_url,
        headers=headers,
    )
    sop_instance_uid_metadata_map = {}
    for item in response.json()["metaData"]["instances"]:
        series_metadata = item["metaData"]
        sop_instance_uid_metadata_map[
            series_metadata[ExactHeadersComparison.SOPInstanceUID.value]["Value"][0]
        ] = series_metadata
    return sop_instance_uid_metadata_map


def check_export_series_count(
    dir_name: str,
) -> None:
    """
    Check that the number of series in the path <tmpdir>/<DATASET>
    is the same as the number of series in the dataset.

    If the number of series is not the same, the export has failed.

    Args
    ----
    dir_name: str
        The path to the dataset directory.

    Raises
    ------
    ValueError
        If the number of series in the dataset does not match the number of series in the export.
    """
    all_series = os.listdir(dir_name)
    assert ALTADB_SERIES_FILE_NAME in all_series
    all_series.remove(ALTADB_SERIES_FILE_NAME)
    if len(all_series) != 1:
        raise ValueError(
            "The number of series in the dataset does not match the number of series in the export."
        )


def upload_export(
    org_id: str,
    context: altadb.AltaDBContext,
    dataset: altadb.AltaDBDataset,
    new_dataset: str,
    export_dir1: str,
    import_id: str,
):
    """Upload the exported dataset to AltaDB and wait for the dataset to be created."""
    run(dataset.upload.upload_files(new_dataset, export_dir1, import_name=import_id))

    # Wait for max 10 mins till the images are processed by the server.
    total_slept = 0
    # First wait for one minute.
    sleep(60)
    total_slept += 60
    # pylint: disable=unused-variable
    imports, cursor = context.dataset.get_data_store_imports(org_id, new_dataset)
    # then wait for 10 seconds till the images are processed by the server.
    while total_slept < MAX_SLEEP_TIME:
        # pylint: disable=unused-variable
        imports, cursor = context.dataset.get_data_store_imports(org_id, new_dataset)
        import_item = imports[0]
        if import_item["status"] in [
            ResourceStatus.CREATION_FAILURE.value,
            ResourceStatus.CREATION_PARTIAL.value,
        ]:
            raise ValueError("The dataset creation has failed.")
        if import_item["status"] == ResourceStatus.CREATION_SUCCESS.value:
            break
        sleep(10)
        total_slept += 10
    if import_item["status"] != ResourceStatus.CREATION_SUCCESS.value:
        raise ValueError("The dataset creation has failed.")


def build_sop_metadata_map_local(local_dir: str) -> Dict[str, Dict]:
    """Build a SOPInstanceUID to metadata map for the local DICOM files."""
    sop_metadata_map = {}
    for _original_dcm_file in os.listdir(local_dir):
        # Handle local cases when you've hidden files like .DS_Store
        original_dcm_file = os.path.join(local_dir, _original_dcm_file)
        if not original_dcm_file.endswith(".dcm"):
            continue
        ds = pydicom.dcmread(original_dcm_file, force=True)
        sop_instance_uid = ds.SOPInstanceUID
        ds_json_dict = ds.to_json_dict()
        if "7FE00010" in ds_json_dict:
            del ds_json_dict["7FE00010"]  # PixelData
        if "00282000" in ds_json_dict:
            del ds_json_dict["00282000"]  # ICC Profile, present in Modality SM
        if "FFFCFFFC" in ds_json_dict:
            del ds_json_dict["FFFCFFFC"]
        sop_metadata_map[str(sop_instance_uid)] = ds_json_dict
        # Check that it has at least one of the required tags
        assert "00080016" in sop_metadata_map[sop_instance_uid]  # SOPClassUID
        assert "00080018" in sop_metadata_map[sop_instance_uid]  # SOPInstanceUID
    return sop_metadata_map


def compare_metadata(metadata1: Dict[str, Dict], metadata2: Dict[str, Dict]) -> None:
    """Compare the metadata of two DICOM files."""
    for sop_instance_uid, metadata in metadata1.items():
        assert metadata2[sop_instance_uid] == metadata


def compare_exported_datasets(dataset1: str, dataset2: str) -> None:
    """Check if the number of directories in two directories are the same."""
    assert len(os.listdir(dataset1)) == len(os.listdir(dataset2))
    dir_series_map1: Dict[str, Dict] = {}
    dir_series_map2: Dict[str, Dict] = {}
    # Read all DICOM files, and map thei SOPInstanceUID to the metadata
    for series_dir in os.listdir(dataset1):
        if series_dir == ALTADB_SERIES_FILE_NAME:
            continue
        dir_series_map1 = build_sop_metadata_map_local(
            os.path.join(dataset1, series_dir)
        )
    for series_dir in os.listdir(dataset2):
        if series_dir == ALTADB_SERIES_FILE_NAME:
            continue
        dir_series_map2 = build_sop_metadata_map_local(
            os.path.join(dataset2, series_dir)
        )
    compare_metadata(dir_series_map1, dir_series_map2)


def compare_directories_for_dicom(dir1: str, dir2: str) -> None:
    """Compare that two directories have the same DICOM files."""
    # Use os.walk to get all the files in the directory
    dir_series_map1 = build_sop_metadata_map_local(dir1)
    dir_series_map2 = build_sop_metadata_map_local(dir2)
    compare_metadata(dir_series_map1, dir_series_map2)


def get_single_data_store_import_series_if_exists(
    context: altadb.AltaDBContext, org_id: str, dataset: str
) -> Dict[str, str]:
    """Get the single data store import series if it exists."""
    series, cursor = context.dataset.get_data_store_import_series(org_id, dataset)
    if cursor:
        raise ValueError("Additional data has been added to the dataset.")
    assert len(series) == 1
    return series[0]
