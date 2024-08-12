from enum import Enum


class PackViews(Enum):
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"
    DETAIL = "detail"
    DELETE = "delete"


def set_enum():
    for enum in PackViews:
        enum.suffix = enum.value
        enum.kwarg = ""
        enum.param = ""

        if enum not in (PackViews.LIST, PackViews.CREATE):
            enum.kwarg = "{id}"
            enum.param = "<int:pk>"

    PackViews.LIST.suffix = ""


set_enum()
