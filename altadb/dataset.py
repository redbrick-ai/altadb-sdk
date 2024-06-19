"""Interface for interacting with your RedBrick AI Projects."""

from typing import Dict, List

from altadb.common.context import AltaDBContext


class AltaDBDataset:
    """
    Representation of RedBrick project.

    The :attr:`redbrick.project.RBProject` object allows you to programmatically interact with
    your RedBrick project. You can upload data, assign tasks, and query your data with this object. Retrieve the project object in the following way:

    .. code:: python

        >>> project = redbrick.get_project(api_key="", org_id="", project_id="")
    """

    def __init__(self, context: AltaDBContext, org_id: str, project_id: str) -> None:
        """Construct RBProject."""
        self.context = context
        self._org_id = org_id
        self._project_id = project_id

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
        return self._project_id

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
