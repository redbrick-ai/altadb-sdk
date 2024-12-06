"""Constants used in the tests."""

from enum import Enum


ALTADB_SERIES_FILE_NAME = "series.json"
DATA_DIR = "data"
MAX_SLEEP_TIME = 900

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


class ExactHeadersComparison(Enum):
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


class ResourceStatus(Enum):
    """Status of a resource."""

    CREATION_PENDING = "CREATION_PENDING"
    CREATING = "CREATING"
    CREATION_PROGRESS = "CREATION_PROGRESS"
    CREATION_PARTIAL = "CREATION_PARTIAL"
    CREATION_SUCCESS = "CREATION_SUCCESS"
    CREATION_FAILURE = "CREATION_FAILURE"
    REMOVING = "REMOVING"
