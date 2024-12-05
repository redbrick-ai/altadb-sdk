"""Utility functions for the tests."""

from asyncio import run
import os
from time import sleep
from typing import Dict
import pydicom
import requests  # type: ignore

import altadb
from tests.contstants import (
    ALTADB_SERIES_FILE_NAME,
    MAX_SLEEP_TIME,
    ExactHeadersComparison,
    ResourceStatus,
)


def get_series_metadata(series_url: str, headers: Dict[str, str]) -> dict:
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


def check_export_series_count(dir_name: str, altadb_dataset: str, series: str) -> None:
    num_series = os.listdir(os.path.join(dir_name, altadb_dataset))
    assert ALTADB_SERIES_FILE_NAME in num_series
    num_series.remove(ALTADB_SERIES_FILE_NAME)
    if len(num_series) != len(series):
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
    imports = context.dataset.get_data_store_imports(org_id, new_dataset)
    # then wait for 10 seconds till the images are processed by the server.
    while total_slept < MAX_SLEEP_TIME:
        imports, cursor = context.dataset.get_data_store_imports(org_id, new_dataset)
        series = imports[0]
        if series["status"] in [
            ResourceStatus.CREATION_FAILURE.value,
            ResourceStatus.CREATION_PARTIAL.value,
        ]:
            raise ValueError("The dataset creation has failed.")
        if series["status"] == ResourceStatus.CREATION_SUCCESS.value:
            break
        total_slept += 10
    if series["status"] != ResourceStatus.CREATION_SUCCESS.value:
        raise ValueError("The dataset creation has failed.")


def compare_exported_datasets(dataset1: str, dataset2: str) -> None:
    """Check if the number of directories in two directories are the same."""
    assert len(os.listdir(dataset1)) == len(os.listdir(dataset2))
    # assert len(os.listdir(os.path.join(dataset1, os.listdir(dataset1)[0]))) == len(
    #     os.listdir(os.path.join(dataset2, os.listdir(dataset2)[0]))
    # )
    dir_series_map1 = {}
    dir_series_map2 = {}
    # Read all DICOM files, and map thei SOPInstanceUID to the metadata
    for series_dir in os.listdir(dataset1):
        if series_dir == ALTADB_SERIES_FILE_NAME:
            continue
        series_path = os.path.join(dataset1, series_dir)
        for dcm_file in os.listdir(series_path):
            ds = pydicom.dcmread(os.path.join(series_path, dcm_file), force=True)
            sop_instance_uid = ds.SOPInstanceUID
            # Remove the PixelData from the metadata
            ds_json_dict = ds.to_json_dict()
            if "7FE00010" in ds_json_dict:
                del ds_json_dict["7FE00010"]
            dir_series_map1[sop_instance_uid] = ds_json_dict
    for series_dir in os.listdir(dataset2):
        if series_dir == ALTADB_SERIES_FILE_NAME:
            continue
        series_path = os.path.join(dataset2, series_dir)
        for dcm_file in os.listdir(series_path):
            ds = pydicom.dcmread(os.path.join(series_path, dcm_file), force=True)
            sop_instance_uid = ds.SOPInstanceUID
            # Remove the PixelData from the metadata
            ds_json_dict = ds.to_json_dict()
            if "7FE00010" in ds_json_dict:
                del ds_json_dict["7FE00010"]
            dir_series_map2[sop_instance_uid] = ds_json_dict
    # Compare the metadata
    for sop_instance_uid, metadata in dir_series_map1.items():
        assert dir_series_map2[sop_instance_uid] == metadata
