from enum import Enum


class PackViews(Enum):
    """The views a ``ModelPack`` can expose."""

    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DETAIL = "detail"
    DELETE = "delete"

    @property
    def is_object_view(self):
        """Whether the view works on a single object, so its URL needs a pk."""
        return self in (PackViews.UPDATE, PackViews.DETAIL, PackViews.DELETE)
