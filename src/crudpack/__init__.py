from django.utils.module_loading import autodiscover_modules

from crudpack.base import ModelPack
from crudpack.decorators import register
from crudpack.enums import PackViews
from crudpack.services.packs import PackService, packs

__all__ = ["ModelPack", "PackService", "PackViews", "autodiscover", "packs", "register"]


def autodiscover():
    """Import the ``packs`` module of every installed app."""
    autodiscover_modules("packs")
