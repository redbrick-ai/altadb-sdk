"""Interface for interacting with your AltaDB Projects."""

import asyncio
from typing import Optional
from altadb.common.constants import EXPORT_PAGE_SIZE, MAX_CONCURRENCY
from altadb.common.context import AltaDBContext
from altadb.export.public import Export
from altadb.upload.public import Upload


class AltaDBDataset:
    """
    Representation of an AltaDB dataset.

    The :attr:`altadb.dataset.AltaDBDataset` object allows you to programmatically interact with
    your AltaDB dataset. You can upload data. Retrieve the dataset object in the following way:

    .. code:: python

        >>> dataset = altadb.get_dataset(org_id="", dataset="", api_key="", secret="", url="")
    """

    def __init__(self, context: AltaDBContext, org_id: str, dataset: str) -> None:
        """Construct RBProject."""
        self.context = context
        self._org_id = org_id
        self._dataset = dataset
        self.upload = Upload(self.context, self._org_id, self._dataset)
        self.export = Export(self.context, self._org_id, self._dataset)

    @property
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this dataset belongs to
        """
        return self._org_id

    def __str__(self) -> str:
        """Representation of object."""
        return f"AltaDB Dataset: {self._dataset}"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    @property
    def name(self) -> str:
        """Retrieve unique name of this project."""
        return self._dataset

    def export_to_files(
        self,
        path: str,
        max_concurrency: int = MAX_CONCURRENCY,
        page_size: int = EXPORT_PAGE_SIZE,
        series: Optional[str] = None,
    ) -> None:
        """
        Export the dataset files to a local folder.

        :param path: The folder to export the dataset to
        :param max_concurrency: The maximum number of concurrent files to download
        :param page_size: The number of series to download
        """
        asyncio.run(
            self.export.export_dataset_to_folder(
                self.name, path, max_concurrency, page_size, series
            )
        )
