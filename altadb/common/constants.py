"""Constants."""

MAX_CONCURRENCY = 30
MAX_FILE_BATCH_SIZE = 1000
MAX_UPLOAD_CONCURRENCY = 5
MAX_FILE_UPLOADS = 50
MAX_RETRY_ATTEMPTS = 3
REQUEST_TIMEOUT = 30
EXPORT_PAGE_SIZE = 50

DEFAULT_URL = "https://app.altadb.com"

PEERLESS_ERRORS = (
    KeyboardInterrupt,
    PermissionError,
    TimeoutError,
    ConnectionError,
    ValueError,
    SystemError,
    SystemExit,
)
