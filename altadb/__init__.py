""""""

import sys
import asyncio

import nest_asyncio  # type: ignore

from altadb.common.context import AltaDBContext
from altadb.common.constants import DEFAULT_URL
from altadb.organization import AltaDBOrganization
from altadb.dataset import AltaDBDataset

from altadb.utils.logging import logger
from altadb.utils.common_utils import config_migration


from .config import config
from .version_check import version_check

__version__ = "0.0.5"

# windows event loop close bug https://github.com/encode/httpx/issues/914#issuecomment-622586610
try:
    if (
        sys.version_info[0] == 3
        and sys.version_info[1] >= 8
        and sys.platform.startswith("win")
    ):
        asyncio.set_event_loop_policy(  # type: ignore
            asyncio.WindowsSelectorEventLoopPolicy()  # type: ignore
        )
except Exception:  # pylint: disable=broad-except
    pass

# if there is a running event loop, apply nest_asyncio
try:
    if asyncio._get_running_loop() is None:  # pylint: disable=protected-access
        raise RuntimeError
    nest_asyncio.apply()
    logger.warning(
        "Applying nest-asyncio to a running event loop, this likely means you're in a jupyter"
        + " notebook and you can safely ignore this."
    )
except (RuntimeError, AttributeError):
    pass

try:
    config_migration()
except Exception:  # pylint: disable=broad-except
    pass


def version() -> str:
    """Check for latest version and return the current one."""
    version_check(__version__, config.check_version)
    return f"v{__version__}"


def _populate_context(context: AltaDBContext) -> AltaDBContext:
    # pylint: disable=import-outside-toplevel
    from altadb.repo import DatasetRepo, UploadRepo

    if context.config.debug:
        logger.debug(f"Using: altadb-sdk=={__version__}")

    context.dataset = DatasetRepo(context.client)
    context.upload = UploadRepo(context.client)
    return context


def get_org(
    org_id: str, api_key: str, secret: str, url: str = DEFAULT_URL
) -> AltaDBOrganization:
    """
    Get an existing altadb organization object.

    Organization object allows you to interact with your organization
    and perform high level actions like creating a project.

    >>> org = altadb.get_org(org_id, api_key)

    Parameters
    ---------------
    org_id: str
        Your organizations unique id https://altadb.com/<org_id>/.

    api_key: str
        Your secret api_key, can be created from the AltaDB platform.

    url: str = DEFAULT_URL
        Should default to https://altadb.com
    """
    context = _populate_context(AltaDBContext(api_key=api_key, secret=secret, url=url))
    return AltaDBOrganization(context, org_id)


def get_dataset(
    org_id: str, dataset: str, api_key: str, secret: str, url: str = DEFAULT_URL
) -> AltaDBDataset:
    """
    Get an existing AltaDB dataset object.

    Dataset objects allow you to interact with your AltaDB projects,
    and perform actions like importing data, exporting data etc.

    >>> dataset = altadb.get_dataset(org_id, project_id, api_key)

    Parameters
    ---------------
    org_id: str
        Your organizations unique id https://app.altadb.com/<org_id>/

    dataset: str
        Your projects unique id https://app.altadb.com/<org_id>/datasets/<dataset_name>

    api_key: str
        Your visible api_key, can be created from the AltaDB platform.

    secret: str
        Your secret key, can be created from the AltaDB platform.

    url: str = DEFAULT_URL
        Should default to https://app.altadb.com
    """
    context = _populate_context(AltaDBContext(api_key=api_key, secret=secret, url=url))
    return AltaDBDataset(context, org_id, dataset)


__all__ = [
    "__version__",
    "config",
    "version",
    "AltaDBContext",
    "AltaDBOrganization",
    "AltaDBDataset",
    "get_org",
    "get_dataset",
]
