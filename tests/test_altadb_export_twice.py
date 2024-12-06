"""Test exporting a dataset to AltaDB twice."""

from asyncio import run
import os
import uuid

import altadb
import altadb.export
import altadb.export.public

from tests import marks
from tests.utils import (
    check_export_series_count,
    compare_directories_for_dicom,
    upload_export,
    compare_exported_datasets,
)

from .contstants import get_altadb_datasets


ALTADB_API_KEY = os.environ["ALTADB_API_KEY"]
ALTADB_SECRET_KEY = os.environ["ALTADB_SECRET_KEY"]
ALTADB_URL = os.environ["ALTADB_URL"]
ALTADB_ORG_ID = os.environ["ALTADB_ORG_ID"]

ALTADB_DATASETS = get_altadb_datasets(ALTADB_ORG_ID)


@marks.parametrize(
    "altadb_dataset, local_dir, org_id",
    [
        (dataset["name"], dataset["local"], dataset["org"])
        for dataset in ALTADB_DATASETS
    ],
)
def test_export_twice(
    tmpdir: str, altadb_dataset: str, local_dir: str, org_id: str
) -> None:
    """Test uploading the exported dataset to AltaDB.

    Steps:
    1. Export the dataset to a temporary directory (export v1).
    2. Upload the dataset to AltaDB.
    3. Export the dataset to a temporary directory (export v2).

    Expected result:
    The two exports should be the same.
    Their pixel data and metadata should be the exactly same, no difference.

    Directory for first export: tmpdir/e1
    Directory for second export: tmpdir/e2
    """
    context = altadb.AltaDBContext(ALTADB_API_KEY, ALTADB_SECRET_KEY, ALTADB_URL)
    dataset = altadb.AltaDBDataset(context, org_id, altadb_dataset)
    altadb._populate_context(context)
    new_dataset = f"{altadb_dataset}v2"

    # If the new dataset already exists, delete it.
    exists = context.dataset.check_if_exists(org_id, new_dataset)
    if exists:
        context.dataset.delete_dataset(org_id, new_dataset)
    context.dataset.create_dataset(org_id, new_dataset)

    # Export the dataset to a temporary directory (export v1).
    export_dir1 = os.path.join(tmpdir, "e1")
    run(dataset.export.export_to_files(altadb_dataset, export_dir1))
    # Get the number of series in the export v1.
    series, cursor = context.dataset.get_data_store_import_series(
        org_id, altadb_dataset
    )
    if cursor:
        raise ValueError("Additional data has been added to the dataset.")
    check_export_series_count(export_dir1, altadb_dataset, series)

    # Upload the dataset to AltaDB.
    import_id = str(uuid.uuid4())
    upload_export(org_id, context, dataset, new_dataset, export_dir1, import_id)

    # Export the dataset to a temporary directory (export v2).
    export_dir2 = os.path.join(tmpdir, "e2")

    #
    run(dataset.export.export_to_files(new_dataset, export_dir2))
    # Get the number of series in the export v2.
    series, cursor = context.dataset.get_data_store_import_series(org_id, new_dataset)
    if cursor:
        raise ValueError("Additional data has been added to the dataset.")
    check_export_series_count(export_dir2, new_dataset, series)

    # Compare the two exports.
    compare_exported_datasets(
        f"{export_dir1}/{altadb_dataset}", f"{export_dir2}/{new_dataset}"
    )

    series_id = series[0]["seriesId"]

    compare_directories_for_dicom(local_dir, f"{export_dir2}/{new_dataset}/{series_id}")

    # # Delete the new dataset.
    context.dataset.delete_dataset(org_id, new_dataset)
