from asyncio import run
import os

import pydicom
import pydicom.dataset

import altadb
from altadb.repo.dataset import DatasetRepo

from tests import marks
from tests.utils import (
    build_sop_metadata_map_local,
    check_export_series_count,
    compare_directories_for_dicom,
    compare_metadata,
    get_altadb_datasets,
    build_sop_metadata_map_remote,
    get_single_data_store_import_series_if_exists,
)


ALTADB_ORG_ID = os.environ["ALTADB_ORG_ID"]


ALTADB_DATASETS = get_altadb_datasets(ALTADB_ORG_ID)


@marks.parametrize(
    "altadb_dataset, local_dir, org_id",
    [(dataset.name, dataset.local, dataset.org_id) for dataset in ALTADB_DATASETS],
)
def test_export_once(
    context: altadb.AltaDBContext,
    tmpdir: str,
    altadb_dataset: str,
    local_dir: str,
    org_id: str,
) -> None:
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
    dataset = altadb.AltaDBDataset(
        context,
        org_id=org_id,
        dataset=altadb_dataset,
    )
    # Export the images to the path
    run(
        dataset.export.export_to_files(
            dataset_name=altadb_dataset,
            path=tmpdir,
        )
    )
    # Get the number of series in the dataset
    # The test data has a limited number of series
    series = get_single_data_store_import_series_if_exists(
        context, org_id, altadb_dataset
    )
    # Get that the number of series in the path <tmpdir>/<DATASET>
    # is the same as the number of series in the dataset
    # If the number of series is not the same, the export has failed
    # Check that the series.json file is present
    check_export_series_count(os.path.join(tmpdir, altadb_dataset))
    url_sop_metadata_map = build_sop_metadata_map_remote(
        series["url"], headers=context.client.headers
    )
    local_sop_metadata_map = build_sop_metadata_map_local(local_dir)
    compare_directories_for_dicom(
        local_dir, os.path.join(tmpdir, altadb_dataset, series["seriesId"])
    )
    for sop_instance_uid, url_metadata in url_sop_metadata_map.items():
        compare_metadata(
            local_sop_metadata_map[sop_instance_uid],
            url_metadata,
        )
