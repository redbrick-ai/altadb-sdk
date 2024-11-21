"""Organization class."""

from typing import Dict, List
from altadb.common.context import AltaDBContext


class AltaDBOrganization:
    """
    Representation of AltaDB organization.

    The :attr:`altadb.organization.AltaDBOrganization` object allows you to programmatically interact with
    your AltaDB organization. This class provides methods for querying your
    organization and doing other high level actions. Retrieve the organization object in the following way:

    .. code:: python

        >>> org = altadb.get_org(api_key="", org_id="")
    """

    def __init__(self, context: AltaDBContext, org_id: str) -> None:
        """Construct AltaDBOrganization."""
        self.context = context

        self._org_id = org_id
        self._name: str

        self._get_org()

    def _get_org(self) -> None:
        org = self.context.dataset.get_org(self._org_id)
        self._name = org["name"]

    @property
    def org_id(self) -> str:
        """Retrieve the unique org_id of this organization."""
        return self._org_id

    @property
    def name(self) -> str:
        """Retrieve unique name of this organization."""
        return self._name

    def __str__(self) -> str:
        """Get string representation of AltaDBOrganization object."""
        return f"AltaDB Organization - {self._name} - ( {self._org_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    def get_datasets(
        self,
    ) -> list:
        """Retrieve all datasets in organization."""
        query = """
            query sdkDataStores($orgId: UUID!) {
                dataStores(orgId: $orgId) {
                    orgId
                    name
                    displayName
                    createdAt
                    createdBy
                    status
                    updatedAt
                    importStatuses
                }
            }
        """
        response: Dict[str, List[Dict]] = self.context.client.execute_query(
            query, {"orgId": self.org_id}
        )
        return response["dataStores"]
