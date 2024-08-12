from django.utils.module_loading import autodiscover_modules

from crudpack.base import ModelPack
from crudpack.services.packs import packs

__all__ = ["packs", "ModelPack"]


def autodiscover():
    autodiscover_modules("packs")
