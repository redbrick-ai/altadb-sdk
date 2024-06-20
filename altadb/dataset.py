"""Interface for interacting with your AltaDB Projects."""

from altadb.common.context import AltaDBContext


class AltaDBDataset:
    """
    Representation of an AltaDB dataset.

    The :attr:`altadb.dataset.AltaDBDataset` object allows you to programmatically interact with
    your AltaDB dataset. You can upload data. Retrieve the project object in the following way:

    .. code:: python

        >>> project = altadb.get_dataset(org_id="", dataset="", api_key="", secret="", url="")
    """

    def __init__(self, context: AltaDBContext, org_id: str, dataset: str) -> None:
        """Construct RBProject."""
        self.context = context
        self._org_id = org_id
        self._dataset = dataset

    @property
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this project belongs to
        """
        return self._org_id

    @property
    def project_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Project ID UUID.
        """
        return self._dataset

    def __str__(self) -> str:
        return f"AltaDB Dataset: {self.org_id}/{self._dataset}"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    @property
    def name(self) -> str:
        """Retrieve unique name of this project."""
        return self._dataset
