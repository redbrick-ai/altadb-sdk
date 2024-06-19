"""Interface for interacting with your AltaDB Projects."""

from typing import Dict, List

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

    @property
    def members(self) -> List[Dict]:
        """Get list of project members."""
        members = self.context.project.get_members(self.org_id, self.project_id)
        project_members = []
        for member in members:
            member_obj = member.get("member", {})
            user_obj = member_obj.get("user", {})
            project_members.append(
                {
                    "userId": user_obj.get("userId"),
                    "email": user_obj.get("email"),
                    "givenName": user_obj.get("givenName"),
                    "familyName": user_obj.get("familyName"),
                    "role": member_obj.get("role"),
                    "tags": member_obj.get("tags"),
                    "stageAccess": member.get("stageAccess"),
                }
            )
        return project_members

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    @property
    def name(self) -> str:
        """Retrieve unique name of this project."""
        return self._dataset
