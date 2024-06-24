"""Interface for interacting with your AltaDB Projects."""

from altadb.common.context import AltaDBContext
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
