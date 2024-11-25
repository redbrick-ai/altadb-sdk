from asyncio import run
import enum
import json
import os
from typing import Dict

import pydicom
import pydicom.dataset
import requests  # type: ignore
import altadb
import altadb.export
from altadb.repo.dataset import DatasetRepo
import altadb.export.public
from tests import marks

ALTADB_API_KEY = os.environ["ALTADB_API_KEY"]
ALTADB_SECRET_KEY = os.environ["ALTADB_SECRET_KEY"]
ALTADB_URL = os.environ["ALTADB_URL"]
ALTADB_ORG_ID = os.environ["ALTADB_ORG_ID"]
ALTADB_DATASET = os.environ["ALTADB_DATASET"]
ALTADB_SERIES_FILE_NAME = "series.json"
DATA_DIR = "data"

# List of folders that contain the test data
# The name of the folder should match the name of the dataset in the AltaDB
DATA_ITEMS = [
    "Brain110",
    "ProstatePT",
    "ModalitySM",
    "ModalityHC",
    "ModalityOT",
    "AbdominalMR",
]

ALTADB_DATASETS = [
    {
        "name": item,
        "local": f"data/{item}",
        "org": ALTADB_ORG_ID,
    }
    for item in os.listdir(os.path.join(os.path.dirname(__file__), DATA_DIR))
    if item in DATA_ITEMS
]


class ExactHeadersComparison(enum.Enum):
    """Enum to specify the exact headers comparison."""

    SOPClassUID = "00080016"
    SOPInstanceUID = "00080018"
    StudyInstanceUID = "0020000D"
    SeriesInstanceUID = "0020000E"
    PatientID = "00100020"
    PatientName = "00100010"
    StudyID = "00200010"
    StudyDate = "00080020"
    StudyTime = "00080030"
    ReferringPhysicianName = "00080090"
    AccessionNumber = "00080050"
    SeriesNumber = "00200011"
    Modality = "00080060"
    SeriesDescription = "0008103E"
    ImageNumber = "00200013"
    AcquisitionDate = "00080022"
    AcquisitionTime = "00080032"
    ImageType = "00080008"
    ImageComments = "00204000"
    ImagePositionPatient = "00200032"
    ImageOrientationPatient = "00200037"
    SliceLocation = "00201041"
    PixelSpacing = "00280030"
    SliceThickness = "00180050"
    Rows = "00280010"
    Columns = "00280011"
    SamplesPerPixel = "00280002"
    PhotometricInterpretation = "00280004"
    BitsAllocated = "00280100"
    BitsStored = "00280101"
    HighBit = "00280102"
    PixelRepresentation = "00280103"


def _get_series_metadata(series_url: str, headers: Dict[str, str]) -> dict:
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


@marks.parametrize(
    "altadb_dataset, local_dir, org_id",
    [
        (dataset["name"], dataset["local"], dataset["org"])
        for dataset in ALTADB_DATASETS
    ],
)
def test_export(tmpdir: str, altadb_dataset: str, local_dir: str, org_id: str) -> None:
    """Test that the export functionality works.

    Steps:
    1. Export the dataset to a temporary directory.
    2. Get a map of SOP Instance UID to metadata from the URL.
    3. Get a map of SOP Instance UID to metadata from the local DICOM files.
    4. For each series in the export, compare.

        4.1 The metadata from the URL.

        4.2 The metadata from the local DICOM files.

        4.3 The metadata from the exported DICOM files.

    """
    context = altadb.AltaDBContext(
        api_key=ALTADB_API_KEY,
        secret=ALTADB_SECRET_KEY,
        url=ALTADB_URL,
    )
    dataset = altadb.AltaDBDataset(
        context,
        org_id=org_id,
        dataset=altadb_dataset,
    )
    context.dataset = DatasetRepo(context.client)

    # Export the images to the path
    run(
        dataset.export.export_to_files(
            dataset_name=altadb_dataset,
            path=tmpdir,
        )
    )

    # Get the number of series in the dataset
    # The test data has a limited number of series
    series, cursor = context.dataset.get_data_store_import_series(
        org_id, altadb_dataset
    )
    if cursor:
        raise ValueError("Additional data has been added to the dataset.")
    # Get that the number of series in the path <tmpdir>/<DATASET> is the same as the number of series in the dataset
    # If the number of series is not the same, the export has failed
    num_series = os.listdir(os.path.join(tmpdir, altadb_dataset))
    assert ALTADB_SERIES_FILE_NAME in num_series
    num_series.remove(ALTADB_SERIES_FILE_NAME)
    if len(num_series) != len(series):
        raise ValueError(
            "The number of series in the dataset does not match the number of series in the export."
        )
    url_sop_metadata_map = _get_series_metadata(
        series[0]["url"], headers=context.client.headers
    )
    local_series_root = os.path.join(os.path.dirname(__file__), local_dir)
    local_dcm_files = []
    for file in os.listdir(local_series_root):
        local_dcm_files.append(os.path.join(local_series_root, file))
    local_sop_metadata_map = {}
    temp = []
    for original_dcm_file in local_dcm_files:
        ds = pydicom.dcmread(original_dcm_file, force=True)
        sop_instance_uid = ds.SOPInstanceUID
        local_sop_metadata_map[str(sop_instance_uid)] = ds.to_json_dict()
        x = ds.to_json_dict()
        # Remove pixel data
        del x["7FE00010"]
        temp.append(x)

    for exported_series_dir in os.listdir(os.path.join(tmpdir, altadb_dataset)):
        if exported_series_dir == ALTADB_SERIES_FILE_NAME:  # Skip the series.json file
            continue
        # The folder structure is <tmpdir>/<DATASET>/<series>/<dcm_file>
        temp_series_path = os.path.join(tmpdir, altadb_dataset, exported_series_dir)
        # Read the file with the metadata
        temp_dcm_files = os.listdir(temp_series_path)
        for dcm_file in temp_dcm_files:
            exported_dicom_ds = pydicom.dcmread(
                os.path.join(temp_series_path, dcm_file)
            )
            sop_instance_uid = str(exported_dicom_ds.SOPInstanceUID)
            exported_metadata = exported_dicom_ds.to_json_dict()
            url_metadata = url_sop_metadata_map[sop_instance_uid]
            original_metadata = local_sop_metadata_map[sop_instance_uid]

            for tag, value in exported_metadata.items():
                if tag == "7FE00010":  # Skip pixel data
                    continue
                if tag in url_metadata and tag in original_metadata:
                    assert value == url_metadata[tag] == original_metadata[tag]
