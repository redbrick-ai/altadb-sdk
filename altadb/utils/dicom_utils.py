"""Utility functions for DICOM files."""

import pydicom
import pydicom.dataset


def move_group2_to_file_meta(dataset: pydicom.Dataset) -> pydicom.Dataset:
    """Move all group 2 elements to file meta.

    Args
    ----
    metadata_dcm_dataset: pydicom.Dataset
        The metadata of the DICOM file.
    """
    if not hasattr(dataset, "file_meta"):
        dataset.file_meta = pydicom.dataset.FileMetaDataset()

    for elem in dataset:
        if elem.tag.group == 2:
            dataset.file_meta.add(elem)
            del dataset[elem.tag]

    return dataset
